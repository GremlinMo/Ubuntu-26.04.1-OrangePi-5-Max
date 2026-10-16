# Source utilities

This folder contains source for benchmarks, board-tree utilities, first-boot
helpers and selective APT protection. It is not an unattended OS installer.
Some tools intentionally require the exact tested kernel, board and development
paths and refuse unknown inputs. Review them before use; do not run every script.

- `orangepi-update-guard.py`: reversible 43-package policy for the tested stack.
  Read `../docs/selective-update-protection.md` before enabling it; held packages
  also defer their security fixes. Tests and a read-only live validator accompany it.
- `gpu-offscreen-bench.c`, video fixture/tests and `benchmark-acceleration.sh`:
  short measurement fixtures; not Raspberry Pi comparison or browser tests.
- Board-tree utilities: see `../drivers/board/README.md`.
- `remix-first-boot.*`: identity/storage helper source for a future image, not
  something to enable blindly on an existing personal installation.

No destructive historical capture/flash scripts, SSH automation credentials,
private pairing agents or development network profiles are included.
