
import time, math, yaml
from typing import List, Dict, Any
from .models import VodItem, BreakEvent
from .scte35_tools import make_splice_insert_b64

class Scheduler:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.refresh()

    def refresh(self):
        # Build a rolling 24h playlist from VOD items
        self.mode = self.cfg['mode']
        self.segment = int(self.cfg['ihls']['segment_duration'])
        if self.mode == 'vod':
            items = [VodItem(**it) for it in self.cfg['vod']['playlist']]
            # Repeat list to cover at least 24h
            seconds_needed = 24*3600
            pl = []
            t = time.time()
            while seconds_needed > 0:
                for it in items:
                    pl.append({
                        'type': 'vod',
                        'file': it.file,
                        'title': it.title,
                        'start_utc': t,
                        'duration': it.duration,
                        'vtt': it.vtt,
                    })
                    t += it.duration
                    seconds_needed -= it.duration
                    if seconds_needed <= 0:
                        break
            self.playlist = pl
        else:
            # live relay – single item placeholder
            self.playlist = [{
                'type': 'live', 'title': 'Live Relay', 'file': self.cfg['live']['input'],
                'start_utc': time.time(), 'duration': 24*3600, 'vtt': None
            }]
        # Compute ad breaks per hour
        self.breaks = self._compute_breaks()

    def _compute_breaks(self) -> List[BreakEvent]:
        mph = int(self.cfg['ads'].get('minutes_per_hour', 8))
        min_pod = int(self.cfg['ads'].get('min_pod', 60))
        max_pod = int(self.cfg['ads'].get('max_pod', 120))
        total = mph * 60
        # Simple split into 3 pods/hour as a baseline, bounded by min/max
        pod_count = max(2, min(4, math.ceil(total / ((min_pod+max_pod)//2))))
        base = total // pod_count
        pods = [max(min_pod, min(max_pod, base)) for _ in range(pod_count)]
        # Schedule pods at roughly even spacing each hour on wall clock boundaries
        now = time.time()
        # Align to top of current hour
        hour_start = now - (now % 3600)
        events = []
        for h in range(24):
            hs = hour_start + h*3600
            slot = 3600 / pod_count
            for i, dur in enumerate(pods):
                start = hs + int(i*slot + slot*0.5)  # middle of each slot
                scte35_b64 = make_splice_insert_b64(duration=dur)
                events.append(BreakEvent(start_utc=start, duration=dur, scte35_b64=scte35_b64))
        return events

    def now_playing(self, t=None):
        if t is None:
            t = time.time()
        for it in self.playlist:
            if it['start_utc'] <= t < it['start_utc'] + it['duration']:
                return it
        return self.playlist[-1]

    def upcoming(self, horizon_sec=1800):
        t = time.time()
        return [it for it in self.playlist if t <= it['start_utc'] < t + horizon_sec]

    def next_breaks(self, horizon_sec=900):
        t = time.time()
        return [b.__dict__ for b in self.breaks if t <= b.start_utc < t + horizon_sec]
