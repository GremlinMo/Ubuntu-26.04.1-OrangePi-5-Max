#!/bin/bash
set -euo pipefail
out=/home/oem/acceleration-fixtures
mkdir -p "$out"
ffmpeg -hide_banner -loglevel error -y -f lavfi -i testsrc2=size=1920x1080:rate=60 \
    -frames:v 180 -c:v libx264 -preset ultrafast -tune zerolatency \
    -pix_fmt yuv420p -profile:v main -f h264 "$out/h264-1080p60.h264"
ffmpeg -hide_banner -loglevel error -y -f lavfi -i testsrc2=size=3840x2160:rate=60 \
    -frames:v 120 -c:v libx265 -preset ultrafast \
    -x265-params pools=4:frame-threads=2:bframes=0:log-level=error \
    -pix_fmt yuv420p -f hevc "$out/hevc-4k60.h265"
ffmpeg -hide_banner -loglevel error -y -f lavfi -i testsrc2=size=1280x720:rate=30 \
    -frames:v 60 -c:v libsvtav1 -preset 12 -crf 40 -threads 4 \
    -svtav1-params lp=4 -pix_fmt yuv420p -f ivf "$out/av1-720p30.ivf"
ls -lh "$out"
