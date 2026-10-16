"""Functional and throughput tests with explicit hardware/software decoders.

Consumes every frame into appsink and reports checksum, caps, duration and CPU
time.  No decodebin is used, so a missing decoder cannot silently fall back.
"""
import hashlib
import json
import resource
import time
import sys
import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, GstVideo

Gst.init(None)
fixtures = '/home/oem/acceleration-fixtures'
tests = [
    ('h264-1080p60', 'h264-1080p60.h264', 'h264parse', 'v4l2slvideo1h264dec', 'avdec_h264', 180),
    ('hevc-4k60', 'hevc-4k60.h265', 'h265parse', 'v4l2slh265dec', 'avdec_h265', 120),
    ('av1-720p30', 'av1-720p30.ivf', 'ivfparse ! av1parse', 'v4l2slav1dec', 'av1dec', 60),
]


def run(name, filename, parser, decoder, expected):
    if Gst.ElementFactory.find(decoder) is None:
        return dict(test=name, decoder=decoder, status='missing decoder')
    description = (f'filesrc location={fixtures}/{filename} ! {parser} ! {decoder} ! '
                   'videoconvert ! video/x-raw,format=I420 ! '
                   'appsink name=frames sync=false max-buffers=4 drop=false')
    pipeline = Gst.parse_launch(description)
    sink = pipeline.get_by_name('frames')
    frames, caps = 0, ''
    digest = hashlib.sha256()
    cpu = time.process_time()
    start = time.monotonic()
    pipeline.set_state(Gst.State.PLAYING)
    bus = pipeline.get_bus()
    error = None
    try:
        while time.monotonic() - start < 90:
            sample = sink.emit('try-pull-sample', Gst.SECOND)
            if sample:
                caps = sample.get_caps().to_string()
                buffer = sample.get_buffer()
                okay, mapped = buffer.map(Gst.MapFlags.READ)
                if okay:
                    pixels = memoryview(mapped.data)
                    info = GstVideo.VideoInfo.new_from_caps(sample.get_caps())
                    meta = GstVideo.buffer_get_video_meta(buffer)
                    offsets = meta.offset if meta else info.offset
                    strides = meta.stride if meta else info.stride
                    # Hash logical pixels only; HW/SW pools may use different
                    # strides or padding even with identical I420 output caps.
                    for plane in range(3):
                        width = info.width if plane == 0 else (info.width + 1) // 2
                        height = info.height if plane == 0 else (info.height + 1) // 2
                        for row in range(height):
                            begin = offsets[plane] + row * strides[plane]
                            digest.update(pixels[begin:begin + width])
                    pixels.release()
                    buffer.unmap(mapped)
                    frames += 1
            message = bus.pop_filtered(Gst.MessageType.ERROR)
            if message:
                err, debug = message.parse_error()
                error = str(err) + ': ' + str(debug)
                break
            if sink.get_property('eos'):
                break
        else:
            error = '90-second timeout'
    finally:
        pipeline.set_state(Gst.State.NULL)
    elapsed = time.monotonic() - start
    cpu = time.process_time() - cpu
    return dict(test=name, decoder=decoder, frames=frames, expected=expected,
                seconds=round(elapsed, 4), fps=round(frames / elapsed, 2),
                cpu_seconds=round(cpu, 4), caps=caps, sha256=digest.hexdigest(),
                status='pass' if frames == expected and not error else 'fail', error=error)


for name, filename, parser, hardware, software, count in tests:
    if len(sys.argv) > 1 and not name.startswith(sys.argv[1]):
        continue
    for decoder in (hardware, software):
        print(json.dumps(run(name, filename, parser, decoder, count)), flush=True)
