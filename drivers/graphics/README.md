# GPU rendering

The tested Ubuntu stack uses the Panthor kernel driver and Mesa 26.0.8
Panfrost/PanVK for the Mali-G610 MC4. Hardware OpenGL ES 3.1 rendering is
verified, with 181.54 FPS in the latest 1920x1080 offscreen shader fixture.
PanVK enumeration is not a Vulkan benchmark or an all-game compatibility claim.

Source test: `../../scripts/gpu-offscreen-bench.c`.
Evidence: `../../docs/acceleration-proof-20261017/live-acceleration.json`.
Ubuntu packages are not repackaged here; preserve matching package source and
licence requirements when publishing a binary image.
