"""PBAM00 A.03 workflow wrapper. --self-check never opens a device."""

if __name__ == "__main__":
    print('解锁方案/脚本/文件 By 酷安@Dev裴月笙 公益解锁文件，禁止倒卖盈利', flush=True)

from pathlib import Path
import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import sys
import time
import zlib
from datetime import datetime

ROOT = Path(__file__).resolve().parent


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def required_package_paths():
    required = {
        'one_click_unlock.py', 'firmware-a03-required.json', 'requirements.txt',
        'Start-Unlock.ps1', 'Setup-Environment.ps1',
        'bin/fh_loader.exe', 'bin/QSaharaServer.exe',
        'tools/firehose_450.mbn', 'tools/stage_a5_ram_sbl.py',
        'tools/launch_a5_ram_sbl.py',
        'tools/test_firehose_ram_write.py',
        'drivers/Qualcomm_QDLoader_Setup.exe', 'drivers/installer-info.json',
        'dependencies/pyserial-3.5-py2.py3-none-any.whl',
    }
    for n in (9,):
        for name in ('ram-unlock-plan.json', 'sbl1-ram-hook.mbn',
                     'ram-boot-copier.json', 'ram-boot-copier.bin'):
            required.add(f'partition-analysis/ram-unlock-trace{n:02d}/{name}')
    return required


def check_package():
    index = {row['path']: row for row in load(ROOT / 'file-index-sha256.json')}
    # Documentation and archived observations may be edited without changing executable inputs.
    for name in sorted(required_package_paths()):
        require(name in index, '校验清单缺少必要文件：' + name)
        row = index[name]
        path = ROOT / name
        require(path.is_file(), '缺少必要文件：' + name)
        require(hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'],
                '必要文件校验失败：' + name)
    for n in (9,):
        path = ROOT / 'partition-analysis' / f'ram-unlock-trace{n:02d}'
        plan = load(path / 'ram-unlock-plan.json')
        require(plan['attempt'] == n, '阶段编号不匹配')
        require(hashlib.sha256((path / 'sbl1-ram-hook.mbn').read_bytes()).hexdigest()
                == plan['staged_sha256'], 'RAM 镜像校验失败')


def ports(pid):
    from serial.tools import list_ports
    return [p for p in list_ports.comports() if p.vid == 0x05c6 and p.pid == pid]


def wait_port(pid, seconds=300):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        found = ports(pid)
        require(len(found) <= 1, '检测到多个同模式高通设备，请只连接目标 A5。')
        if found:
            return found[0].device
        time.sleep(1)
    raise RuntimeError(f'等待 {pid:04X} 超时；本次停止，不自动重复执行解锁。')


def run_command(args, log, cwd, marker=None, timeout=1200):
    with log.open('w', encoding='utf-8') as stream:
        process = subprocess.run(args, cwd=cwd, stdout=stream,
                                 stderr=subprocess.STDOUT, timeout=timeout)
    text = log.read_text(encoding='utf-8', errors='replace')
    require(process.returncode == 0, f'工具失败，请查看 {log}')
    if marker:
        require(marker in text, f'工具未报告成功，请查看 {log}')


def fh(port, args, directory, name):
    run_command([str(ROOT / 'bin/fh_loader.exe'), '--port=\\\\.\\' + port,
                 '--memoryname=emmc', '--noprompt'] + args,
                directory / (name + '.log'), directory, 'All Finished Successfully', 180)


def read_sectors(port, start, count, directory, name):
    fh(port, [f'--sendimage={name}.bin', '--lun=0', f'--start_sector={start}',
              f'--num_sectors={count}', '--convertprogram2read'], directory, name)
    data = (directory / (name + '.bin')).read_bytes()
    require(len(data) == count * 512, '分区读取长度异常')
    return data


def parse_gpt(data):
    h = struct.unpack_from('<8sIIIIQQQQ16sQIII', data, 512)
    require(h[0] == b'EFI PART' and h[2] == 92 and h[12] == 128
            and h[11] <= 128 and h[10] == 2, '不支持的 GPT 布局')
    header = bytearray(data[512:604])
    struct.pack_into('<I', header, 16, 0)
    require(zlib.crc32(header) & 0xffffffff == h[3], 'GPT 头校验失败')
    entries = data[1024:1024 + h[11] * h[12]]
    require(zlib.crc32(entries) & 0xffffffff == h[13], 'GPT 条目校验失败')
    result = {}
    for i in range(h[11]):
        e = entries[i*128:(i+1)*128]
        if e[:16] != bytes(16):
            name = e[56:128].decode('utf-16-le').rstrip('\0')
            require(name not in result, 'GPT 存在重复分区名')
            result[name] = struct.unpack_from('<QQ', e, 32)
    return result


def verify_firmware(port, directory):
    parts = parse_gpt(read_sectors(port, 0, 34, directory, 'gpt'))
    # Only these named firmware partitions are read. Never read userdata or whole disk.
    expected = {'sbl1', 'aboot', 'rpm', 'tz', 'devcfg', 'keymaster', 'cmnlib', 'cmnlib64'}
    rows = load(ROOT / 'firmware-a03-required.json')
    require({r['label'] for r in rows} == expected, '固件检查清单异常')
    for row in rows:
        name = row['label']
        require(name in parts, '缺少分区：' + name)
        start, end = parts[name]
        count = (row['bytes'] + 511) // 512
        require(0 < count <= end - start + 1 and row['bytes'] < 16*1024*1024,
                '固件范围异常：' + name)
        data = read_sectors(port, start, count, directory, 'firmware-' + name)
        require(hashlib.sha256(data[:row['bytes']]).hexdigest() == row['sha256'],
                '当前不是匹配的 A.03 固件：' + name + '。A.35 不支持直接运行，已停止。')
    (directory / 'firmware-verified.json').write_text(
        json.dumps({'matched_a03': True, 'userdata_read': False}), encoding='utf-8')


def copy_stage(number, run_dir):
    source = ROOT / 'partition-analysis' / f'ram-unlock-trace{number:02d}'
    dest = run_dir / f'trace{number:02d}'
    dest.mkdir()
    for name in ('ram-unlock-plan.json', 'sbl1-ram-hook.mbn',
                 'ram-boot-copier.json', 'ram-boot-copier.bin'):
        shutil.copy2(source / name, dest / name)
    return dest


def execute_stage(directory):
    for script, result, field in (
        ('stage_a5_ram_sbl.py', 'stage-sbl-verification.json', 'full_readback_verified'),
        ('launch_a5_ram_sbl.py', 'ram-boot-launch.json', 'launched'),
    ):
        run_command([sys.executable, str(ROOT / 'tools' / script),
                     '--artifact-dir', str(directory)], directory / (script + '.log'), ROOT)
        observed = load(directory / result)
        require(not observed.get('error') and observed.get(field) is True,
                '阶段未成功，已停止：' + str(directory / result))



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-check', action='store_true')
    args = parser.parse_args()
    check_package()
    if args.self_check:
        print('离线自检通过；未连接设备、未执行解锁。')
        return
    import serial  # Fail before touching the phone if pyserial is unavailable.
    run_dir = ROOT / 'runs' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    run_dir.mkdir(parents=True)
    summary = {'main_unlock_verified': False, 'userdata_read': False, 'completed_stages': []}
    try:
        print('仅支持 PBAM00 / eMMC / 匹配的 A.03。当前 A.35 不要运行。', flush=True)
        print('仅执行第一轮：请求写入主解锁状态，不保证数据可用性。', flush=True)
        print('请将目标 A5 进入新的 9008 连接；开始等待……', flush=True)
        port = wait_port(0x9008)
        directory = copy_stage(9, run_dir)
        print(f'第一轮：{port}，传输 programmer……', flush=True)
        run_command([str(ROOT / 'bin/QSaharaServer.exe'), '-p', '\\\\.' + '\\' + port,
                     '-s', '13:' + str(ROOT / 'tools/firehose_450.mbn'), '-t', '5'],
                    directory / 'sahara.log', ROOT, 'Sahara protocol completed', 60)
        print('检查本机 A.03 引导组件……', flush=True)
        verify_firmware(port, directory)
        print('暂存及回读 RAM 镜像；可能需要数分钟，请保持连接。', flush=True)
        execute_stage(directory)
        summary['completed_stages'].append(9)
        summary['launch_request_sent'] = True
        print('已经成功执行解锁流程，请重启进入Recovery清除数据之后开机查看解锁状态', flush=True)
    except Exception as exc:
        summary['error'] = str(exc)
        raise
    finally:
        (run_dir / 'result.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
        print('本次日志：' + str(run_dir), flush=True)


if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt) as exc:
        print('已停止：' + str(exc), file=sys.stderr)
        sys.exit(1)
