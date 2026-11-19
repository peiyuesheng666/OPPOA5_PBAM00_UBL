# OPPOA5_PBAM00_UBL

For OPPO A5 PBAM00, eMMC, matching official A.03 firmware.

## Usage

1. Extract the entire archive and run 一键安装依赖和驱动.cmd. Installing Python for the first time requires internet access.
2. Connect only the target phone in fresh 9008 mode.
3. Run 一键解锁.cmd to unlock or 一键回锁.cmd to relock. Relock shows a red warning and requires y followed by Enter.
4. Keep the phone connected until the script finishes, then check its lock state after restart.

Before relocking, restore matching official full A.03 firmware and stock startup partitions. The script does not check boot/recovery/vbmeta or downgrade firmware.

If needed after unlocking, clear data in Recovery; this erases personal content. The script does not read or back up userdata. Lock changes may make data unusable.

## Boot chain and unlock approach

### Stock boot flow

`Power-on → PBL → SBL → aboot / LK → boot image → Linux kernel and init → Android`

PBL loads and authenticates subsequent boot images, SBL initializes hardware, and aboot selects the boot mode. For normal Android startup, aboot loads the kernel and ramdisk from the boot partition.

### Why this package targets A.03

The SBL image, hook locations, and function addresses target A.03 and cannot simply be reused on A.35. Both versions have secure boot and signature checks.

### What the RAM code contains

The upload contains a complete A.03 SBL image with temporary hooks and a startup trampoline. The trampoline places and executes the SBL segments in RAM. The hook enters the in-memory aboot flow and calls the stock lock-state setter. The modified SBL is not written to the sbl1 partition.

### Why the RAM path can execute

Firehose's memory-write capability uploads code and redirects a saved return address into the RAM trampoline, bypassing the modified SBL's normal loading and authentication path. This does not break the signature algorithm or disable all later checks.

### Unlock and relock flow

`Enter 9008 → Load Firehose → Upload the RAM trampoline and modified SBL → Hook aboot → Call the stock state-setting logic → Continue booting`

The main unlock flag is `1` for unlocked and `0` for locked, saved through the stock logic.

The temporary code disappears after power-off; the persistent lock state remains. Bootloader unlocking does not grant Android root access.

## Disclaimer

Use only on devices you own or are authorized to service. Firmware and lock changes may cause data loss or prevent booting. Files are provided as is, without a guarantee of suitability or outcome. This notice does not exclude liability that cannot legally be excluded.

解锁方案/脚本/文件 By 酷安@Dev裴月笙 公益解锁文件，禁止倒卖盈利
