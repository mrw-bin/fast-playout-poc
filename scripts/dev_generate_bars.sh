
#!/usr/bin/env bash
set -euo pipefail
mkdir -p media

# 20 minutes of 1080p color bars with tone (useful for quick testing)
ffmpeg -hide_banner -y \
  -f lavfi -i "smptebars=size=1920x1080:rate=25" \
  -f lavfi -i "sine=frequency=1000:sample_rate=48000" \
  -t 600 \
  -c:v libx264 -pix_fmt yuv420p -preset veryfast -crf 22 -g 50 -x264-params keyint=50:min-keyint=50:scenecut=0 \
  -c:a aac -b:a 192k \
  media/sample_01.mp4

# Short slate clip used during unfilled ads
ffmpeg -hide_banner -y \
  -f lavfi -i "color=c=black:s=1920x1080:r=25" \
  -f lavfi -i "anullsrc=r=48000:cl=stereo" \
  -t 30 \
  -c:v libx264 -pix_fmt yuv420p -preset veryfast -crf 23 -g 50 -x264-params keyint=50:min-keyint=50:scenecut=0 \
  -c:a aac -b:a 128k \
  media/slate.mp4

cat > media/sample_01.vtt <<VTT
WEBVTT

00:00:01.000 --> 00:00:04.000
Sample caption one

00:00:05.000 --> 00:00:08.000
Sample caption two
VTT

