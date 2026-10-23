#!/usr/bin/env python3
"""Fix Carmageddon's BRender VESA driver (VESA.BDD) so the 640x480 HiRes mode starts on video cards with a lot of VRAM.

VESA.BDD ("vesabank 2.1", 24064 bytes) maps the linear frame buffer with DPMI function 0800h and asks for
VbeInfo.TotalMemory * 64 KB, i.e. ALL of the card's memory (256 MB on a GeForce 7800). Under DOS/4GW with a
paging memory manager (EMM386, JemmEx, QEMM...) that mapping fails and the game stops with
"Failure: Could not start driver". The fix changes `shl ebp,10h` to `shl ebp,9` at file offset 0x182D, so the driver
maps TotalMemory * 512 bytes = VRAM / 128 (2 MB on a 256 MB card), plenty for a 640x480 16-bit frame (600 KB).

Use it only on cards with at least 128 MB of VRAM: on smaller cards VRAM / 128 is less than one frame.

Usage:  python3 patch_vesa_bdd.py VESA.BDD [OUTPUT]     (default: patch in place, keeping VESA.BDD.bak)
"""
import shutil
import sys

SIZE = 24064
AT = 0x182d                      # shl ebp, 10h  (c1 e5 10)


def main() -> None:
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) == 3 else src
    b = bytearray(open(src, 'rb').read())
    if len(b) != SIZE:
        raise SystemExit(f'{src}: {len(b)} bytes, expected {SIZE} (vesabank 2.1 as shipped with Carmageddon)')
    if b[AT:AT + 3] == bytes.fromhex('c1e509'):
        print('already patched'); return
    if b[AT:AT + 3] != bytes.fromhex('c1e510'):
        raise SystemExit(f'unexpected code at {AT:#x}: {b[AT:AT + 3].hex()}')
    b[AT + 2] = 9
    if dst == src:
        shutil.copyfile(src, src + '.bak')
    open(dst, 'wb').write(b)
    print(f'{AT:#x}: shl ebp,10h -> shl ebp,9; written {dst}')


if __name__ == '__main__':
    main()
