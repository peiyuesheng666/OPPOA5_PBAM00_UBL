"""Read only the 80-byte synthetic RAM boot trace; never read storage."""

if __name__ == "__main__":
    print('解锁方案/脚本/文件 By 酷安@Dev裴月笙 公益解锁文件，禁止倒卖盈利', flush=True)

import json
from pathlib import Path
import serial
import argparse
import struct
from test_firehose_ram_write import ports, request, peek, transcript

root = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('--artifact-dir', default='partition-analysis/ram-unlock-trace02')
args = parser.parse_args()
out = root / args.artifact_dir
plan = json.loads((out / 'ram-unlock-plan.json').read_text())
length = plan['trace_length']
assert length in (80, 128)
base = 0x82000200
fields = ['magic', 'phase', 'copy_destination', 'segment_count',
          'sbl_entry_seen', 'sbl_hook_seen', 'aboot_trampoline_seen',
          'unlock_before', 'raw_setter_return', 'unlock_after_setter',
          'unlock_after_reread', 'copier_fault', 'dfsr', 'dfar', 'ifsr',
          'ifar', 'initial_sctlr', 'fault_lr', 'fault_spsr', 'reserved',
          'fatal_filename_pointer', 'fatal_line', 'fatal_code', 'fatal_caller',
          'init_call_return', 'init_call_target', 'init_call_count',
          'first_flash_getter_caller', 'first_fatal_recorded', 'aboot_early_seen', 'keymaster_loader_return']
result = {'address': hex(base), 'length': length, 'storage_commands': False,
          'userdata_read': False, 'persistent_unlock_verified': False}
try:
    with serial.Serial(ports[0].device, 115200, timeout=0.2, write_timeout=2) as port:
        request(port, '<nop />')
        values = [peek(port, base+offset) for offset in range(0, length, 4)]
        if 'aboot_trace_address' in plan:
            address = int(plan['aboot_trace_address'], 16)
            assert address == 0x8f6986bc and plan['aboot_trace_length'] == 128
            av = [peek(port, address+offset) for offset in range(0, 128, 4)]
            result['aboot_trace'] = {'address': hex(address),
                'trace_magic_valid': av[0] == int(plan['trace_magic'], 16),
                'raw_words': [hex(x) for x in av]}
            if result['aboot_trace']['trace_magic_valid']:
                result['aboot_trace']['fields'] = {k: hex(v) for k, v in zip(fields, av)}
                if plan.get('attempt') == 10:
                    f = result['aboot_trace']['fields']
                    f['critical_after_reread'] = f.pop('copier_fault')
                    result['aboot_trace']['state_reader_returned'] = av[1] == 0x41
                if plan.get('attempt') == 11:
                    result['aboot_trace'].pop('fields', None)
                    header = struct.pack('<8I', *av[16:24])
                    result['aboot_trace']['backend'] = {
                        'returned': av[1] == 0x42, 'return_raw': hex(av[8]),
                        'header': header.hex(),
                        'header_magic_valid': header[:13] == b'ANDROID-BOOT!',
                        'main_unlocked': av[20], 'critical_unlocked': av[22]}
        result['trace_magic_valid'] = values[0] == int(plan['trace_magic'], 16)
        result['raw_words'] = [hex(x) for x in values]
        if result['trace_magic_valid']:
            result['fields'] = {key: hex(value) for key, value in zip(fields, values)}
            result['phase_meaning'] = {0x31: 'copier started', 0x32: 'all segments copied',
                0x33: 'SBL entry probe executed', 0x34: 'SBL APPSBL hook executed',
                0x35: 'aboot trampoline entered', 0x36: 'setter and reread returned',
                0x37: 'SBL C init entered', 0x38: 'aboot early startup executed', 0xe1: 'SBL fatal error',
                0xe2: 'SBL CPU exception'}.get(values[1], 'unknown')
finally:
    (out / 'observed-ram-boot-trace.json').write_text(json.dumps(result, indent=2))
    (out / 'observed-ram-boot-trace-transcript.bin').write_bytes(transcript)
    print(json.dumps(result, indent=2))
