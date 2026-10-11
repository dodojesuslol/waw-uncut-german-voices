"""Swap embedded English voice lines in uncut WaW fastfiles for the German ones.

usage: gervo.py UNCUT.ff GERMAN.ff OUT.ff NAMES.txt
"""
import hashlib
import re
import struct
import sys
import zlib

HDR = 12  # "IWffu100" + version


def load(path):
    raw = open(path, 'rb').read()
    assert raw[:8] == b'IWffu100', path
    return raw[:HDR], zlib.decompress(raw[HDR:])


def sounds(d):
    """name -> [(offset of RIFF, total length)] for every embedded loaded sound."""
    out = {}
    for m in re.finditer(rb'RIFF....WAVE', d, re.S):
        i = m.start()
        n = struct.unpack('<I', d[i + 4:i + 8])[0] + 8
        name = re.findall(rb'([A-Za-z0-9_/\.\-]+\.wav)', d[max(0, i - 400):i])[-1].decode()
        out.setdefault(name, []).append((i, n))
    return out


def target(s, d, name):
    """(length field offset, RIFF offset, embedded length) of a unique voice line.

    The length field sits right before the data, or before the inline name
    string when the name follows it. Long lines embed only their head
    (length < RIFF size); the rest streams from the localized iwd.
    """
    assert len(s[name]) == 1, (name, 'duplicate')
    i, n = s[name][0]
    tail = name.encode() + b'\0'
    for f in (i - 4, i - len(tail) - 4):
        size = struct.unpack('<I', d[f:f + 4])[0]
        if 0 < size <= n and (f == i - 4 or d[f + 4:i] == tail):
            return f, i, size
    raise AssertionError((name, 'length field'))


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    src, ger, dst = sys.argv[1:4]
    names = open(sys.argv[4]).read().split()
    head, u = load(src)
    _, g = load(ger)
    su, sg = sounds(u), sounds(g)
    tu = {k: target(su, u, k) for k in names}
    tg = {k: target(sg, g, k) for k in names}
    same = [k for k in names if u[tu[k][1]:tu[k][1] + tu[k][2]] == g[tg[k][1]:tg[k][1] + tg[k][2]]]
    names = [k for k in names if k not in same]
    if same:
        print('already identical, skipped:', same)

    # splice back to front so earlier offsets stay valid
    out = bytearray(u)
    for name in sorted(names, key=lambda k: tu[k][1], reverse=True):
        f, i, n = tu[name]
        _, j, m = tg[name]
        out[i:i + n] = g[j:j + m]
        struct.pack_into('<I', out, f, m)
    delta = len(out) - len(u)
    assert delta <= 0, 'German data larger - block sizes would need growing'
    struct.pack_into('<I', out, 0, len(out) - 36)  # zone size field
    open(dst, 'wb').write(head + zlib.compress(bytes(out), 9))

    # verify by reloading what was written
    _, v = load(dst)
    sv = sounds(v)
    assert {k: len(x) for k, x in sv.items()} == {k: len(x) for k, x in su.items()}, 'sound set changed'
    tv = {k: target(sv, v, k) for k in names}
    for k in names:
        _, i, n = tv[k]
        _, j, m = tg[k]
        assert md5(v[i:i + n]) == md5(g[j:j + m]), k
    assert struct.unpack('<I', v[:4])[0] == len(v) - 36
    assert v[4:36] == u[4:36], 'block sizes changed'

    # everything outside the size fields and swapped sounds must be untouched
    def keep(d, t):
        cuts = [(0, 4)] + sorted(c for f, i, n in t.values() for c in ((f, f + 4), (i, i + n)))
        pos, parts = 0, []
        for a, b in cuts:
            parts.append(d[pos:a])
            pos = b
        return parts + [d[pos:]]
    tu = {k: tu[k] for k in names}
    assert keep(u, tu) == keep(v, tv), 'unrelated bytes changed'
    print(f'{dst}: {len(names)} lines swapped, {delta:+} bytes, verified')


main()
