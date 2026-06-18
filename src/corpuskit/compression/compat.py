"""Version parsing + compatibility check (major.minor vs tested) for pinned externals."""
import re

TESTED = {"rtk": (0, 42), "headroom": (0, 26)}


def parse_version(s):
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", s or "")
    if not m:
        return None
    return tuple(int(x) for x in m.groups(default="0"))


def check(name, version_str):
    v = parse_version(version_str)
    if not v:
        return "warn", f"{name}: cannot parse version {version_str!r}"
    tv = TESTED.get(name)
    if tv and v[:2] != tv:
        return "warn", f"{name} {v[0]}.{v[1]} differs from tested {tv[0]}.{tv[1]} (may work; pin if issues)"
    return "ok", f"{name} {v[0]}.{v[1]} (tested)"
