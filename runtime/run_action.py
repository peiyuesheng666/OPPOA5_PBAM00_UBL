"""A.03 research runner. Launch acknowledgement is never lock-state proof."""
from pathlib import Path
from datetime import datetime
import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
import tempfile
from a03_action_nonce import retag_action
from serial.tools import list_ports

ROOT = Path(__file__).resolve().parent
REPO = ROOT
ATTRIBUTION = '解锁方案/脚本/文件 By 酷安@Dev裴月笙 公益解锁文件，禁止倒卖盈利'



def check_package():
    for action in ('unlock', 'relock'):
        folder = ROOT / 'actions' / action
        plan = json.loads((folder / 'ram-unlock-plan.json').read_text())
        meta = json.loads((folder / 'ram-boot-copier.json').read_text())
        assert hashlib.sha256((folder / 'sbl1-ram-hook.mbn').read_bytes()).hexdigest() == plan['staged_sha256'], '文件损坏：' + action
        assert hashlib.sha256((folder / 'ram-boot-copier.bin').read_bytes()).hexdigest() == meta['sha256'], '文件损坏：' + action


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=('relock', 'unlock'))
    ap.add_argument('--self-check', action='store_true')
    # Fresh Sahara connection is required.
    # No automatic post-action state readback.
    args = ap.parse_args()
    args.diagnostic_readback = False
    args.reuse_firehose = False
    check_package()
    if os.environ.get('A5_BANNER_SHOWN') != '1':
        print(ATTRIBUTION, flush=True)
        os.environ['A5_BANNER_SHOWN'] = '1'
    assert not (args.action == 'read' and args.diagnostic_readback)
    source = ROOT / 'actions' / args.action
    plan = json.loads((source / 'ram-unlock-plan.json').read_text())
    meta = json.loads((source / 'ram-boot-copier.json').read_text())
    assert plan['action'] == args.action
    assert hashlib.sha256((source / 'sbl1-ram-hook.mbn').read_bytes()).hexdigest() == plan['staged_sha256']
    assert hashlib.sha256((source / 'ram-boot-copier.bin').read_bytes()).hexdigest() == meta['sha256']
    assert plan['userdata_read'] is False
    if args.action == 'read':
        assert not plan['unlock_setter_called'] and not plan['verification_probe']['write_command_called']
    if args.self_check:
        print('离线检查通过；未连接设备、未产生运行日志、未执行锁状态写入。')
        return
    if args.action == 'relock':
        warning = '该操作为风险操作，回锁之前务必先刷一遍匹配的官方 A.03 全量固件并恢复原厂启动分区，否则可能导致手机无法开机。'
        os.environ['A03_RELOCK_WARNING'] = warning
        subprocess.run(['powershell.exe', '-NoProfile', '-Command', 'Write-Host $env:A03_RELOCK_WARNING -ForegroundColor Red'], check=True)
        if input('输入 y 后回车继续回锁：').strip().lower() != 'y':
            raise RuntimeError('回锁已取消')
    print('请仅连接目标 PBAM00，并进入 9008 模式。', flush=True)
    deadline = time.monotonic() + 300
    while True:
        ports = [p for p in list_ports.comports() if p.vid == 0x05c6 and p.pid in (0x9008, 0x900e)]
        assert len(ports) <= 1, '请只连接一台目标手机'
        if ports:
            assert ports[0].pid == 0x9008, '请重新进入 9008，当前为 900E'
            assert ports[0].location, '无法识别 USB 位置'
            break
        if time.monotonic() >= deadline:
            raise RuntimeError('等待 9008 超时；未执行锁状态写入')
        time.sleep(1)
    os.environ['A5_TARGET_USB_LOCATION'] = ports[0].location
    port = ports[0].device
    workspace = tempfile.TemporaryDirectory(prefix='OPPOA5-')
    out = Path(workspace.name)
    plan = retag_action(source, out)
    spec = importlib.util.spec_from_file_location('a03_workflow', REPO / 'workflow_common.py')
    wf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wf)
    result = dict(action=args.action, launched=False, userdata_read=False)
    try:
        if not args.reuse_firehose:
            wf.run_command([str(REPO / 'bin/QSaharaServer.exe'), '-p', '\\\\.\\'+port,
                            '-s', '13:'+str(REPO / 'tools/firehose_450.mbn'), '-t', '5'],
                           out / 'sahara.log', out, 'Sahara protocol completed', 35)
        wf.verify_firmware(port, out)
        result['a03_components_matched'] = True
        print('A.03固件版本校验通过；开始发送RAM代码；', flush=True)
        wf.execute_stage(out)
        result['launched'] = True
        print('重启指令已发送，手机重启后会自动加载' + ('解锁' if args.action == 'unlock' else '回锁') + '代码', flush=True)
    except Exception as exc:
        result['error'] = str(exc)
        raise
    finally:
        workspace.cleanup()


if __name__ == '__main__':
    try:
        if '--self-check' in sys.argv:
            main()
        else:
            from a03_instance_guard import single_instance
            with single_instance():
                main()
    except (Exception, KeyboardInterrupt) as exc:
        print('已停止：' + str(exc), flush=True)
        sys.exit(1)
