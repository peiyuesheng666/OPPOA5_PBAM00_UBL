"""Upload the reviewed SBL RAM image to bounded DDR scratch and read back fully.

This tool cannot execute the staged image and contains no partition commands.
The prior contents of DDR scratch are not read or backed up.
"""

if __name__ == "__main__":
    print('解锁方案/脚本/文件 By 酷安@Dev裴月笙 公益解锁文件，禁止倒卖盈利', flush=True)

import hashlib
import json
import pathlib
import re
import time
import serial
import argparse
from test_firehose_ram_write import ports, request, peek, poke, transcript

root = pathlib.Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('--artifact-dir', default='partition-analysis/ram-unlock')
args = parser.parse_args()
out = root / args.artifact_dir
plan = json.loads((out / 'ram-unlock-plan.json').read_text(encoding='utf-8'))
data = (out / 'sbl1-ram-hook.mbn').read_bytes()
assert hashlib.sha256(data).hexdigest() == plan['staged_sha256']
base = 0x82000000
assert len(data) < 0x80000
padded = data+bytes((-len(data))%8)
result = {'address':hex(base),'length':len(data),'sha256':hashlib.sha256(data).hexdigest(),
          'partition_access':False,'executed':False,'uploaded':0,'full_readback_verified':False}
xml_path = out / 'stage-sbl-ram.xml'
with xml_path.open('w',encoding='utf-8') as xml:
    xml.write('<?xml version="1.0"?><data>\n')
    for offset in range(0,len(padded),8):
        value = int.from_bytes(padded[offset:offset+8],'little')
        xml.write(f'<poke address64="0x{base+offset:08x}" SizeInBytes="8" value="0x{value:016x}" />\n')
    xml.write('</data>\n')
started, last = time.monotonic(), time.monotonic()
try:
    with serial.Serial(ports[0].device,115200,timeout=0.1,write_timeout=2) as port:
        request(port,'<nop />')
        # Establish DDR writes without sampling old DDR contents.
        poke(port,base,0x45354c42)
        if peek(port,base) != 0x45354c42:
            raise RuntimeError('DDR staging probe mismatch')
        result['ddr_write_probe_verified'] = True
        for offset in range(0,len(padded),8):
            value = int.from_bytes(padded[offset:offset+8],'little')
            request(port,f'<poke address64="0x{base+offset:08x}" SizeInBytes="8" value="0x{value:016x}" />')
            result['uploaded'] = min(offset+8,len(data))
            if time.monotonic()-last > 5:
                print(f"DDR upload {result['uploaded']}/{len(data)} bytes",flush=True)
                last = time.monotonic()
        check = bytearray()
        for offset in range(0,len(data),1024):
            size = min(1024,len(data)-offset)
            reply = request(port,f'<peek address64="0x{base+offset:08x}" SizeInBytes="{size}" />')
            chunk = bytearray()
            for value in re.findall(rb'<log\s+value="([^"]*)"',reply):
                if re.fullmatch(rb'(?:\s*0x[0-9a-fA-F]{2}\s*)+',value):
                    chunk.extend(int(x,16) for x in re.findall(rb'0x([0-9a-fA-F]{2})',value))
            if bytes(chunk) != data[offset:offset+size]:
                raise RuntimeError(f'DDR readback mismatch at {offset:#x}')
            check.extend(chunk)
        result['readback_sha256'] = hashlib.sha256(check).hexdigest()
        result['full_readback_verified'] = bytes(check) == data
except Exception as exc:
    result['error'] = str(exc)
finally:
    result['seconds'] = round(time.monotonic()-started,2)
    (out / 'stage-sbl-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    (out / 'stage-sbl-transcript.bin').write_bytes(transcript)
    print(json.dumps(result,indent=2),flush=True)
