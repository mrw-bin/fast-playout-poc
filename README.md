
# FAST Playout Engine (POC) — Samsung TV Plus–ready

A fully Dockerized Python-based reference implementation that can:

- Run a **24/7 playout** from VOD assets or **relay an existing live stream**
- Maintain a **dynamic playlist** with just-in-time media injection
- Provide a **daily 24‑hour scheduler** (EPG + programming grid)
- Insert **SCTE‑35** ad markers and tags (both **manifest markers** and optional **binary splice_info() in TS**)
- Encode an **ABR HLS ladder** with FFmpeg (5–6s segments) and emit **Samsung TV Plus SSAI‑ready** output
- Serve **segmented WebVTT subtitles** synced to the video timeline
- Expose a small **dashboard** with live stream stats (position, breaks, playlist, schedule)

> **Why this POC?** To satisfy Samsung TV Plus onboarding expectations for origin HLS, ad markers, captions, XMLTV EPG and operational controls. See `docs/` for the provided Samsung PDFs and the notes below.

---

## Architecture

```
                +-------------------+
  VOD .mp4 ---> | Scheduler &       |     +---------------------------+
  Live HLS ---> | Playout Orchestr. |---->|  FFmpeg HLS Encoder        |---> /out/hls (master + variants)
                |  (FastAPI)        |     |  (ABR ladder, 5-6s segs)  |
                +----+--------------+     +---------------------------+
                     |                       ^
                     | (break events)        | (optional TS patch)
                     v                       |
           +-------------------+             |
           | Manifest Patcher  |----(CUE/DATERANGE w/ SCTE35)---->
           +-------------------+             |
                     |                       |
                     v                       |
           +-------------------+             |
           |  TSDuck Injector  |----(splice_info() in TS)--------+
           +-------------------+
                     |
                     v
           +-------------------+
           |  WebVTT Segmenter |
           +-------------------+

           +-------------------+
           | Dashboard (HTML)  |
           +-------------------+
```

- **Modes**: `vod` (concat demuxer) or `live` (relay input URL) — switchable via config.
- **ABR**: default 4 variants (360p/540p/720p/1080p). Segment length: **6s**. `#EXT-X-PROGRAM-DATE-TIME` included.
- **Ad Markers**: `#EXT-X-CUE-OUT/IN` and `#EXT-X-DATERANGE` with base64 **SCTE35** payloads. Optionally, inject **binary SCTE‑35** into TS segments via **TSDuck**.
- **Subtitles**: Generate **segmented WebVTT** playlist aligned to HLS sequence numbers and timestamps (with `X-TIMESTAMP-MAP`).
- **EPG**: Emits XMLTV day file with required fields; extend to 4–10 days as needed.

> **Samsung TV Plus requirements reflected here**: HLS RFC 8216 compliance, 5–6s segments, variant manifests synced with VTT and `PROGRAM-DATE-TIME`, frame‑accurate ad markers with `EXT-X-CUE-OUT/IN` (and support for SCTE‑35), WebVTT captions, origin delivery expectations, etc. See citations in the GitHub README references section (mirrors in this chat answer).

---

## Quick start

### 1) Prerequisites
- Docker & Docker Compose
- Place VOD assets (`.mp4`) and optional subtitles (`.vtt`) under `media/`.

(Optional) Generate test bars & audio:

```bash
./scripts/dev_generate_bars.sh
```

### 2) Configure the channel
Edit `configs/channel.yml` — key options:
- `mode: vod | live`
- `vod.playlist`: list of assets with start times, durations and optional `vtt` paths
- `live.input`: input HLS/RTMP/RTP/SRT URL
- `ads.minutes_per_hour`: e.g., 8
- `ads.min_pod`: e.g., 60 (seconds)
- `hls.segment_duration`: e.g., 6 (seconds)

### 3) Run

```bash
docker compose up --build
```

HLS output: `./out/hls/index.m3u8`

Dashboard: http://localhost:8080/

---

## Project layout

```
fast-playout-poc/
├─ docker-compose.yml
├─ playout/
│  ├─ Dockerfile
│  ├─ requirements.txt
│  └─ app/
│     ├─ main.py                # FastAPI app + orchestrator
│     ├─ scheduler.py           # 24h grid + dynamic injection
│     ├─ ffmpeg_runner.py       # ABR HLS command builder
│     ├─ manifest_patcher.py    # Insert CUE/DATERANGE markers
│     ├─ scte35_tools.py        # threefive helpers (encode SCTE-35)
│     ├─ subtitles.py           # Segmented WebVTT generator
│     ├─ epg.py                 # XMLTV output
│     └─ models.py              # Pydantic models
├─ configs/
│  └─ channel.yml               # Channel configuration
├─ media/                       # Place your VODs and .vtt files here
│  └─ .gitkeep
├─ out/
│  ├─ hls/                      # HLS (master + variants + segments)
│  └─ vtt/                      # Segmented WebVTT
├─ scripts/
│  └─ dev_generate_bars.sh      # Generate test bars/slate
├─ web/
│  └─ static/
│     └─ dashboard.html         # Simple HTML dashboard
├─ docs/                        # (optional) Samsung PDFs (not committed here)
├─ README.md
└─ LICENSE (MIT)
```

---

## Notes on Samsung TV Plus alignment
- **HLS**: 5–6s segment target; RFC 8216 compliant, master manifest with correct `BANDWIDTH`, `CODECS`, `RESOLUTION`, variant manifests synced and carrying `EXT-X-PROGRAM-DATE-TIME`; variants & VTT sequence numbers kept in sync. (See Samsung spec doc.)
- **Ad markers**: `EXT-X-CUE-OUT/IN` required; `EXT-X-DATERANGE` + `EXT-OATCLS-SCTE35` supported for enhanced signaling; frame-accurate markers expected. (See Samsung spec doc.)
- **Subtitles**: WebVTT supported/preferred; `EXT-X-MEDIA` line in master manifest to reference VTT playlist; include `X-TIMESTAMP-MAP` mapping to MPEGTS timebase. (See Samsung spec doc.)
- **EPG**: Daily XMLTV with specific required fields; 4+ days recommended.
- **Origin delivery**: Either partner origin pulled by Samsung CDN or push to Samsung proxy origin (S3); sessionless HLS.

> See the Samsung PDFs you provided in `docs/` for the exact examples and field lists.

---

## Limitations (POC)
- Binary SCTE‑35 injection into TS via TSDuck is implemented as a **file post-processor** for recent segments; production should use an inline `tsp` pipeline (or a packager with native SCTE‑35 insertion).
- FFmpeg ABR ladder is a common baseline; tune ladder/bitrates to your content.
- Live relay ad breaks are **manifest-markers only** by default (no content splice).

---

## License
MIT
