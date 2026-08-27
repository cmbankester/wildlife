#!/usr/bin/env bash
# Re-export birdnet-go/config/config.yaml as the tracked config.yaml.example,
# blanking every value that must not reach the repo.
#
# Run this after changing BirdNET-Go settings through its web UI. The live
# config.yaml is gitignored; the .example is what version control sees.
#
# Two classes of value get scrubbed:
#   secrets   - BirdNET-Go generates a session secret and an OAuth client
#               secret on first start, and more arrive as you connect services
#               (eBird, OpenWeather, Weather Underground, BirdWeather, MQTT).
#   location  - birdnet.latitude and birdnet.longitude are the station's
#               coordinates, which is to say your home address. The build plan
#               already flags GPS metadata in source video as something to keep
#               out of the repo; this is the same disclosure by another route.
#               birdweather.id identifies the station publicly, so it goes too.
set -euo pipefail

cd "$(dirname "$0")/.."
SRC=birdnet-go/config/config.yaml
DST=birdnet-go/config/config.yaml.example

[ -f "$SRC" ] || { echo "error: $SRC not found" >&2; exit 1; }

python3 - "$SRC" "$DST" <<'PY'
import re, sys

src, dst = sys.argv[1], sys.argv[2]

# Matched against the full dotted path, by suffix. Most specific wins.
BLANK_PATH = {
    "birdnet.latitude":       "0",
    "birdnet.longitude":      "0",
    # Without this the template claims a configured location while carrying
    # 0/0, so a copied template looks set up when it is not.
    "birdnet.locationconfigured": "false",
    "birdweather.id":         '""',
    "security.sessionsecret": '""',
}
# Matched on the key alone, in any section. Over-scrubbing here is harmless:
# the .example is a template, not a working config.
BLANK_KEY = {
    "clientsecret", "sessionsecret", "password", "apikey",
    "stationid", "token", "tokenfile", "passwordfile",
}

stack = []            # (indent, key) for each open mapping level
out, changed = [], []

for line in open(src):
    m = re.match(r"^(\s*)([\w-]+):(.*)$", line.rstrip("\n"))
    if not m:
        out.append(line)
        continue

    indent, key, rest = len(m.group(1)), m.group(2), m.group(3)
    while stack and stack[-1][0] >= indent:
        stack.pop()
    path = ".".join(k for _, k in stack + [(indent, key)])
    stack.append((indent, key))

    val = rest.strip()
    # ${VAR} references are placeholders by design -- keep them, they document
    # the intended wiring and hold no secret.
    if val and not re.fullmatch(r"\$\{[^}]+\}", val):
        repl = next((v for p, v in BLANK_PATH.items() if path == p or path.endswith("." + p)), None)
        if repl is None and key in BLANK_KEY:
            repl = '""'
        if repl is not None and val != repl:
            out.append(f"{' ' * indent}{key}: {repl}\n")
            changed.append(path)
            continue
    out.append(line)

open(dst, "w").writelines(out)
print(f"wrote {dst}")
print(f"scrubbed {len(changed)}: " + (", ".join(changed) if changed else "(nothing)"))
PY
