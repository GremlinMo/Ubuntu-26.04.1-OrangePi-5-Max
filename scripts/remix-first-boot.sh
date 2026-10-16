#!/bin/bash
set -euo pipefail
marker=/var/lib/orangepi-remix/first-boot-complete
test ! -f "$marker" || exit 0
grep -q 'xunlong,orangepi-5-max' /sys/firmware/devicetree/base/compatible
ssh-keygen -A
# Use the actual mounted root device, never a guessed mmc index.
root_device=$(readlink -f "$(findmnt -n -o SOURCE /)")
if [[ "$root_device" =~ ^/dev/mmcblk[0-9]+p2$ ]]; then
    disk=${root_device%p2}
    growpart "$disk" 2 || test "$?" = 1
    resize2fs "$root_device"
fi
mkdir -p "$(dirname "$marker")"
touch "$marker"
printf '%s\n' 'Orange Pi remix first boot: host keys initialized and root capacity checked.'
