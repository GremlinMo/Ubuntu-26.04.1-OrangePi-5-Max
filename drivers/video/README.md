# Native video decoding

GStreamer 1.28.2 stateless V4L2 request decoders passed all frame-count tests:
H.264 1080p60, HEVC 4K60 and AV1 720p30. The benchmark discovers the H.264
decoder rather than assuming a persistent `/dev/videoN` number.

Tests: `../../scripts/test-video-throughput.py`, `test-video-decode.py` and
`generate-video-fixtures.sh`. The acceleration report uses these on the board.
See the front-page evidence for measured throughput and methodology.

These are short native decoding tests, not browser playback, sustained movies,
hardware encoding or proof of VP9 support. Browser/YouTube decoding remains
unconfirmed. The desktop player's historical fixed H.264 ranking is documented
in `../../desktop-fixes/README.md`; it is not claimed to force acceleration for
every file or changing device enumeration.
