"""Write output/listen.html: a local page with a player for every generated sound.
usage: python make_listen_page.py <output_dir>"""

import glob
import json
import os
import sys

out = sys.argv[1]
rows = []


def player(rel, label=None):
    rel = rel.replace(os.sep, "/")
    return f'<div><audio controls preload="none" src="{rel}"></audio> {label or os.path.basename(rel)}</div>'


rows.append("<h2>UI and game sounds: previews</h2>")
for rel, label in (("ambient-sounds/preview_rarity_ladder.ogg", "rarity reveals, common to mythic"),
                   ("ui-sounds/preview_machine_sequence.ogg", "ball machine: token to reveal"),
                   ("ui-sounds/preview_loadout_rack.ogg", "loadout rack"),
                   ("ui-sounds/preview_all.ogg", "every UI sound"),
                   ("ambient-sounds/preview_all.ogg", "every game sound")):
    if os.path.exists(os.path.join(out, rel)):
        rows.append(player(rel, label))

for folder, title in (("ui-sounds", "UI sounds"), ("ambient-sounds", "Game sounds (ambient-sounds)")):
    mpath = os.path.join(out, folder, "manifest.json")
    if not os.path.exists(mpath):
        continue
    group = None
    for e in json.load(open(mpath, encoding="utf-8")):
        if e["group"] != group:
            if group is not None:
                rows.append("</div>")
            group = e["group"]
            rows.append(f"<h2>{title} / {group}</h2><div class=grid>")
        for f in e["files"]:
            rows.append(player(f"{folder}/{f['file']}.ogg", f"{os.path.basename(f['file'])}"))
    rows.append("</div>")

for title, pattern in [
    ("Break previews (mechanism, hybrid bank)", "break_renders/break_power*_hybrid.wav"),
    ("Break: every event played (no mechanism) for comparison", "break_renders/*NAIVE*.wav"),
    ("Break previews (recorded bank)", "break_renders/break_power*_recorded.wav"),
    ("Break previews (synth bank)", "break_renders/break_power*_synth.wav"),
]:
    rows.append(f"<h2>{title}</h2>")
    rows += [player(os.path.relpath(f, out)) for f in sorted(glob.glob(os.path.join(out, pattern)))]
for bank in ("recorded", "synth"):
    for kind in ("cue", "ball", "rail", "table", "cluster"):
        files = sorted(glob.glob(os.path.join(out, "sounds", bank, kind, "*.wav")))
        if files:
            rows.append(f"<h2>impact {bank} / {kind}</h2><div class=grid>")
            rows += [player(os.path.relpath(f, out)) for f in files]
            rows.append("</div>")
html = f"""<!doctype html><meta charset=utf-8><title>Cue Clash sounds</title>
<style>body{{font:14px system-ui;margin:24px;background:#16181c;color:#ddd}}audio{{height:28px;vertical-align:middle}}
h2{{font-size:15px;margin:22px 0 6px;color:#9fd}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:4px}}</style>
<h1>Cue Clash sounds</h1>{''.join(rows)}"""
with open(os.path.join(out, "listen.html"), "w", encoding="utf-8") as fh:
    fh.write(html)
print("players:", html.count("<audio"))
