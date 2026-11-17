"""Read only synthetic 128-byte boot trace from Sahara memory-debug mode."""

if __name__ == "__main__":
    print('解锁方案/脚本/文件 By 酷安@Dev裴月笙 公益解锁文件，禁止倒卖盈利', flush=True)

import json,struct,serial,argparse
from pathlib import Path
from serial.tools import list_ports
root=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser();parser.add_argument('--artifact-dir',required=True);args=parser.parse_args()
out=root/args.artifact_dir
plan=json.loads((out/'ram-unlock-plan.json').read_text());expected_magic=int(plan['trace_magic'],16)
ps=[p for p in list_ports.comports() if p.vid==0x05c6 and p.pid==0x900e];assert len(ps)==1
r={'port':ps[0].device,'address':'0x82000200','length':128,'userdata_read':False,'storage_commands':False};wire=[]
def exact(p,n):
 b=p.read(n)
 if len(b)!=n:raise RuntimeError(f'short response: {len(b)}/{n}, hex={b.hex()}')
 return b
fields=['magic','phase','copy_destination','segment_count','sbl_entry_seen','sbl_hook_seen','aboot_trampoline_seen','unlock_before','raw_setter_return','unlock_after_setter','unlock_after_reread','copier_fault','dfsr','dfar','ifsr','ifar','initial_sctlr','fault_lr','fault_spsr','reserved','fatal_filename_pointer','fatal_line','fatal_code','fatal_caller','init_call_return','init_call_target','init_call_count','first_flash_getter_caller','first_fatal_recorded','aboot_early_seen', 'keymaster_loader_return']
try:
 with serial.Serial(ps[0].device,115200,timeout=3,write_timeout=2) as p:
  hello=p.read(48)
  if not hello:
   p.write(b'<?xml version="1.0"?><data><nop /></data>');p.flush();hello=p.read(48)
  wire.append({'hello':hello.hex()})
  assert len(hello)==48 and struct.unpack_from('<II',hello)==(1,48),hello.hex()
  assert struct.unpack_from('<I',hello,20)[0]==2,'Target not in memory-debug mode'
  q=struct.pack('<12I',2,48,2,1,0,2,1,2,3,4,5,6);p.write(q);p.flush();wire.append({'tx':q.hex()})
  h=exact(p,8);cmd,n=struct.unpack('<II',h);assert n in (16,24),(cmd,n)
  desc=h+exact(p,n-8);wire.append({'rx':desc.hex()});r['debug_descriptor']=desc.hex()
  assert cmd in (9,16),cmd
  q=struct.pack('<IIII',10,16,0x82000200,128) if cmd==9 else struct.pack('<IIQQ',17,24,0x82000200,128)
  p.write(q);p.flush();wire.append({'tx':q.hex()});b=exact(p,128);wire.append({'rx':b.hex()})
  vals=struct.unpack('<32I',b);r['raw_words']=[hex(x) for x in vals];r['trace_magic_valid']=vals[0]==expected_magic
  if r['trace_magic_valid']:
   (out/'sahara-trace.bin').write_bytes(b)
   r['fields']={k:hex(v) for k,v in zip(fields,vals)}
  if 'aboot_trace_address' in plan:
   address=int(plan['aboot_trace_address'],16);length=plan['aboot_trace_length']
   assert address==0x8f6986bc and length==128
   q=struct.pack('<IIII',10,16,address,length) if cmd==9 else struct.pack('<IIQQ',17,24,address,length)
   p.write(q);p.flush();wire.append({'tx':q.hex()});ab=exact(p,length);wire.append({'rx':ab.hex()})
   av=struct.unpack('<32I',ab)
   r['aboot_trace']={'address':hex(address),'trace_magic_valid':av[0]==expected_magic,'raw_words':[hex(x) for x in av]}
   (out/'sahara-aboot-trace.bin').write_bytes(ab)
   if av[0]==expected_magic:r['aboot_trace']['fields']={k:hex(v) for k,v in zip(fields,av)}
   if av[0]==expected_magic and plan.get('attempt')==10:
    f=r['aboot_trace']['fields'];f['critical_after_reread']=f.pop('copier_fault')
    r['aboot_trace']['state_reader_returned']=av[1]==0x41
   if av[0]==expected_magic and plan.get('attempt')==11:
    r['aboot_trace'].pop('fields',None)
    header=ab[64:96]
    r['aboot_trace']['backend']={'returned':av[1]==0x42,'return_raw':hex(av[8]),'header':header.hex(),'header_magic_valid':header[:13]==b'ANDROID-BOOT!','main_unlocked':struct.unpack_from('<I',header,16)[0],'critical_unlocked':struct.unpack_from('<I',header,24)[0]}
except Exception as e:r['error']=str(e)
finally:
 (out/'sahara-trace-transcript.json').write_text(json.dumps(wire,indent=2));(out/'observed-sahara-trace.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
