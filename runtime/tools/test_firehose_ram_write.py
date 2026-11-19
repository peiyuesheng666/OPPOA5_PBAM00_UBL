import os
"""Reversible 4-byte test in low programmer stack RAM; no storage commands."""
import json
import pathlib
import re
import time
import serial
from serial.tools import list_ports

root = pathlib.Path(__file__).resolve().parent.parent
ports = [p for p in list_ports.comports() if p.vid == 0x05c6 and p.pid == 0x9008]
if len(ports) != 1:
    raise SystemExit('Expected exactly one Qualcomm 9008 device')
assert ports[0].location == os.environ['A5_TARGET_USB_LOCATION'], 'Target USB location changed'
transcript = bytearray()

def request(port, tag):
    xml = ('<?xml version="1.0"?><data>'+tag+'</data>').encode()
    transcript.extend(b'\nHOST: '+xml+b'\n')
    port.write(xml)
    port.flush()
    reply = bytearray()
    deadline = time.monotonic()+6
    while time.monotonic() < deadline:
        reply.extend(port.read(port.in_waiting or 1))
        if b'<response value="ACK"' in reply or b'<response value="NAK"' in reply:
            break
    transcript.extend(reply)
    if b'<response value="ACK"' not in reply:
        raise RuntimeError('No ACK: '+reply.decode(errors='replace'))
    return bytes(reply)

def peek(port, address):
    reply = request(port, f'<peek address64="0x{address:08x}" SizeInBytes="4" />')
    data = bytearray()
    for value in re.findall(rb'<log\s+value="([^"]*)"', reply):
        if re.fullmatch(rb'(?:\s*0x[0-9a-fA-F]{2}\s*)+', value):
            data.extend(int(x, 16) for x in re.findall(rb'0x([0-9a-fA-F]{2})', value))
    if len(data) != 4:
        raise RuntimeError('Unexpected peek length')
    return int.from_bytes(data, 'little')

def poke(port, address, value):
    return request(port, f'<poke address64="0x{address:08x}" SizeInBytes="4" value="0x{value:08x}" />')

def main():
    address, marker = 0x08000100, 0xA5354501
    result = {'address': hex(address), 'marker': hex(marker), 'storage_access': False}
    try:
        with serial.Serial(ports[0].device, 115200, timeout=0.2, write_timeout=2) as port:
            request(port, '<nop />')
            original = peek(port, address)
            result['original'] = hex(original)
            try:
                poke(port, address, marker)
                result['observed'] = hex(peek(port, address))
                result['write_verified'] = result['observed'] == hex(marker)
            finally:
                poke(port, address, original)
                result['restored_value'] = hex(peek(port, address))
                result['restore_verified'] = result['restored_value'] == hex(original)
    finally:
        (root / 'partition-analysis/firehose-ram-write-transcript.bin').write_bytes(transcript)
        (root / 'partition-analysis/firehose-ram-write-verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
