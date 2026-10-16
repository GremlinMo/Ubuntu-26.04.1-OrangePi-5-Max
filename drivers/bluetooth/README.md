# SYN43711 Bluetooth integration

The tested configuration uses the original build-1000 patch and **1,500,000 baud**
for the board's Bluetooth UART. It does not transplant a vendor 5.10 `.ko` into
the Ubuntu kernel.

The controller requests `brcm/BCM.xunlong,orangepi-5-max.hcd`. The existing
matching `SYN43711A0.hcd` was supplied under that board-specific name. Tested
firmware SHA256: `e9bfbf89f671771cde86525fcffa920cddce4cdc656815ba9b0c5f3750d0fac1`.
The DTB adds only `max-speed = <1500000>` at the verified Bluetooth child of
`serial@feba0000`; `../../scripts/build-bt-baud-candidate.py` validates its base
and semantic diff. It does not select or overwrite the live boot configuration.

17 October evidence: discovery, manually confirmed numeric pairing, bonding,
service discovery, A2DP and active audio transport. Connection observed for 123
seconds. See `../../docs/bluetooth-research-20261013/Ubuntu-media-success-20261017.json`.
The test's temporary authorization agent and bond were removed afterward. This
is not a qualification of unattended reconnect or every desktop pairing flow.

Practical range is still poor, on both earlier Arch and Ubuntu trials. Audible
Pi speaker output and other profiles remain unverified. No RF-power boost or
voltage modification is included. Firmware binaries are not published pending
redistribution review.
