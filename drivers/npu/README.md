# NPU integration

See `../../npu-package/README.md` for the isolated runtime, application and builder.
`runtime-1.0.0/installed-qualification.json` records the installed-package test:
12 successful Rocket submit ioctls, two delegated partitions, matching top class
and maximum one quantization-step CPU/NPU difference.

The latest short comparison is in the front-page evidence. The earlier full
20-run qualification and later 10-run comparison are separate tests; differences
in timings are expected. Only MobileNet V1 UINT8 is qualified, with some CPU
operations possible. Other precisions, all-core scaling and 6 TOPS are not claimed.

The application source is public. The complete binary package's third-party
dependency/source inventory is part of the pending binary-release review.
