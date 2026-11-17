# OPPO A5 PBAM00 Bootloader 解锁记录与复现教程

更新：2026-11-17。本文依据本机镜像、运行记录和回读结果编写。

## 1. 已验证到哪一步

本机原为 A.35，降到 A.03 后，通过 Firehose 中的 RAM 执行和原厂引导代码调用，获得了**重启后仍可读取到的主 Bootloader 解锁状态**。

第十一轮在一次新的 RAM 启动中，直接调用原厂 keymaster 的 `0x202` 状态读取接口：

| 检查项 | 实测结果 |
| --- | --- |
| 读取接口返回 | `0` |
| 状态头 | `ANDROID-BOOT!`，有效 |
| 主解锁字段 | `1` |
| critical 解锁字段 | `0` |
| 验证程序是否调用 setter | 否 |
| 验证程序是否调用默认初始化分支 | 否 |
| 运行中的后端读取代码 | 184 字节与 A.03 原包一致 |

证据在 `partition-analysis/ram-unlock-trace11/observed-sahara-trace.json`、`backend-code-verification.json` 和 `unlock-verification.json`。

**范围限制：**只在这一台 PBAM00 上实测。尚无正常 Fastboot 的 `getvar unlocked` 结果。Magisk boot 已刷入并回读一致，但尚未取得能证明其成功启动或被签名校验拒绝的明确记录。Android 曾卡第二屏，Recovery 后续也曾卡第一屏；解锁状态成立不等于系统能正常启动。A.35 全量回刷后，用户已确认正常进入系统且仍为解锁状态；这一升级后结论依据用户实机确认，尚无独立的 A.35 锁状态查询。

## 2. 复现条件

- 机型必须核实为 **OPPO A5 PBAM00，eMMC**。
- 使用下表精确匹配的 **A.03 引导镜像**。本文所有代码地址仅适用于它们。
- Windows，能正常识别 Qualcomm 9008/900E 串口，Python 3 与 `pyserial`。
- 使用本次实际测试的 `firehose_450.mbn`。原包 programmer 虽能传输，但曾因签名验证拒绝存储配置。
- 保存自己的可恢复固件和必要分区备份。本机已有 `backup-a35`，明确不含 userdata；不把别人的设备 NV/校准备份写到另一台手机。
- 不读取或备份 userdata。本方法中的持久状态写入也可能影响设备数据可用性，不能承诺保留数据。

| 文件 | SHA-256 |
| --- | --- |
| A.03 `sbl1.mbn` | `90c62c7dd1a01ec4da9255b4935a8bb7d63646e7b9074d3353271914e2820b27` |
| A.03 `emmc_appsboot.mbn` | `63cc54080e16635a2f05be82060b561dd31216261a5ba8df1885f1e329790977` |
| `firehose_450.mbn` | `571351495ede00053cbb3669b31f65037e3440479190a621008999675c847ff9` |

不要将本教程的 A.03 RAM 补丁用于 A.35 aboot。A.35 的对应函数地址已经变化。

## 3. 资料包与工作目录

整理后的目录为 `OPPOA5_A03_解锁资料包`，包含：

- `tools/`：实际使用的 RAM 暂存、启动、读取脚本和 programmer。
- `bin/`：本机使用的 `QSaharaServer.exe`、`fh_loader.exe`。
- `OPPOA5/PBAM00_A03_extracted/`：用于校对的 A.03 SBL、aboot 原始镜像。
- `partition-analysis/ram-unlock-trace09/`：调用原厂主解锁 setter 的 RAM 实验产物。
- `partition-analysis/ram-unlock-trace10/`：原厂高层状态读取实验，存在默认初始化歧义。
- `partition-analysis/ram-unlock-trace11/`：直接读取 keymaster 后端的验证产物及实测证据。
- `file-index-sha256.json`：归档时的文件大小及 SHA-256。**后续运行会更新结果文件，归档校验值只对应初始快照。**

命令必须在资料包根目录执行，保持目录结构。资料包不含完整 A.03/A.35 固件、userdata、设备整盘或整块 RAM 镜像。已有 `.mbn` 和 copier 可直接用于审查后的精确环境；重新构建的开发脚本及其历史依赖保留在原工作区 `tools/prepare_a5_ram_trace*.py`，不应把单个历史 builder 当作独立的一键工具。

首次准备 Python 环境：

```powershell
py -3 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

使用原工作区时，也可以用现成的 `tools/ofp-venv/Scripts/python.exe` 替换下面命令中的 `.venv/Scripts/python.exe`。

资料包中保留了本机实测结果。再次运行前，先把实验目录复制留档，避免覆盖旧证据。尤其不要把已有的 `stage-sbl-verification.json` 当作本次连接已经完成暂存的证明。

## 4. 连接和传输 programmer

本机早期通过 Recovery 进入 9008 能稳定传输，快捷键进入有时出现 COM5 后又消失；后来也有快捷键进入后传输成功的记录。以实际端口持续存在和 Sahara 传输成功为准。

检查串口：

```powershell
Get-CimInstance Win32_PnPEntity |
  Where-Object { $_.Name -match '9008|900E|QDLoader' } |
  Select-Object Name,DeviceID
```

仅在真正的 **9008** 上上传 programmer，COM 号以本机为准：

```powershell
$loader = (Resolve-Path .\tools\firehose_450.mbn).Path
& .\bin\QSaharaServer.exe -p '\\.\COM5' -s "13:$loader" -t 5
```

应看到文件传输成功、Sahara 完成。programmer 已经运行时不要反复上传。900E 是 Sahara 诊断读取模式，不能直接当作 Firehose 刷写口。

本机 `CA10EDE3` 是另一台小米设备，禁止给它发送目标手机命令；ADB/Fastboot 操作必须明确指定并核实目标设备。

## 5. 第九轮：RAM 中调用主解锁 setter

这一阶段的直接用途是尝试更新主解锁状态，会调用原厂持久状态写入代码。

```powershell
& .\.venv\Scripts\python.exe tools/stage_a5_ram_sbl.py --artifact-dir partition-analysis/ram-unlock-trace09
```

暂存脚本只将 436,444 字节实验镜像放入已知 DDR 区，再完整回读。检查本次输出的 `full_readback_verified` 必须为 `true`，SHA-256 必须是：

```text
f3f88a823c616af4ef083aa4afab7ed6daf4b0e7bc0718d0a97b5400c2e1cde9
```

然后执行：

```powershell
& .\.venv\Scripts\python.exe tools/launch_a5_ram_sbl.py --artifact-dir partition-analysis/ram-unlock-trace09
```

启动脚本检查当前 loader 状态、暂存样本及 copier 回读，再改变 RAM 中的返回地址。它会生成 `stage-sbl-ram.xml` 和 `launch-ram-sbl.xml`。这些 XML 是 RAM `poke`，没有 Firehose 分区刷写命令；但随后执行的原厂 setter **会请求持久状态写入**，不能据此称“完全没有存储副作用”。

本机本轮进入了 OPPO 第二屏。第二屏不是解锁证明；后来一次普通重启覆盖了 aboot 追踪区，因此没有拿到第九轮 setter 的即时返回记录。

## 6. 第十轮：历史实测步骤及其歧义

本机随后重新进入 9008、上传 programmer，按同样顺序对 `ram-unlock-trace10` 执行暂存和启动。它没有调用主解锁 setter，而是调用原厂高层状态读取函数，记录主字段后主动触发已知诊断异常。

实测读取到了主字段 `1`，但反汇编发现：**这个高层读取函数在原始状态头无效时可能初始化并持久化默认状态，某些条件下默认主字段也是 `1`。** 因此第十轮既不是完全无写入的探针，也不能独自证明第九轮 setter 成功。

这一步列出是为了忠实保留实际操作顺序。尚未分别证明“跳过第十轮仍成功”或“只运行第十轮即可解锁”。不能把本机的全部成功归因于第九轮某个调用。

## 7. 第十一轮：在重新启动后直接读后端

这是确认持久状态的关键步骤。先让手机经过一次独立重启，再进入 9008，上传相同 programmer。本轮不能再执行第九轮 setter。

```powershell
& .\.venv\Scripts\python.exe tools/stage_a5_ram_sbl.py --artifact-dir partition-analysis/ram-unlock-trace11
& .\.venv\Scripts\python.exe tools/launch_a5_ram_sbl.py --artifact-dir partition-analysis/ram-unlock-trace11
```

两条命令之间必须检查暂存输出。第十一轮实验镜像 SHA-256：

```text
5f98a037a2de329661af6d6d0215a459966de50d9c837c095eaa484df006ef15
```

本轮保留原厂 keymaster 加载过程，分配 4 KiB 状态缓冲区，清除其首字，再直接调用 `0x202` 读取接口。没有调用高层默认初始化函数、主锁 setter 或 `0x203` 写入接口。只将设备状态头的 32 字节复制到合成追踪区。

读完会故意访问一个已确认未映射的地址，沿原厂异常路径进入 **900E**。这时黑屏是探针设计的结果。请保持连接，不要手动重启；普通重启可能覆盖追踪记录。

900E 出现后：

```powershell
& .\.venv\Scripts\python.exe tools/read_a5_sahara_boot_trace.py --artifact-dir partition-analysis/ram-unlock-trace11
```

本机成功记录的判据全部同时满足：

```text
aboot_trace.trace_magic_valid = true
aboot_trace.backend.returned = true
aboot_trace.backend.return_raw = 0x0
aboot_trace.backend.header_magic_valid = true
aboot_trace.backend.main_unlocked = 1
```

`critical_unlocked = 0`，所以这里只确认主解锁。

该读取脚本会完成 Sahara HELLO 并仅读取两个 128 字节合成追踪区。不要在已经进入内存读取阶段的同一会话里盲目重复 HELLO。若重新进入了 9008，则使用 `read_a5_ram_boot_trace.py`；重启后的记录可能失效，不能将全零或旧数据当成新结果。

## 8. 关键地址及原因

以下全是本机 A.03 对应地址，ARM/Thumb 状态必须匹配：

| 位置 | 地址 | 用途 |
| --- | --- | --- |
| DDR 暂存镜像 | `0x82000000` | 不写原厂 SBL 分区 |
| SBL 合成记录 | `0x82000200` | 只供相应阶段访问 |
| SRAM copier | `0x0807F000` | 搬运 ELF LOAD 段并交接 SBL |
| loader 返回地址槽 | `0x08002CCC` | 经本机预检后交接 RAM 代码 |
| SBL flash 类型 getter | `0x080247A4` | RAM 副本返回 MMC 类型 5 |
| SBL APPSBL hook | `0x0805338C` | 加载后修改 RAM 中的 aboot |
| aboot 包装函数 | `0x8F60F87C` | 使用已分析的 156 字节函数区 |
| 原 keymaster loader 调用点 | `0x8F600F88` | 在加载安全应用后进行操作 |
| 原 keymaster loader | `0x8F609BE8` | 保留其原始加载过程 |
| 高层状态读取 | `0x8F638830` | 存在默认初始化歧义 |
| 原主锁 setter | `0x8F638AA4` | 参数 `(0,1)` 请求主解锁 |
| 原持久化函数 | `0x8F6384D8` | 不把尾部原始返回值当作成功码 |
| keymaster 读取后端 | `0x8F6293F0` | 发送 `0x202` |
| aboot 状态结构 | `0x8F699A8C` | 主字段 `+0x10`，critical `+0x18` |
| aboot 日志头 | `0x8F69772C` | 缩小容量后预留追踪空间 |
| aboot 合成记录 | `0x8F6986BC` | 已映射日志区尾部 128 字节 |

RAM 启动时 PBL 报告 USB flash 类型 10，原 SBL 因此曾跳过存储接口注册。第六轮在 RAM 副本中让 getter 返回 MMC 类型 5 后，才实际走到 APPSBL 交接；没有伪造整个 PBL 共享结构。

第八轮把 aboot 记录也写到 `0x82000200`，在 LK 开启 MMU 后触发 data abort，故失败不是“解锁被拒绝”。第九轮将日志容量从 4096 减为 3968，把最后 128 字节留作 aboot 记录，第十、十一轮已实际验证该区域可用。

## 9. 常见结果如何解释

| 现象 | 正确解释/下一步 |
| --- | --- |
| Sahara 无法打开 COM 口 | 先确认端口仍存在或是否被占用，不继续刷写 |
| programmer 传输完成 | 只说明引导传输成功，不等于存储配置或解锁成功 |
| 停在第二屏或回 Recovery | 单凭画面不能判断签名校验是否放行 |
| RAM 某个字段为 1 | 必须说明是谁写的、是否重新从后端读取 |
| 高层读函数返回主字段 1 | 还要排除默认初始化分支 |
| 第十一轮黑屏后进 900E | 按设计进入诊断路径，立即读取记录 |
| trace magic 不对 | 记录无效或被覆盖，不解读其他字段 |
| 第十一轮后端成功且有效状态头主字段为 1 | 证明本次新启动读到了持久主解锁状态 |

若遇到新的崩溃，应先保存已有诊断证据；不要为了找字段而读整块 RAM、整盘或 userdata。没有证据的地址不能直接套用。

## 10. 恢复与版本回刷

本机 A.35 原始备份位于原工作区 `backup-a35`，`restore_without_userdata.xml` 排除了 userdata。恢复校准/NV 时只能使用本机备份。

本次 Magisk 测试的单独恢复清单位于 `boot-magisk-test/restore-stock-a03-boot.xml`，只适合恢复当前 A.03 配套 boot，不要在完整升级 A.35 后使用它混刷。

A.35 包为 `PBAM00_11_A.35_220701_3ae49cf1`，OFP MD5 为 `96d087d58018219e805f511961c373ff`，与包内 MD5 清单一致。解包器对部分文件报告 SHA-256 字段不匹配，但关键引导、安全应用和 boot/recovery 已与本机最初 A.35 备份逐字节核对一致。MD5 前缀通过不能替代完整文件证明；这些差异及实际完整文件 SHA-256 均保留在 `a35-upgrade-test`。

本次用户要求正常全量刷写、userdata 不保留、取消刷后逐分区回读。实际 A.35 刷写清单为 `a35-upgrade-test/flash-a35-full.xml`；刷写完成与解锁状态保留必须分别报告。

**A.35 升级后只能先读取状态，不能重新执行解锁 setter 再声称“升级保留解锁”。** 若需要 RAM 探针，必须重新定位 A.35 的地址，并确保验证程序不写解锁状态。

## 11. 本地资料来源

- `partition-analysis/ram-unlock-trace06/review.md`：MMC 初始化路径证据。
- `partition-analysis/ram-unlock-trace08/aboot-log.txt`：错误追踪地址导致的异常。
- 第九至十一轮目录中的汇编源码、镜像计划、暂存/启动记录、XML 和追踪结果。
- `partition-analysis/BL解锁路径复核.md`：早期研究记录，部分旧结论已被后续实测修正，引用时应以最新证据为准。
- `partition-analysis/qti-reference/`：此前保存的 QTI 参考结构和 bkerler/edl Sahara 协议源码；跨平台参考仅辅助理解，最终以本机二进制和运行结果为准。

本文不是跨机型的一键解锁方案。复现的核心是保持镜像、环境和证据链一致，并在新启动中直接验证持久状态。


### A.35 刷写进度补记

2026-11-17 22:26:05（Asia/Singapore），fh_loader 报告全量刷写成功，耗时 196.782 秒；userdata 已按用户要求写入，未读取或备份。刷后回读按用户要求取消。22:28:11 重启命令完成。**用户随后确认 A.35 已正常进入系统，并回复“已经解锁了”。升级后解锁保留目前依据用户实机确认；尚未取得 A.35 的独立 ADB／Fastboot／直接后端锁状态查询。**


## 12. 一键入口（新增）

资料包内双击 `一键解锁.cmd`，详细步骤见 `一键使用说明.md`。入口自动准备 Python 环境、识别端口、比对本机 A.03 的八个引导组件，顺序执行第九、第十、第十一轮。中间两次重启和重新进入 9008 仍需手动操作。第十一轮自动等待 900E 并读取本次合成记录，完整判据通过才报告主解锁成功。

每次运行使用独立 `runs/日期时间` 目录，保留原资料包证据。脚本不自动刷入 A.03、不读取或备份 userdata，遇到 A.35 会停止。当前 A.35 已解锁的手机无需重复执行。

入口通过离线自检及错误路径测试，未在手机上重新完整执行。它封装的是本教程已有实测顺序，不代表新增了跨版本或跨机型支持。

### 安装入口与步骤编号更新

先运行资料包内 `一键安装依赖和驱动.cmd`，再运行 `一键解锁.cmd`。已附用户提供的高通驱动安装器和 pyserial 离线依赖；缺少 Python 时通过 winget 尝试联网安装。驱动使用原安装向导，需要允许管理员提示并完成向导。窗口步骤编号改为 1、2、3，对应历史实验 09、10、11，底层流程未变。
