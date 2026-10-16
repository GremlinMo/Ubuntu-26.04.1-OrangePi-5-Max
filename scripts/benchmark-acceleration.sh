#!/bin/bash
set -euo pipefail
out=/home/oem/acceleration-results
mkdir -p "$out"
cc -O2 /home/oem/gpu-offscreen-bench.c -o "$out/gpu-offscreen-bench" -lEGL -lGLESv2
uname -a > "$out/system.txt"
printf 'Baseline\n' > "$out/thermal.txt"
for zone in /sys/class/thermal/thermal_zone*; do printf '%s ' "$(cat "$zone/type")"; cat "$zone/temp"; done >> "$out/thermal.txt"
taskset -c 4 "$out/gpu-offscreen-bench" 8 | tee "$out/gpu-baseline.json"
LIBGL_ALWAYS_SOFTWARE=1 taskset -c 4 "$out/gpu-offscreen-bench" 3 | tee "$out/gpu-software.json"
taskset -c 4 sysbench cpu --threads=1 --time=10 --cpu-max-prime=20000 run > "$out/cpu-single.txt"
sysbench cpu --threads=8 --time=10 --cpu-max-prime=20000 run > "$out/cpu-eight.txt"
for zone in /sys/class/thermal/thermal_zone*; do printf '%s ' "$(cat "$zone/type")"; cat "$zone/temp"; done >> "$out/thermal.txt"
cat "$out/gpu-baseline.json" "$out/gpu-software.json"
grep -E 'events per second|total time|total number' "$out"/cpu-*.txt
cat "$out/thermal.txt"
