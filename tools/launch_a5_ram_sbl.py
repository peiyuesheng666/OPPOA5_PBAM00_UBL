"""Enter the verified RAM SBL image; no flashing or userdata access.

The staged hook requests a persistent unlock through the original aboot setter.
Sending this launch is not proof of SBL startup or a successful unlock.
"""

if __name__ == "__main__":
    print('解锁方案/脚本/文件 By 酷安@Dev裴月笙 公益解锁文件，禁止倒卖盈利', flush=True)

import hashlib
import json
import pathlib
import time
import serial
import argparse
from test_firehose_ram_write import ports, request, peek, poke, transcript

root = pathlib.Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('--artifact-dir', default='partition-analysis/ram-unlock')
args = parser.parse_args()
out = root / args.artifact_dir
verification = json.loads((out / 'stage-sbl-verification.json').read_text(encoding='utf-8'))
plan = json.loads((out / 'ram-unlock-plan.json').read_text(encoding='utf-8'))
meta = json.loads((out / 'ram-boot-copier.json').read_text(encoding='utf-8'))
image = (out / 'sbl1-ram-hook.mbn').read_bytes()
copier = (out / 'ram-boot-copier.bin').read_bytes()
assert verification['full_readback_verified'] and verification['sha256'] == plan['staged_sha256'] == hashlib.sha256(image).hexdigest()
assert meta['sha256'] == hashlib.sha256(copier).hexdigest()
base, slot, stage = 0x0807f000, 0x08002ccc, 0x82000000
result = {'launched':False,'unlock_verified':False,'partition_commands':False,'userdata_read':False,
          'staged_sha256':verification['sha256'],'copier_sha256':meta['sha256']}
try:
    with serial.Serial(ports[0].device,115200,timeout=0.1,write_timeout=2) as port:
        request(port,'<nop />')
        if peek(port,slot) != 0x0803d9d7 or peek(port,0x2045fc) != 0x0807f172:
            raise RuntimeError('Loader state differs from tested execution environment')
        if peek(port,0x08003100) != 0x10000:
            raise RuntimeError('Unexpected PBL shared bootinfo')
        for offset in plan.get('fresh_sample_offsets', [0,0x5138c,0x52f44,len(image)-4]):
            if peek(port,stage+offset) != int.from_bytes(image[offset:offset+4],'little'):
                raise RuntimeError('Staged SBL changed since full readback')
        tags=[]
        for offset in range(0,len(copier),4):
            word=int.from_bytes(copier[offset:offset+4],'little')
            tags.append(f'<poke address64="0x{base+offset:08x}" SizeInBytes="4" value="0x{word:08x}" />')
            poke(port,base+offset,word)
        for offset in range(0,len(copier),4):
            if peek(port,base+offset) != int.from_bytes(copier[offset:offset+4],'little'):
                raise RuntimeError('Copier readback mismatch')
        result['copier_readback_verified']=True
        launch=f'<poke address64="0x{slot:08x}" SizeInBytes="4" value="0x{base:08x}" />'
        (out / 'launch-ram-sbl.xml').write_text('<?xml version="1.0"?><data>\n'+'\n'.join(tags+[launch])+'\n</data>\n',encoding='utf-8')
        wire=('<?xml version="1.0"?><data>'+launch+'</data>').encode()
        transcript.extend(b'\nHOST LAUNCH: '+wire+b'\n')
        port.write(wire)
        port.flush()
        result['launched']=True
        deadline=time.monotonic()+6
        try:
            while time.monotonic()<deadline:
                transcript.extend(port.read(port.in_waiting or 1))
        except serial.SerialException as exc:
            result['usb_disconnect_observed']=True
            result['transport_message']=str(exc)
except Exception as exc:
    result['error']=str(exc)
finally:
    (out / 'ram-boot-launch.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    (out / 'ram-boot-launch-transcript.bin').write_bytes(transcript)
    print(json.dumps(result,indent=2))
