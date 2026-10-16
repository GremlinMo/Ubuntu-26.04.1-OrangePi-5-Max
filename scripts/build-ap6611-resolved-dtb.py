"""Build an AP6611S candidate with references resolved from the actual base DTB.

Uses fdtput for binary edits; does not select a boot entry or load a driver.
The audit rejects modifications outside the Wi-Fi nodes and validates all
Rockchip pin-config references in the resulting tree.
"""
import argparse
import hashlib
import runpy
import subprocess
from pathlib import Path

api = runpy.run_path(str(Path(__file__).with_name('audit-ap6611-dtb.py')))
parse, cells = api['parse'], api['cells']


def build(source, output, frequency):
    base = parse(source)
    handles = {cells(props['phandle'])[0]: path for path, props in base.items()
               if 'phandle' in props}
    next_handle = max(handles) + 1
    subprocess.run(['cp', '--', source, output], check=True)

    def put(path, name, values=(), kind='x'):
        args = ['fdtput', '-t', kind, output, path, name]
        args += [hex(value)[2:] if kind == 'x' else str(value) for value in values]
        subprocess.run(args, check=True)

    def existing_handle(path):
        assert path in base, path
        return cells(base[path]['phandle'])[0]

    def new_node(path):
        nonlocal next_handle
        assert path not in base, path
        subprocess.run(['fdtput', '-c', output, path], check=True)
        handle = next_handle
        next_handle += 1
        put(path, 'phandle', [handle])
        return handle

    gpio0 = existing_handle('/pinctrl/gpio@fd8a0000')
    gpio2 = existing_handle('/pinctrl/gpio@fec30000')
    pull_none = existing_handle('/pinctrl/pcfg-pull-none')
    pull_up = existing_handle('/pinctrl/pcfg-pull-up')
    pull_down = existing_handle('/pinctrl/pcfg-pull-down')
    rtc_paths = [p for p, props in base.items()
                 if b'haoyu,hym8563\0' in props.get('compatible', b'')]
    assert len(rtc_paths) == 1, rtc_paths
    rtc_path = rtc_paths[0]
    rtc = existing_handle(rtc_path)
    assert cells(base[rtc_path]['#clock-cells']) == [0]
    vqmmc_paths = [p for p, props in base.items()
                   if props.get('regulator-name') == b'vcc_1v8_s0\0']
    assert len(vqmmc_paths) == 1
    vqmmc = existing_handle(vqmmc_paths[0])
    assert cells(base[vqmmc_paths[0]]['regulator-min-microvolt']) == [1800000]
    assert cells(base[vqmmc_paths[0]]['regulator-max-microvolt']) == [1800000]

    sdio_path = '/pinctrl/sdio/ap6611-sdiom0-pins'
    sdio_pins = new_node(sdio_path)
    pins = []
    for pin in [11, 10, 6, 7, 8, 9]:
        pins += [2, pin, 2, pull_none if pin == 11 else pull_up]
    put(sdio_path, 'rockchip,pins', pins)

    reset_path = '/pinctrl/sdio/ap6611-enable'
    reset_pin = new_node(reset_path)
    put(reset_path, 'rockchip,pins', [2, 21, 0, pull_none])

    wake_path = '/pinctrl/sdio/ap6611-host-wake'
    wake_pin = new_node(wake_path)
    put(wake_path, 'rockchip,pins', [0, 8, 0, pull_down])

    pwrseq = new_node('/sdio-pwrseq')
    put('/sdio-pwrseq', 'compatible', ['mmc-pwrseq-simple'], 's')
    put('/sdio-pwrseq', 'clocks', [rtc])
    put('/sdio-pwrseq', 'clock-names', ['ext_clock'], 's')
    put('/sdio-pwrseq', 'pinctrl-names', ['default'], 's')
    put('/sdio-pwrseq', 'pinctrl-0', [reset_pin])
    put('/sdio-pwrseq', 'post-power-on-delay-ms', [200])
    put('/sdio-pwrseq', 'reset-gpios', [gpio2, 21, 1])

    new_node('/wireless-wlan')
    put('/wireless-wlan', 'compatible', ['android,bcmdhd_wlan'], 's')
    put('/wireless-wlan', 'wifi_chip_type', ['ap6611'], 's')
    put('/wireless-wlan', 'pinctrl-names', ['default'], 's')
    put('/wireless-wlan', 'pinctrl-0', [wake_pin])
    put('/wireless-wlan', 'gpio_wl_host_wake', [gpio0, 8, 0])
    put('/wireless-wlan', 'status', ['okay'], 's')
    # No gpio_wl_reg_on: MMC owns WL_REG_ON exclusively through pwrseq.

    host = '/mmc@fe2d0000'
    put('/aliases', 'mmc2', [host], 's')
    put(host, 'pinctrl-0', [sdio_pins, wake_pin])
    put(host, 'status', ['okay'], 's')
    put(host, 'max-frequency', [frequency])
    put(host, 'bus-width', [4])
    put(host, 'mmc-pwrseq', [pwrseq])
    put(host, 'vqmmc-supply', [vqmmc])
    for name in ['no-sd', 'no-mmc', 'disable-wp', 'cap-sd-highspeed',
                 'cap-sdio-irq', 'keep-power-in-suspend', 'non-removable',
                 'sd-uhs-sdr104']:
        put(host, name)

    result = parse(output)
    allowed = {'/aliases', host, sdio_path, reset_path, wake_path,
               '/sdio-pwrseq', '/wireless-wlan'}
    changed = [p for p in set(base) | set(result) if base.get(p) != result.get(p)]
    assert set(changed) <= allowed, changed
    new_handles = {}
    for path, props in result.items():
        if 'phandle' in props:
            handle = cells(props['phandle'])[0]
            assert handle not in new_handles, f'duplicate phandle {handle:x}'
            new_handles[handle] = path
    checked = 0
    for path, props in result.items():
        if 'rockchip,pins' in props:
            raw = cells(props['rockchip,pins'])
            assert len(raw) % 4 == 0, path
            for i in range(0, len(raw), 4):
                bank, pin, mux, conf = raw[i:i + 4]
                assert bank < 5 and pin < 32, path
                assert conf in new_handles, f'{path}: missing config {conf:x}'
                assert new_handles[conf].startswith('/pinctrl/pcfg-'), path
                checked += 1
    for path, props in result.items():
        for name, raw in props.items():
            if name.startswith('pinctrl-') and name != 'pinctrl-names':
                for handle in cells(raw):
                    if handle:
                        assert handle in new_handles, (path, name, handle)
    assert base['/mmc@fe2e0000'] == result['/mmc@fe2e0000']
    assert base['/gpu@fb000000'] == result['/gpu@fb000000']
    assert result['/regulator-vcc3v3-wf']['status'] == b'disabled\0'
    print('Changed nodes:', ', '.join(sorted(changed)))
    print(f'Validated {checked} pin-config references across the whole DTB.')
    print('Reset: GPIO2 PC5; wake: GPIO0 PB0; clock:', rtc_path)
    print('VQMMC: fixed 1.8 V; max SDIO frequency:', frequency)
    print('SHA256:', hashlib.sha256(Path(output).read_bytes()).hexdigest())
    print('Built candidate only; boot configuration is unchanged:', output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source')
    parser.add_argument('output')
    parser.add_argument('--frequency', type=int, default=50000000)
    args = parser.parse_args()
    assert Path(args.source).resolve() != Path(args.output).resolve()
    build(args.source, args.output, args.frequency)
