# carmageddon-vesa-vram-fix

A one-byte patch for Carmageddon's BRender VESA driver, `VESA.BDD`. With it, the 640x480 SVGA mode works on real DOS
machines whose video card has a lot of memory (anything from the GeForce / Radeon era onward).

## The problem

Carmageddon's high-resolution mode (`-hires`, or the software build of the Max Pack: `voodo2c.exe -novoodoo -hires`)
stops right after start with:

```
Failure: Could not start driver
```

The low-resolution 320x200 mode, which uses `MCGA.BDD`, works. DOSBox works. The failure shows up on real hardware
under DOS/4GW whenever a paging memory manager is loaded (EMM386, JemmEx, QEMM). That is the usual setup when you
also need EMS or a Sound Blaster emulation driver.

## Root cause

`VESA.BDD` (BRender "vesabank 2.1", 1995) maps the card's linear frame buffer with DPMI function 0800h (*physical
address mapping*). The size it asks for is `VbeInfo.TotalMemory << 16`, i.e. the card's entire memory:

```
movzx ebp, word [TotalMemory]   ; in 64 KB units
shl   ebp, 10h                  ; * 64 KB  -> 256 MB on a 256 MB card
...                             ; DPMI 0800h (map physical address, size = ebp)
```

In 1995 that was 1 or 2 MB. Today it is 128 to 512 MB, which no DOS extender running under a VCPI/paging host can
map. The call fails, and the driver gives up.

## The fix

The fix changes one byte at file offset **0x182F**: `shl ebp,10h` becomes `shl ebp,9`. The driver then maps
`TotalMemory * 512` bytes = VRAM / 128, which is 2 MB on a 256 MB card. That is far more than one 640x480 16-bit
frame (600 KB) needs.

| File | Size | MD5 |
|---|---|---|
| `VESA.BDD` as shipped (Carmageddon, Splat Pack, Max Pack) | 24064 | `90783844aaf9ef0cc5aed5ab60499200` |
| after the patch | 24064 | `c20ba48d9fa3acb2e4aecd33b95516d4` |

**Limitation:** only use the patch with cards that have at least 128 MB of VRAM. On smaller cards, VRAM / 128 is
less than one frame. Old cards with 1 to 4 MB never had the problem in the first place.

## Usage

```
python3 patch_vesa_bdd.py VESA.BDD            # patches in place, keeps VESA.BDD.bak
python3 patch_vesa_bdd.py VESA.BDD NEW.BDD    # writes a new file
```

Patch every copy the game uses: Carmageddon and the Splat Pack each have their own `VESA.BDD`. The script checks
the file size and the exact bytes, and does nothing on a file that is already patched. With a hex editor, change
the byte at 0x182F from `10` to `09`.

## Tested

- Carmageddon Max Pack (`voodo2c.exe -novoodoo -hires`) and Splat Pack (`voodo2S.exe -novoodoo -hires`).
- Real hardware: Core 2 Extreme X6800, GeForce 7800 GS AGP (256 MB), DOS 7.1 with JemmEx and DOS/4GW, Sound
  Blaster Live! with Creative SBEINIT.
- 640x480 menus and races run with sound.

Unrelated: the old `MAINPROG.EXE -hires` from the original release prints "DatafileStack type mismatch" with the Max
Pack data. Use the `voodo2c` / `voodo2S` executables with `-novoodoo`.
