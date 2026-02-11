
import os, time, threading, glob, datetime
from .scte35_tools import daterange_tags

class ManifestPatcher:
    '''Watches variant playlists and injects CUE/DATERANGE tags when a break window begins.
    Simplified POC: we insert tags at the top of the next segment once NOW >= break.start_utc.'''
    def __init__(self, cfg, scheduler):
        self.cfg = cfg
        self.scheduler = scheduler
        self.hls_dir = cfg['output']['hls_dir']
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self.running = False

    def _loop(self):
        fired = set()
        while self.running:
            now = time.time()
            for ev in self.scheduler.breaks:
                key = (ev.start_utc, ev.duration)
                if key in fired:
                    continue
                if now >= ev.start_utc:
                    self._mark_all_variants(ev)
                    fired.add(key)
            time.sleep(1)

    def _mark_all_variants(self, ev):
        start_iso = datetime.datetime.utcfromtimestamp(ev.start_utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        tagblock = daterange_tags(event_id=f"splice-{int(ev.start_utc)}", start_iso=start_iso, duration=ev.duration, scte35_b64=ev.scte35_b64)
        for m3u in glob.glob(os.path.join(self.hls_dir, f"{self.cfg['output']['playlist_basename']}_*.m3u8")):
            try:
                with open(m3u, 'r+', encoding='utf-8') as f:
                    txt = f.read()
                    # Insert tag before last segment (approximate alignment)
                    ix = txt.rfind('#EXTINF')
                    if ix != -1:
                        new = txt[:ix] + tagblock + txt[ix:]
                        f.seek(0)
                        f.write(new)
                        f.truncate()
            except Exception as e:
                print("Manifest patch error", m3u, e)
