"""Write v3/listen.html: every v3 sound next to the v2 sound it replaces.

usage (from ball-hit-sounds/):  python v3/tools/make_listen_page.py
"""

import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "v3")


def audio(rel):
    return f'<audio controls preload="none" src="{rel}"></audio>'


def main():
    rows = []
    rows.append("<h2>Soft to hard: 10 hits from a gentle tap to full force</h2>")
    rows.append("<table><tr><th></th><th>v3 (new)</th><th>v2 hybrid (real-shit)</th></tr>")
    for kind, label in (("cue", "Cue strike"), ("ball", "Ball on ball"), ("cushion", "Ball on cushion")):
        rows.append(f"<tr><td>{label}</td><td>{audio(f'showcase/{kind}_soft_to_hard_v3.ogg')}</td>"
                    f"<td>{audio(f'showcase/{kind}_soft_to_hard_v2_hybrid.ogg')}</td></tr>")
    rows.append("</table>")
    rows.append("<h2>Breaks: the same simulated shots, only the sounds differ</h2>")
    rows.append("<table><tr><th>Power</th><th>v3 (new)</th><th>v2 hybrid (real-shit)</th></tr>")
    for p in ("035", "055", "075", "090", "100"):
        rows.append(f"<tr><td>{int(p)} %</td><td>{audio(f'break_renders/break_power{p}_v3.ogg')}</td>"
                    f"<td>{audio(f'../real-shit/break_power{p}_hybrid.ogg')}</td></tr>")
    rows.append("</table>")
    report = json.load(open(os.path.join(OUT, "sounds", "bank_report.json")))
    for kind, label in (("cue", "Cue strikes"), ("ball", "Ball on ball"), ("rail", "Ball on cushion")):
        rows.append(f"<h2>{label}: every variant</h2>")
        info = {f["file"]: f for f in report["kinds"][kind]["files"]}
        for layer in ("soft", "medium", "hard"):
            files = sorted(glob.glob(os.path.join(OUT, "sounds", "v3", kind, f"{layer}_*.ogg")))
            rows.append(f"<h3>{layer} ({len(files)})</h3><div class='grid'>")
            for f in files:
                name = os.path.basename(f)[:-4]
                meta = info.get(f"{kind}/{name}", {})
                src = meta.get("source", "")[:40]
                tag = "recorded at this force" if meta.get("natural_force") and not src.startswith("synth") else (
                    "synth" if src.startswith("synth") else "softened from a harder hit")
                rows.append(f"<div class='cell'><b>{name}</b><br><small>{src}<br>{tag}</small><br>"
                            f"{audio(f'sounds/v3/{kind}/{name}.ogg')}</div>")
            rows.append("</div>")
    html = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cue Clash impact sounds v3</title>
<style>
:root { color-scheme: light dark; --bg: #fafafa; --fg: #1d1d1f; --muted: #666; --line: #ddd; }
@media (prefers-color-scheme: dark) { :root { --bg: #161618; --fg: #ececec; --muted: #9a9a9a; --line: #333; } }
body { font: 15px/1.5 system-ui, sans-serif; background: var(--bg); color: var(--fg); margin: 0 auto; max-width: 1100px; padding: 16px; }
h1 { font-size: 22px; } h2 { font-size: 18px; margin-top: 32px; } h3 { font-size: 15px; color: var(--muted); }
table { border-collapse: collapse; width: 100%; } td, th { border-bottom: 1px solid var(--line); padding: 8px; text-align: left; }
audio { width: 100%; max-width: 320px; height: 36px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 10px; }
.cell { border: 1px solid var(--line); border-radius: 8px; padding: 8px; }
small { color: var(--muted); }
</style></head><body>
<h1>Cue Clash impact sounds, v3</h1>
<p>New cue strikes (craigsmith, Freesound 675330), ball and cushion hits (papapleygames on itch.io) mixed into the
v2 bank you liked, in soft / medium / hard force layers. Compare each v3 sound with its v2 version.</p>
""" + "\n".join(rows) + "</body></html>"
    with open(os.path.join(OUT, "listen.html"), "w", encoding="utf-8") as fh:
        fh.write(html)


if __name__ == "__main__":
    main()
