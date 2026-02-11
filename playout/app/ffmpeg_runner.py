
import os, subprocess, shlex
from typing import Dict, Any, List

class FfmpegRunner:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg

    def start_vod(self, concat_list_path: str):
        return self._run_ffmpeg(input_args=f"-f concat -safe 0 -i {shlex.quote(concat_list_path)}")

    def start_live(self, input_url: str):
        return self._run_ffmpeg(input_args=f"-re -i {shlex.quote(input_url)}")

    def _run_ffmpeg(self, input_args: str):
        hls_dir = self.cfg['output']['hls_dir']
        os.makedirs(hls_dir, exist_ok=True)
        seg = int(self.cfg['ihls']['segment_duration'])
        variants = self.cfg['ihls']['variants']
        # Build filter graph + maps for ladder
        vf_parts = []
        maps = []
        var_stream_map = []
        for idx, v in enumerate(variants):
            vf_parts.append(f"[0:v]scale=w={v['width']}:h={v['height']}:force_original_aspect_ratio=decrease:eval=frame:flags=bicubic,format=yuv420p[v{idx}]")
            maps.append(f"-map [v{idx}] -map a:0")
            var_stream_map.append(f"v:{idx},a:{idx}")
        vf = ";".join(vf_parts)
        maps_str = " ".join(maps)
        v_bitrates = " ".join([f"-b:v:{i} {v['v_bitrate']} -maxrate:v:{i} {v['v_bitrate']} -bufsize:v:{i} {int(int(v['v_bitrate'][:-1])*2)}k -g {seg*2} -keyint_min {seg*2} -sc_threshold 0" for i, v in enumerate(variants)])
        a_bitrates = " ".join([f"-c:a:{i} aac -b:a:{i} {v['a_bitrate']}" for i, v in enumerate(variants)])
        cmd = f"ffmpeg -hide_banner -nostdin -y {input_args} -filter_complex {shlex.quote(vf)} {maps_str} -c:v h264 {v_bitrates} {a_bitrates} " \
              f"-f hls -hls_time {seg} -hls_playlist_type event -hls_flags independent_segments+program_date_time " \
              f"-master_pl_name {self.cfg['output']['master_name']} -strftime_mkdir 1 -var_stream_map '{','.join(var_stream_map)}' " \
              f"-hls_segment_filename {shlex.quote(os.path.join(hls_dir, self.cfg['output']['playlist_basename']) )}_%v_%05d.ts " \
              f"{shlex.quote(os.path.join(hls_dir, self.cfg['output']['playlist_basename']))}_%v.m3u8"
        print("Launching FFmpeg:\n", cmd, flush=True)
        return subprocess.Popen(cmd, shell=True)
