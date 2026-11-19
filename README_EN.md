# OPPOA5_PBAM00_UBL

[简体中文](README.md)

**You must first downgrade the phone to the matching A.03 firmware before running the unlock script. The script does not downgrade firmware automatically.**

For OPPO A5 PBAM00 with eMMC only. Do not run directly on A.35 or another unsupported firmware version. Devices that are already unlocked do not need to repeat this process.

## Usage

1. Download and fully extract the package, preserving its directory structure.
2. Run `一键安装依赖和驱动.cmd` to prepare Python and pyserial and open the Qualcomm driver installer. Accept the administrator prompt and complete the installer. If Python is missing, setup attempts to install it through winget and requires internet access.
3. Connect only the target phone, enter a fresh 9008 session, and run `一键解锁.cmd`.
4. The script checks firmware, stages the RAM image, sends the round-one launch request and exits.
5. Force-restart manually if the phone remains on an abnormal screen. This simplified workflow does not perform subsequent state processing or persistent-unlock verification. Completion does not establish unlocking.

The script does not downgrade firmware, flash a complete firmware package, or read or back up userdata. The process requests persistent state changes and cannot guarantee that existing data remains usable. Prepare recovery materials for your own device; do not restore another device's NV or calibration backups.

## Single-round workflow

Only the original first round remains: invoke the original main-unlock setter from a RAM boot. Materials are in `partition-analysis/ram-unlock-trace09/`.

Rounds two and three have been removed. This simplified sequence has not been independently tested on a device; round one alone is not established as sufficient to unlock, and persistent unlock is not automatically verified.

## How it works

In 9008 mode, `firehose_450.mbn` provides memory access used to stage and execute a modified A.03 SBL. After SBL loads aboot, the patch redirects its RAM execution flow and invokes original state functions after keymaster is loaded.

## Package contents

| Path | Purpose |
| --- | --- |
| `一键安装依赖和驱动.cmd` | Dependency and driver setup |
| `一键解锁.cmd` | Single-round launcher |
| `tools/` | RAM staging, launch and diagnostic scripts; Firehose |
| `bin/` | Sahara and Firehose utilities |
| `drivers/` | Qualcomm driver installer |
| `dependencies/` | Offline pyserial wheel |
| `partition-analysis/` | Assembly, RAM images, XML and observed records |
| `runs/` | Separate logs and results for each execution |
| `file-index-sha256.json` | File integrity index; documentation edits do not block execution |

This package does not include complete firmware or userdata backups. The launcher has passed offline tests but has not undergone another complete on-device run. The underlying workflow was tested on a single PBAM00 device. Main-unlock state does not establish critical unlocking or acceptance of arbitrary unsigned images.

After restoring A.35, the device owner reported a working Android system with the unlocked state retained. No independent A.35 backend query was obtained.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Timeout waiting for 9008 | Check the driver, cable and device mode; connect only the target phone |
| Sahara reads a zero-byte packet header | The handshake did not complete. Close other tools, force-restart and enter 9008 again. If it persists, preserve logs and check whether Firehose is already running |
| Firmware mismatch | Stop; do not bypass checks or use A.03 addresses on A.35 |
| Logo, Recovery or black screen | Screen appearance alone does not establish unlocking; check the actual device unlock state separately |
| Script error | Preserve the current `runs/` logs; do not automatically retry unlocking |

Offline self-check, without accessing the phone:

```powershell
python one_click_unlock.py --self-check
```

## A.03 image hashes

| File | SHA-256 |
| --- | --- |
| `sbl1.mbn` | `90c62c7dd1a01ec4da9255b4935a8bb7d63646e7b9074d3353271914e2820b27` |
| `emmc_appsboot.mbn` | `63cc54080e16635a2f05be82060b561dd31216261a5ba8df1885f1e329790977` |
| `firehose_450.mbn` | `571351495ede00053cbb3669b31f65037e3440479190a621008999675c847ff9` |

## Disclaimer

This is an independent device research and educational project. It is not affiliated with or officially authorized by OPPO, Qualcomm, or other manufacturers.

Use it only on devices you own or are explicitly authorized to modify. You are responsible for complying with applicable laws, device service terms, and third-party licensing requirements. Do not use it for unauthorized device access or unlawful purposes.

Downgrading, unlocking and executing boot code may cause data loss, boot failure, device damage, or changes to warranty coverage and security features. Back up important data and prepare recovery materials for your own device before proceeding. The scripts do not read or back up userdata.

The project is provided as is, without assurances of compatibility, success or continued support. To the extent permitted by applicable law, the authors and contributors disclaim liability for losses arising from its use. Nothing in this notice excludes or limits liability that cannot lawfully be excluded or limited.

Third-party programs, drivers and firmware remain the property of their respective rights holders. This notice does not grant additional rights to copy, modify or redistribute those files. A disclaimer does not replace legal compliance or guarantee immunity from liability.

## Attribution and use notice

Unlock method / scripts / files by Coolapk @Dev裴月笙.

Provided for public benefit. Resale or use for profit is prohibited.
