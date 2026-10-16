# Browser decoding audit — 17 October 2026

Status: preliminary checks only; on-screen Firefox/YouTube decoding NOT yet
measured. The user requested verification, not installation of a new browser or
driver. No browser preferences, sandbox controls, packages or boot files changed.

## Observed live state

- Firefox is the installed browser: Snap 154.0-1, revision 8762. Its Ubuntu deb
  is the 1:1snap1-0ubuntu8 launcher. Chromium was not found.
- No Firefox process was running. There was no OEM Wayland socket and no logged-in
  OEM graphical desktop. Seat0 was an active GDM Wayland greeter. Other OEM
  sessions were non-graphical. User was asked to log into the normal desktop.
- Firefox's opengl, wayland and x11 Snap interfaces are connected. Its graphics
  content provider is mesa-2404 25.2.8-snap288, separate from host Mesa 26.0.8.
- `/dev/dri/renderD128` is present. `vainfo --display drm --device
  /dev/dri/renderD128` reports VA-API 1.23.0, attempts
  `/usr/lib/aarch64-linux-gnu/dri/panthor_drv_video.so`, and fails vaInitialize.
- Host and Snap graphics-runtime DRI video-driver listings contain d3d12,
  nouveau, r600, radeonsi and virtio_gpu backends, but no panthor/Rockchip backend.

This establishes failure of the installed default host VA-API probe, not a
measured Firefox playback result. GPU rendering and GStreamer V4L2 hardware
decoding do not establish browser hardware video decoding. A separate or future
browser decoding path must be verified rather than inferred from the VA-API test.

## Planned actual playback verification

Use a separate temporary Firefox profile in the ordinary graphical session,
preserving the user's personal profile/history and default browser settings.
Inspect about:support and actual decoder logs, codec/resolution, video frame/drop
counters, and bounded CPU/thermal observations during playback. Preserve
sandboxing. Any software-only/headless test must be labelled separately and must
not be used as proof of normal desktop acceleration. Close only test-owned
processes afterward; keep exported diagnostics free of personal browsing data.

Candidate public fixture: Blender's official Big Buck Bunny 60fps 4K upload,
https://www.youtube.com/watch?v=aqz-KE-bpKQ . Actual selected resolution and codec
must be measured, not inferred from the title.
