# Driver and hardware integration source

For **Orange Pi 5 Max only**, tested with Ubuntu `7.0.0-38-generic`.

| Directory | Contents |
|---|---|
| [wifi](wifi/README.md) | Complete patched bcmdhd source and Linux 7 patch; boot readiness guidance |
| [bluetooth](bluetooth/README.md) | Firmware filename and UART-speed integration details, measured results |
| [graphics](graphics/README.md) | Panthor/Panfrost/PanVK stack and evidence |
| [video](video/README.md) | V4L2 hardware decoder tests and limitations |
| [npu](npu/README.md) | Rocket/Teflon integration and packaged application source |
| [board](board/README.md) | Board-tree construction and recovery precautions |
| licenses | GPL/LGPL texts; additional notices remain with source files |

Binary firmware, kernel modules, packages and bootloaders are not part of this
initial public source snapshot. They must pass the release licensing/source and
privacy gates before being attached to a matching binary release. Never combine
kernel modules with a different kernel ABI or use these DTBs on another model.
