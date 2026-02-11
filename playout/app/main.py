
import os, time, yaml, threading, datetime, json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .scheduler import Scheduler
from .ffmpeg_runner import FfmpegRunner
from .manifest_patcher import ManifestPatcher
from .subtitles import WebVTTSegmenter
from .epg import EPG

CFG_PATH = os.environ.get('CHANNEL_CONFIG','configs/channel.yml')

app = FastAPI()
app.mount("/", StaticFiles(directory="/app/web/static", html=True), name="static")

state = {
    'proc': None,
    'started': None,
}

def build_concat_list(playlist, path):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('ffconcat version 1.0\n')
        for it in playlist:
            if it['type'] == 'vod':
                f.write(f"file '{it['file']}'\n")

@app.on_event('startup')
async def startup():
    with open(CFG_PATH, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    app.state.cfg = cfg
    app.state.scheduler = Scheduler(cfg)
    app.state.ff = FfmpegRunner(cfg)
    # Prepare HLS output folder
    os.makedirs(cfg['output']['hls_dir'], exist_ok=True)

    if cfg['mode'] == 'vod':
        concat_path = os.path.join('/app/out', 'concat.ffconcat')
        build_concat_list(app.state.scheduler.playlist, concat_path)
        state['proc'] = app.state.ff.start_vod(concat_path)
    else:
        state['proc'] = app.state.ff.start_live(cfg['live']['input'])

    state['started'] = time.time()

    # Start manifest patcher
    app.state.patcher = ManifestPatcher(cfg, app.state.scheduler)
    app.state.patcher.start()

    # Segment subtitles for first VOD item if present (POC)
    try:
        first = app.state.scheduler.playlist[0]
        if first.get('vtt'):
            segger = WebVTTSegmenter(first['vtt'], cfg['output']['vtt_dir'], cfg['ihls']['segment_duration'])
            # Use an arbitrary PTS base 900000 (10 seconds) for demo
            segger.segment(program_start_pts90k=900000, out_playlist=os.path.join(cfg['output']['vtt_dir'], 'playlistWebVTT.m3u8'))
    except Exception as e:
        print('VTT segment error', e)

    # Generate a simple EPG for today
    try:
        epg = EPG(out_dir='/app/out/epg', channel_id=cfg['channel_id'])
        day = datetime.date.today()
        programs=[]
        for it in app.state.scheduler.playlist[:10]:
            start = datetime.datetime.utcfromtimestamp(it['start_utc'])
            stop = start + datetime.timedelta(seconds=it['duration'])
            programs.append({'title': it['title'], 'start_iso': start.strftime('%Y-%m-%dT%H:%M:%S.%f+0000'), 'stop_iso': stop.strftime('%Y-%m-%dT%H:%M:%S.%f+0000'), 'duration': it['duration']})
        epg.write_day(day, programs)
    except Exception as e:
        print('EPG error', e)

@app.get('/api/status')
async def status():
    cfg = app.state.cfg
    sch = app.state.scheduler
    hls_dir = cfg['output']['hls_dir']
    master = os.path.join(hls_dir, cfg['output']['master_name'])
    hls = {
        'master': master if os.path.exists(master) else None,
        'segments': len([f for f in os.listdir(hls_dir) if f.endswith('.ts')]) if os.path.exists(hls_dir) else 0,
    }
    return JSONResponse({
        'mode': cfg['mode'],
        'now_playing': sch.now_playing(),
        'upcoming': sch.upcoming(),
        'breaks': {
            'next': sch.next_breaks()
        },
        'hls': hls,
        'since': state['started']
    })

