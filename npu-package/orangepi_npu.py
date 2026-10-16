#!/usr/bin/env python3
"""Pinned Rocket/Teflon image classifier; NPU mode never retries on the CPU."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parent
MODEL = ROOT / 'assets/mobilenet_v1_1.0_224_quant.tflite'
DELEGATE = ROOT / 'lib/libteflon.so'
NOTE = ('MobileNet V1 UINT8 only. Delegated graph partitions may retain CPU work. '
        'Not RKNN, arbitrary-model support, all precisions, all-core scaling or a 6-TOPS claim.')


def digest(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_files():
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    for name, expected in manifest['files'].items():
        path = ROOT / name
        if not path.resolve().is_relative_to(ROOT) or digest(path) != expected:
            raise RuntimeError('Package integrity check failed: ' + name)
    return manifest


def device_check():
    if platform.machine() != 'aarch64':
        raise RuntimeError('This package requires ARM64 Linux.')
    if not Path('/sys/bus/platform/drivers/rocket/fdab0000.npu').exists():
        raise RuntimeError('Rocket NPU driver is not bound. Use the tested mainline boot entry, not vendor RKNN.')
    if not os.access('/dev/accel/accel0', os.R_OK | os.W_OK):
        raise RuntimeError('NPU unavailable or permission denied. Use a local desktop login or ask the administrator '
                           'for render-group access, then log out/in. Do not run image inference as root.')


def temperatures():
    values = {}
    for zone in Path('/sys/class/thermal').glob('thermal_zone*'):
        try:
            values[(zone / 'type').read_text().strip()] = int((zone / 'temp').read_text()) / 1000
        except (OSError, ValueError):
            pass
    if not values or max(values.values()) >= 75:
        raise RuntimeError('Temperature unavailable or at/above the conservative 75 C test limit.')
    return values


def compare_outputs(cpu, npu):
    if not cpu or len(cpu) != len(npu):
        raise RuntimeError('CPU/NPU output lengths differ or are empty.')
    delta = max(abs(int(a) - int(b)) for a, b in zip(cpu, npu))
    same_top = max(range(len(cpu)), key=cpu.__getitem__) == max(range(len(npu)), key=npu.__getitem__)
    return {'top1_matches': same_top, 'max_difference_lsb': delta,
            'threshold_lsb': 2, 'passed': same_top and delta <= 2}


def infer(image_path, mode, runs):
    # Isolated interpreter ignores PYTHONPATH and user site-packages.
    sys.path.insert(0, str(ROOT / 'site-packages'))
    import numpy as np
    from PIL import Image, ImageOps
    from tflite_runtime.interpreter import Interpreter, OpResolverType, load_delegate

    before = temperatures()
    delegates = []
    if mode == 'npu':
        device_check()
        delegates = [load_delegate(str(DELEGATE))]
    with Image.open(image_path) as source:
        source = ImageOps.exif_transpose(source).convert('RGB')
        if source.size != (224, 224):
            source = ImageOps.fit(source, (224, 224), method=Image.Resampling.BILINEAR)
        pixels = np.asarray(source, dtype=np.uint8)[None, ...]
    started = time.perf_counter()
    interpreter = Interpreter(model_path=str(MODEL), experimental_delegates=delegates,
        num_threads=1, experimental_op_resolver_type=OpResolverType.BUILTIN_WITHOUT_DEFAULT_DELEGATES)
    interpreter.allocate_tensors()
    init_ms = (time.perf_counter() - started) * 1000
    inputs, outputs = interpreter.get_input_details(), interpreter.get_output_details()
    if (len(inputs) != 1 or len(outputs) != 1 or inputs[0]['shape'].tolist() != [1, 224, 224, 3]
            or inputs[0]['dtype'] != np.uint8 or outputs[0]['shape'].tolist() != [1, 1001]
            or outputs[0]['dtype'] != np.uint8):
        raise RuntimeError('Unexpected bundled model schema.')
    partitions = sum(op['op_name'] == 'DELEGATE' for op in interpreter._get_ops_details())
    if mode == 'npu' and partitions == 0:
        raise RuntimeError('No NPU partitions delegated. Refusing silent CPU fallback.')
    interpreter.set_tensor(inputs[0]['index'], pixels)
    latencies, reference, peak = [], None, dict(before)
    for i in range(3 + runs):
        for key, value in temperatures().items():
            peak[key] = max(peak.get(key, value), value)
        started = time.perf_counter()
        interpreter.invoke()
        result = interpreter.get_tensor(outputs[0]['index']).reshape(-1)
        elapsed = (time.perf_counter() - started) * 1000
        if reference is None:
            reference = result.copy()
        elif not np.array_equal(reference, result):
            raise RuntimeError('Repeated inference outputs differ.')
        if i >= 3:
            latencies.append(elapsed)
    labels = (ROOT / 'assets/imagenet_labels.txt').read_text().splitlines()
    if len(labels) != 1001 or labels[0] != 'background':
        raise RuntimeError('Unexpected label index mapping.')
    order = np.argsort(-reference.astype(np.int64), kind='stable')[:5]
    scale, zero = outputs[0]['quantization']
    report = {'mode': mode, 'delegate_partitions': partitions,
        'median_ms': statistics.median(latencies), 'initialization_ms': init_ms,
        'warmups': 3, 'runs': runs, 'cpu_threads': 1, 'cpu_affinity': sorted(os.sched_getaffinity(0)),
        'top5': [{'index': int(i), 'label': labels[i], 'score': float((int(reference[i])-zero)*scale)} for i in order],
        'peak_sampled_temperatures_c': peak, 'output_sha256': hashlib.sha256(reference.tobytes()).hexdigest(),
        'no_full_cpu_fallback': mode == 'npu', 'qualification': NOTE}
    vector = reference.tolist()
    del interpreter
    delegates.clear()
    return report, vector


def format_report(report):
    if report.get('action') == 'doctor':
        return ('Orange Pi NPU runtime ' + report['version'] + '\n'
                'Package checksums: OK\nRocket NPU access: OK\nKernel: ' + report['kernel'] +
                '\nNo inference was run by this health check.\n' + NOTE)
    if report.get('action') == 'verify':
        return ('Orange Pi NPU verification: ' + ('PASS' if report['comparison']['passed'] else 'FAIL') +
            '\nCPU median: %.2f ms\nNPU median: %.2f ms\nSpecific-test speedup: %.2fx\n' %
            (report['cpu']['median_ms'], report['npu']['median_ms'], report['speedup']) +
            'NPU graph partitions: %s\nMaximum CPU/NPU difference: %s quantization steps\n' %
            (report['npu']['delegate_partitions'], report['comparison']['max_difference_lsb']) +
            'Top result: ' + report['npu']['top5'][0]['label'] + '\n' + NOTE +
            '\nTiming excludes model loading/compilation and image preparation; not an optimized CPU comparison.')
    return ('Orange Pi ' + report['mode'].upper() + ' image classification\nMedian: %.2f ms\n' % report['median_ms'] +
            '\n'.join('%s: %.3f' % (item['label'], item['score']) for item in report['top5']) + '\n\n' + NOTE)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('doctor', 'demo', 'classify', 'verify'))
    parser.add_argument('image', nargs='?', help='Local image for classify; never uploaded')
    parser.add_argument('--runs', type=int, default=10)
    parser.add_argument('--mode', choices=('npu', 'cpu'), default='npu')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    if not 1 <= args.runs <= 30:
        parser.error('--runs must be 1..30')
    if (args.action == 'classify') != bool(args.image):
        parser.error('Only classify requires an image path.')
    if args.action == 'verify' and args.mode != 'npu':
        parser.error('verify always compares CPU and NPU.')
    if os.geteuid() == 0:
        raise RuntimeError('Run as an ordinary user, without sudo.')
    manifest = verify_files()
    if args.action == 'doctor':
        device_check()
        report = {'action': 'doctor', 'version': manifest['version'], 'kernel': platform.release(),
                  'integrity_ok': True, 'npu_access': True, 'inference_executed': False}
    elif args.action == 'verify':
        device_check()
        cpu, cpu_values = infer(ROOT / 'assets/dog_224x224.jpg', 'cpu', args.runs)
        npu, npu_values = infer(ROOT / 'assets/dog_224x224.jpg', 'npu', args.runs)
        report = {'action': 'verify', 'cpu': cpu, 'npu': npu,
                  'comparison': compare_outputs(cpu_values, npu_values), 'speedup': cpu['median_ms']/npu['median_ms']}
    else:
        source = Path(args.image).expanduser() if args.image else ROOT / 'assets/dog_224x224.jpg'
        report, _ = infer(source, args.mode, args.runs)
    print(json.dumps(report) if args.json else format_report(report), flush=True)
    return 1 if args.action == 'verify' and not report['comparison']['passed'] else 0


if __name__ == '__main__':
    def expired(*_):
        raise RuntimeError('Inference timed out after 120 seconds.')
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(120)
    try:
        sys.exit(main())
    except Exception as error:
        print('NPU error: ' + str(error), file=sys.stderr)
        sys.exit(1)
