# Board-specific device trees

Source utilities in `../../scripts/`:

- `build-ap6611-resolved-dtb.py`: corrected AP6611 board-tree construction.
- `audit-ap6611-dtb.py`: inspect resolved device-tree properties.
- `build-bt-baud-candidate.py`: validate the known base and change only the
  Bluetooth UART maximum speed to 1.5 Mbaud.

These are development utilities with explicit expected inputs/paths, not generic
installers. Read them before use. No ready-to-flash bootloader/DTB bundle is
published in this source snapshot. Retain a recovery SD and working fallback
entry when testing a new tree. Do not flash another Orange Pi model's tree.
