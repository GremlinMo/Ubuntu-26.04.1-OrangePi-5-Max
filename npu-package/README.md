# Orange Pi NPU runtime

An isolated, removable ARM64 package for the Orange Pi 5 Max Ubuntu mainline
Rocket driver. It packages the already-qualified Mesa Teflon 26.0.8 delegate,
CPython 3.11.17, TFLite Runtime 2.14.0, NumPy 1.26.4 and Pillow 11.3.0. It does
not replace system Python, Mesa graphics libraries, the kernel, firmware or
boot files. No service, network listener or background inference is installed.

## Everyday use

Open **Orange Pi NPU** from Ubuntu's app menu, or run as an ordinary user:

```
orangepi-npu doctor
orangepi-npu demo
orangepi-npu classify '/path/to/photo.jpg'
orangepi-npu verify --runs 20
orangepi-npu verify --runs 20 --json
```

Photos stay local. Classification uses the bundled MobileNet V1 UINT8 ImageNet
model (1001 labels including background), EXIF orientation, RGB conversion and
center-crop/resizing to 224x224. Scores are model outputs, not calibrated
confidence guarantees. This is object classification, not a chatbot, face
recognizer or arbitrary-model runner. Use only trusted image files.

NPU mode checks Rocket access and requires delegated graph partitions. It never
retries a failed NPU invocation in CPU-only mode. Some graph operations can still
run on the CPU. `--mode cpu` explicitly requests a CPU reference for demo/classify.
`verify` checks a bundled sample against that reference, with matching top class
and at most 2 output quantization steps difference. This is not dataset accuracy
certification. Timing excludes startup/compilation and image loading. Both use
one interpreter thread, not an optimized multi-thread CPU benchmark.

Inference is bounded to 1..30 measured runs with three warmups, a 120-second
timeout and conservative 75 C sampled temperature stop. This does not replace
the kernel's thermal protection. Doctor verifies file integrity and NPU access,
but does not run inference. New kernels/runtimes need requalification; they are
not claimed compatible merely because doctor passes. INT4/INT16/FP16, all cores,
6 TOPS and vendor RKNN models are not established by this package.

## Install, access and removal

Install the supplied `.deb` with Ubuntu's package tools. Dependencies must already
be available or resolved normally; do not mix unrelated distributions' packages.
Files live in `/opt/orangepi-npu`, commands in `/usr/bin`, and a desktop entry in
`/usr/share/applications`. Files are root-owned, ordinary users cannot modify the
runtime. There are no maintainer scripts or automatic permission changes.

Use an existing local desktop login with NPU access. For SSH/service users, an
administrator can grant the existing `render` group after considering that this
also grants access to other rendering devices. Log out/in afterward. Never use
`chmod 777` or run untrusted image inference with sudo.

Remove with `sudo apt remove orangepi-npu-runtime`. This leaves the original
validation folder, system drivers and graphics packages intact. No reboot is
required. The private runtime is deliberately versioned, but still needs security
maintenance; system Python updates do not update its bundled dependencies.

## Rebuild and provenance

`build-package.py SOURCE_ASSETS OUTPUT_DIRECTORY` runs on ARM64 Linux, without
root. SOURCE_ASSETS is the original validated download directory. It verifies
all binary inputs against pinned SHA256 values, extracts them to a new temporary
staging directory and builds a package using dpkg-deb. It never copies user
credentials, Wi-Fi profiles, pairing data or test output into the package.

Model: TensorFlow MobileNet V1 2018-08-02, linked by
https://docs.mesa3d.org/teflon.html and downloaded from
https://download.tensorflow.org/models/mobilenet_v1_2018_08_02/mobilenet_v1_1.0_224_quant.tgz

Labels and Apache-2.0 notice: google-coral/test_data commit
104342d2d3480b3e66203073dac24f4e2dbb4c41, `imagenet_labels.txt`.
Sample dog image and redistribution notice: rockchip-linux/rknpu2 commit
5adf7c1bd17e169e9880ccdf3b49adde925ab7f9,
`examples/rknn_mobilenet_demo/model/dog_224x224.jpg`.
Mesa: official Ubuntu mesa-teflon-delegate 26.0.8-1ubuntu0.3 ARM64 package,
with its copyright notice. Python: python-build-standalone release 20261013,
CPython 3.11.17, with bundled notices. Wheels: official PyPI files with their
dist-info license notices. All original notices remain in the package.

The app and packaging source here are provided under the MIT license in LICENSE.
Review third-party notices and release maintenance before public distribution.
