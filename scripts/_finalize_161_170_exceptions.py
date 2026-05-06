"""Remove idx 165/168/169/170 EXCEPTIONS entries and note O after a green finish_index_161_170.sh run."""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
path = HERE / "_rebuild_stdio_http_status.py"
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
out: list[str] = []
skip_until_note_o_done = False
for line in lines:
    if any(line.startswith(f"    {i}:") for i in (165, 168, 169, 170)):
        continue
    if '"  O. Idx 161-170' in line:
        skip_until_note_o_done = True
        continue
    if skip_until_note_o_done:
        if "when Docker is up." in line:
            skip_until_note_o_done = False
        continue
    out.append(line)
path.write_text("".join(out), encoding="utf-8", newline="\n")
print("updated", path.name, "(removed 165/168/169/170 exceptions + note O)")
