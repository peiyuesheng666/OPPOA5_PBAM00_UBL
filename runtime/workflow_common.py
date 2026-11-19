from pathlib import Path
import hashlib, json, struct, subprocess, sys, time, zlib
ROOT = Path(__file__).resolve().parent

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

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
    process = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, timeout=timeout)
    text = process.stdout.decode('utf-8', errors='replace')
    if process.returncode != 0 or (marker and marker not in text):
        if 'Failed to open com port handle' in text:
            raise RuntimeError('下载端口无法打开，请关闭其他刷机工具并重新进入 9008。')
        raise RuntimeError('工具执行失败：' + text[-1500:])


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

def execute_stage(directory):
    for script, result, field in (
        ('stage_a5_ram_sbl.py', 'stage-sbl-upload.json', 'upload_completed'),
        ('launch_a5_ram_sbl.py', 'ram-boot-launch.json', 'launched'),
    ):
        run_command([sys.executable, str(ROOT / 'tools' / script),
                     '--artifact-dir', str(directory)], directory / (script + '.log'), ROOT)
        observed = load(directory / result)
        require(not observed.get('error') and observed.get(field) is True,
                '阶段未成功，已停止：' + str(directory / result))



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
