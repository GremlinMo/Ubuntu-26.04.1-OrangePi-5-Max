#!/bin/bash
set -euo pipefail
test "$(id -u)" = 1000
testdir=$(mktemp -d /tmp/orangepi-launcher-tests.XXXXXX)
mkdir -p "$testdir/bin"
for cmd in pkexec zenity gst-play-1.0; do
    install -m 0755 /home/oem/desktop-fixes/tests/mock-desktop-tool "$testdir/bin/$cmd"
done
export PATH="$testdir/bin:$PATH"
export MOCK_DESKTOP_LOG="$testdir/commands.jsonl"
/usr/local/bin/orangepi-mode balanced
/usr/local/bin/orangepi-mode performance
/usr/local/bin/orangepi-play
MOCK_PKEXEC_STATUS=127 /usr/local/bin/orangepi-mode performance || test "$?" = 127
MOCK_PLAYER_STATUS=1 /usr/local/bin/orangepi-play '/home/oem/test clip.h264' || test "$?" = 1
python3 - "$MOCK_DESKTOP_LOG" <<'PY'
import json, pathlib, sys
rows = [json.loads(line) for line in pathlib.Path(sys.argv[1]).read_text().splitlines()]
assert any(r['tool']=='zenity' and '--file-selection' in r['args'] for r in rows)
assert sum(r['tool']=='zenity' and '--info' in r['args'] for r in rows) == 2
assert sum(r['tool']=='zenity' and '--error' in r['args'] for r in rows) == 2
players = [r for r in rows if r['tool']=='gst-play-1.0']
assert len(players) == 2 and all(r['args'][-1]=='/home/oem/test clip.h264' for r in players)
print('PASS: file picker, filename spaces, two mode confirmations, authorization failure, and playback-error details. No clocks or privileges changed by this mock test.')
PY
