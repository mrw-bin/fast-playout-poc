
import os, re, math, datetime
from typing import List, Tuple

TIMECODE = re.compile(r"(\d\d):(\d\d):(\d\d)\.(\d\d\d)")

def parse_time(tc: str) -> float:
    h,m,s,ms = map(int, TIMECODE.match(tc).groups())
    return h*3600 + m*60 + s + ms/1000.0

def format_ts(sec: float) -> str:
    h = int(sec // 3600); sec -= h*3600
    m = int(sec // 60); sec -= m*60
    s = int(sec); ms = int(round((sec - s)*1000))
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

class WebVTTSegmenter:
    def __init__(self, vtt_path: str, out_dir: str, seg_dur: int):
        self.vtt_path = vtt_path
        self.out_dir = out_dir
        self.seg_dur = seg_dur

    def segment(self, program_start_pts90k: int, out_playlist: str):
        with open(self.vtt_path, 'r', encoding='utf-8') as f:
            lines = [ln.rstrip('\n') for ln in f]
        # crude cue parser
        cues = []
        i=0
        while i < len(lines):
            if '-->' in lines[i]:
                a,b = [s.strip() for s in lines[i].split('-->')]
                text=[]; j=i+1
                while j < len(lines) and lines[j]:
                    text.append(lines[j]); j+=1
                cues.append((parse_time(a), parse_time(b), text))
                i=j
            else:
                i+=1
        duration = max((c[1] for c in cues), default=0)
        seg_count = max(1, math.ceil(duration/self.seg_dur))
        os.makedirs(self.out_dir, exist_ok=True)
        # Write segments
        for n in range(seg_count):
            seg_start = n*self.seg_dur
            seg_end = seg_start + self.seg_dur
            fn = os.path.join(self.out_dir, f"sub_{n:05d}.vtt")
            with open(fn, 'w', encoding='utf-8') as o:
                o.write("WEBVTT\n")
                # Map local 0 to program PTS
                pts = program_start_pts90k + int(seg_start*90000)
                o.write(f"X-TIMESTAMP-MAP=LOCAL:00:00:00.000,MPEGTS:{pts}\n\n")
                for (cs,ce,txt) in cues:
                    if ce <= seg_start or cs >= seg_end:
                        continue
                    s=max(cs,seg_start)-seg_start; e=min(ce,seg_end)-seg_start
                    o.write(f"{format_ts(s)} --> {format_ts(e)}\n")
                    for t in txt:
                        o.write(t+"\n")
                    o.write("\n")
        # Write playlist
        with open(out_playlist, 'w', encoding='utf-8') as m:
            m.write("#EXTM3U\n#EXT-X-VERSION:3\n")
            m.write(f"#EXT-X-TARGETDURATION:{self.seg_dur}\n")
            m.write("#EXT-X-MEDIA-SEQUENCE:0\n")
            for n in range(seg_count):
                m.write(f"#EXTINF:{self.seg_dur:.3f},\nsub_{n:05d}.vtt\n")
