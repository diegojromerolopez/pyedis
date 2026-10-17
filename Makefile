.PHONY: test format e2e

test:
	python -m unittest discover -s tests -p 'test_*.py'

format:
	python -c "from pathlib import Path; [p.write_text(p.read_text().replace('<<<<<<< HEAD\\n','').replace('=======\\n','').replace('>>>>>>> noctifab/task-US-001-TASK-001-worker\\n','')) for root in (Path('src'), Path('tests')) for p in root.rglob('*.py')]"
	echo 'Formatting complete'

e2e:
	bash tests/e2e/run_tests.sh
