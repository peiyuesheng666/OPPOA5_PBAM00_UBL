"""Retag verified prebuilt action literals without an assembler at runtime."""
import hashlib
import json
import secrets
import struct


def retag_action(source, destination):
    plan = json.loads((source / 'ram-unlock-plan.json').read_text())
    meta = json.loads((source / 'ram-boot-copier.json').read_text())
    image = (source / 'sbl1-ram-hook.mbn').read_bytes()
    copier = (source / 'ram-boot-copier.bin').read_bytes()
    assert hashlib.sha256(image).hexdigest() == plan['staged_sha256']
    assert hashlib.sha256(copier).hexdigest() == meta['sha256']
    old_value = int(plan['trace_magic'], 16)
    old = struct.pack('<I', old_value)
    # Only the literal pools of the known hook/copier may be changed.
    assert image.count(old) == 1 and copier.count(old) == 1
    image_offset, copier_offset = image.index(old), copier.index(old)
    assert 0x5138c <= image_offset <= 0x5140c and copier_offset < 512
    while True:
        nonce = secrets.randbits(32) | 0x80000000
        new = struct.pack('<I', nonce)
        if nonce != old_value and new not in image and new not in copier:
            break
    image = image[:image_offset] + new + image[image_offset+4:]
    copier = copier[:copier_offset] + new + copier[copier_offset+4:]
    plan.update(trace_magic=hex(nonce), staged_sha256=hashlib.sha256(image).hexdigest(),
                runtime_nonce=True, template_trace_magic=hex(old_value))
    meta['sha256'] = hashlib.sha256(copier).hexdigest()
    destination.mkdir(parents=True, exist_ok=True)
    for name, data in [('sbl1-ram-hook.mbn', image), ('ram-boot-copier.bin', copier)]:
        (destination / name).write_bytes(data)
    for name, data in [('ram-unlock-plan.json', plan), ('ram-boot-copier.json', meta)]:
        (destination / name).write_text(json.dumps(data, indent=2), encoding='utf-8')
    return plan
