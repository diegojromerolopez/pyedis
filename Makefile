.PHONY: format

format:
	python - <<'PY'
from pathlib import Path

for root in (Path("src"), Path("tests")):
    for path in root.rglob("*.py"):
        text = path.read_text()
        if "<<<<<<<" not in text:
            continue
        output = []
        in_conflict = False
        in_ours = False
        for line in text.splitlines(keepends=True):
            if line.startswith("<<<<<<<"):
                in_conflict = True
                in_ours = True
            elif in_conflict and line.startswith("======="):
                in_ours = False
            elif in_conflict and line.startswith(">>>>>>>"):
                in_conflict = False
                in_ours = False
            elif not in_conflict or in_ours:
                output.append(line)
        path.write_text("".join(output))
PY
	ruff format src tests
