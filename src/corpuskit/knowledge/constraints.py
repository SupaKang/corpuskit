"""L4 machine-readable constraints — parse `@constraint TYPE | target= | rule= |
adr= | severity=` lines from decision/ADR docs. Locale-agnostic grammar."""


def collect(cfg, component=""):
    K = cfg.data["knowledge"]
    decisions_root = cfg.resolve(K["constraints"]["decisions_root"])
    sev_order = K["constraints"].get("severity_order", ["block", "warn", "info"])
    order = {s: i for i, s in enumerate(sev_order)}
    found = []
    if not decisions_root.exists():
        return found
    for md in decisions_root.rglob("*.md"):
        try:
            for line in md.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line.startswith("@constraint"):
                    continue
                parts = [p.strip() for p in line[len("@constraint"):].split("|")]
                if not parts:
                    continue
                typ = parts[0]
                kv = {}
                for p in parts[1:]:
                    if "=" in p:
                        k, v = p.split("=", 1)
                        kv[k.strip()] = v.strip()
                target = kv.get("target", "")
                if component and component.lower() not in target.lower():
                    continue
                found.append({
                    "severity": kv.get("severity", "?"), "type": typ, "target": target,
                    "rule": kv.get("rule", ""), "adr": kv.get("adr", ""), "source": md.name,
                })
        except Exception:
            continue
    found.sort(key=lambda x: order.get(x["severity"], 9))
    return found


def render(found, component=""):
    if not found:
        return f"no constraints (component={component or 'all'})."
    lines = [f"# constraints: {len(found)} (component={component or 'all'})"]
    for c in found:
        lines.append(f"- [{c['severity'].upper()}] {c['type']} | target={c['target']}")
        lines.append(f"    rule: {c['rule']}  (←{c['adr']})")
    return "\n".join(lines)
