import json
import os
from pathlib import Path
import re
import time
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstAllocators', '1.0')
from gi.repository import Gst, GstAllocators
Gst.init(None)
fixtures = os.environ.get('ORANGEPI_FIXTURE_DIR', '/home/oem/acceleration-fixtures')
# Device numbers vary across boots. Identify rkvdec by its device node.
h264_candidates = []
for factory in Gst.Registry.get().get_feature_list(Gst.ElementFactory):
    name = factory.get_name()
    if factory.get_plugin_name() != 'v4l2codecs' or not re.fullmatch(r'v4l2sl(?:video\d+)?h264dec', name):
        continue
    element = factory.create(None)
    device = element.get_property('video-device')
    try:
        driver = (Path('/sys/class/video4linux') / Path(device).name / 'name').read_text().strip()
    except OSError:
        driver = ''
    h264_candidates.append((0 if driver == 'rkvdec' else 1, name))
h264 = min(h264_candidates)[1] if h264_candidates else 'v4l2slh264dec'

tests = [
    ('h264-1080p60', 'h264-1080p60.h264', 'h264parse', h264, 'avdec_h264', 180),
    ('hevc-4k60', 'hevc-4k60.h265', 'h265parse', 'v4l2slh265dec', 'avdec_h265', 120),
    ('av1-720p30', 'av1-720p30.ivf', 'ivfparse ! av1parse', 'v4l2slav1dec', 'av1dec', 60),
]

for name, filename, parser, hardware, software, expected in tests:
    for decoder in (hardware, software):
        if not Gst.ElementFactory.find(decoder):
            print(json.dumps(dict(test=name, decoder=decoder, status='missing')), flush=True)
            continue
        is_hardware = decoder == hardware
        memory_filter = ''
        pipe = Gst.parse_launch(f'filesrc location="{fixtures}/{filename}" ! '
                                f'{parser} ! {decoder}{memory_filter} ! '
                                'fakesink name=output sync=false signal-handoffs=true')
        count, caps, memory_type = [0], [''], ['']
        def handoff(sink, buffer, pad):
            count[0] += 1
            if not caps[0]:
                caps[0] = pad.get_current_caps().to_string()
                if buffer.n_memory():
                    memory_type[0] = 'dmabuf' if GstAllocators.is_dmabuf_memory(buffer.peek_memory(0)) else 'system-or-v4l2'
        pipe.get_by_name('output').connect('handoff', handoff)
        start, cpu = time.monotonic(), time.process_time()
        pipe.set_state(Gst.State.PLAYING)
        message = pipe.get_bus().timed_pop_filtered(45 * Gst.SECOND, Gst.MessageType.EOS | Gst.MessageType.ERROR)
        error = None
        if not message:
            error = 'timeout'
        elif message.type == Gst.MessageType.ERROR:
            parsed, debug = message.parse_error()
            error = f'{parsed}: {debug}'
        pipe.set_state(Gst.State.NULL)
        elapsed = time.monotonic() - start
        print(json.dumps(dict(test=name, decoder=decoder, frames=count[0], expected=expected,
            seconds=round(elapsed, 4), fps=round(count[0] / elapsed, 2),
            cpu_seconds=round(time.process_time() - cpu, 4), caps=caps[0], memory_type=memory_type[0],
            hardware=is_hardware, status='pass' if count[0] == expected and not error else 'fail', error=error)), flush=True)
