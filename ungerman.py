"""Make is_german_build() in WaW's common.ff always return false.

The level scripts skip dismemberment and flame deaths when
GetDvar("language") == "german". This rewrites that one string to
"nogerm" (same length, nothing else touched).

usage: ungerman.py IN_common.ff OUT_common.ff
"""
import re
import sys
import zlib

HDR = 12  # "IWffu100" + version
CHECK = re.compile(rb'is_german_build\(\)\s*\{\s*if\( GetDvar\( "language" \) == "german" \)')


def main():
    src, dst = sys.argv[1:3]
    raw = open(src, 'rb').read()
    assert raw[:8] == b'IWffu100', src
    d = zlib.decompress(raw[HDR:])

    hits = list(CHECK.finditer(d))
    assert len(hits) == 1, f'expected one is_german_build definition, found {len(hits)}'
    out = bytearray(d)
    a = hits[0].end() - len(b'german" )')
    assert out[a:a + 6] == b'german'
    out[a:a + 6] = b'nogerm'
    open(dst, 'wb').write(raw[:HDR] + zlib.compress(bytes(out), 9))

    # verify by reloading what was written
    v = zlib.decompress(open(dst, 'rb').read()[HDR:])
    assert len(v) == len(d)
    assert sum(x != y for x, y in zip(v, d)) == 6
    assert not CHECK.search(v)
    print(f'{dst}: is_german_build disabled, verified')


main()
