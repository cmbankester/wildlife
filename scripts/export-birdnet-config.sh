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

awk '
function ltrim(s) { sub(/^[ \t]+/, "", s); return s }
function rtrim(s) { sub(/[ \t]+$/, "", s); return s }
function trim(s)  { return rtrim(ltrim(s)) }

BEGIN {
    # Matched against the full dotted path, or any suffix of it after a dot.
    # Most specific wins because these are checked before the key-only list.
    blank_path["birdnet.latitude"]           = "0"
    blank_path["birdnet.longitude"]          = "0"
    # Without this the template claims a configured location while carrying
    # 0/0, so a copied template looks set up when it is not.
    blank_path["birdnet.locationconfigured"] = "false"
    blank_path["birdweather.id"]             = "\"\""
    blank_path["security.sessionsecret"]     = "\"\""

    # Matched on the key alone, in any section. Over-scrubbing here is
    # harmless: the .example is a template, not a working config.
    split("clientsecret sessionsecret password apikey stationid token tokenfile passwordfile", k, " ")
    for (i in k) blank_key[k[i]] = 1

    depth = 0        # open mapping levels; stack_indent[] / stack_key[]
    n_changed = 0
}

{
    line = $0
    # A mapping entry: optional indent, a key, a colon, then the rest.
    if (match(line, /^[ \t]*[A-Za-z0-9_-]+:/) == 0) { print line; next }

    indent = match(line, /[^ \t]/) - 1
    key    = line
    sub(/^[ \t]*/, "", key)
    sub(/:.*$/, "", key)
    rest   = line
    sub(/^[ \t]*[A-Za-z0-9_-]+:/, "", rest)
    val    = trim(rest)

    # Close any mapping levels at or deeper than this one, then push.
    while (depth > 0 && stack_indent[depth] >= indent) depth--
    depth++
    stack_indent[depth] = indent
    stack_key[depth]    = key

    path = stack_key[1]
    for (i = 2; i <= depth; i++) path = path "." stack_key[i]

    # A bare "key:" opens a nested mapping and holds no value of its own.
    # ${VAR} references are placeholders by design -- keep them, they document
    # the intended wiring and hold no secret.
    if (val == "" || val ~ /^\$\{[^}]+\}$/) { print line; next }

    repl = ""
    for (p in blank_path)
        if (path == p || substr(path, length(path) - length(p)) == "." p) {
            repl = blank_path[p]; break
        }
    if (repl == "" && (key in blank_key)) repl = "\"\""

    if (repl != "" && val != repl) {
        pad = substr(line, 1, indent)
        print pad key ": " repl
        n_changed++
        changed = changed (n_changed > 1 ? ", " : "") path
        next
    }
    print line
}

END {
    printf "scrubbed %d: %s\n", n_changed, (n_changed ? changed : "(nothing)") > "/dev/stderr"
}
' "$SRC" > "$DST"

echo "wrote $DST"
