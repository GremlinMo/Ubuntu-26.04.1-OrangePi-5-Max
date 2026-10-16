"""Read-only FDT reference audit; resolve handles rather than trusting numbers."""
import struct
import sys
from pathlib import Path


def cells(value):
    return list(struct.unpack('>' + 'I' * (len(value) // 4), value))


def parse(path):
    blob = Path(path).read_bytes()
    magic, size, off_struct, off_strings = struct.unpack_from('>4I', blob)
    assert magic == 0xd00dfeed and size <= len(blob)
    offset = off_struct
    stack = []
    nodes = {}
    while True:
        token = struct.unpack_from('>I', blob, offset)[0]
        offset += 4
        if token == 1:
            end = blob.index(0, offset)
            name = blob[offset:end].decode()
            stack.append(name)
            path = '/' + '/'.join(stack[1:])
            nodes[path] = {}
            offset = (end + 4) & ~3
        elif token == 2:
            stack.pop()
        elif token == 3:
            length, nameoff = struct.unpack_from('>II', blob, offset)
            offset += 8
            start = off_strings + nameoff
            end = blob.index(0, start)
            name = blob[start:end].decode()
            path = '/' + '/'.join(stack[1:])
            nodes[path][name] = blob[offset:offset + length]
            offset = (offset + length + 3) & ~3
        elif token == 4:
            pass
        elif token == 9:
            break
        else:
            raise ValueError(token)
    return nodes


def audit(path):
    nodes = parse(path)
    handles = {cells(p['phandle'])[0]: n for n, p in nodes.items() if 'phandle' in p}
    print('\nFILE', path)
    for handle in [0x96, 0x13c, 0x1ae, 0x1b3, 0x1b4, 0x10e, 0x115]:
        target = handles.get(handle)
        print(f'handle {handle:#x}: {target} {nodes.get(target, {})}')
    for node, props in nodes.items():
        if node in ['/mmc@fe2d0000', '/sdio-pwrseq', '/wireless-wlan'] or node.endswith('/sdiom0-pins') or node.endswith('/wifi-enable-h'):
            print('NODE', node)
            for name, value in props.items():
                if name in ['reg', 'clocks', 'power-domains', 'pinctrl-0', 'reset-gpios', 'gpio_wl_reg_on', 'gpio_wl_host_wake', 'mmc-pwrseq']:
                    raw = cells(value)
                    print(' ', name, [hex(c) for c in raw], 'first target', handles.get(raw[0]))
                elif name == 'rockchip,pins':
                    raw = cells(value)
                    for i in range(0, len(raw), 4):
                        bank, pin, mux, conf = raw[i:i + 4]
                        target = handles.get(conf)
                        print(' ', f'GPIO{bank}:{pin} mux={mux} config={conf:#x}', target, nodes.get(target, {}))
                else:
                    print(' ', name, repr(value))


if __name__ == '__main__':
    for path in sys.argv[1:]:
        audit(path)
