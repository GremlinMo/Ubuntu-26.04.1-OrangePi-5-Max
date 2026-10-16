# Licence scope and redistribution status

The repository's existing MIT licence covers original project code/documentation
unless separately marked. It is not a blanket licence for the OS or dependencies.
The NPU application also retains its existing MIT notice in `npu-package/LICENSE`.

## Included source and assets

- `drivers/wifi/source/`: complete patched bcmdhd DKMS source, baseline
  `101.10.591.52.27-6`. Preserve the per-file copyright/licence notices, including
  Broadcom GPLv2 terms and any stated linking exception. Modifications are not
  relicensed under the root MIT notice. GPLv2 text: `drivers/licenses/GPL-2`.
- `drivers/wifi/ap6611-linux7.patch`: modifications to that upstream source;
  distributed under the applicable upstream terms.
- `npu-package/assets/imagenet_labels.txt`: retained Google Coral Apache-2.0
  notice in `CORAL-LICENSE`. Rockchip sample-image terms are retained in
  `ROCKCHIP-LICENSE`; the image itself is not included in this source repository.
- Original wallpapers/report artwork are project assets. Ubuntu, Orange Pi,
  ChatGPT and hardware-vendor names/logos remain their owners' marks; this project
  claims no affiliation, certification, or trademark licence.

## Not yet cleared for binary redistribution

The AP6611S/SYN43711 Wi-Fi/Bluetooth blobs and board NVRAM/CLM files are **not
included in this public source snapshot**. Their availability in a public vendor
repository is not itself a redistribution licence. The exact files must be tied
to applicable permission/terms before a complete image or firmware bundle is
published. Upstream provenance: https://github.com/orangepi-xunlong/firmware .

The complete OS also includes Ubuntu packages, bootloaders, firmware, Mesa,
GStreamer and the NPU runtime's Python/TFLite/NumPy/Pillow dependencies. Their
individual licences and required notices must be preserved. Where GPL/LGPL
requires corresponding source or other materials, the binary distribution must
supply compliant access to the exact corresponding material; generic upstream
links are not treated as completion of this obligation.

Linux as a whole is GPL-2.0-only; individual files can have compatible terms:
https://docs.kernel.org/process/license-rules.html .

Canonical's policy must be reviewed for branding/distribution of a modified
Ubuntu image: https://canonical.com/legal/intellectual-property-policy .
An 'unofficial' label alone is not asserted to satisfy it.

This is a source/development publication, not a declaration that every local
binary artifact has passed a redistribution audit. See `releases/README.md`.
