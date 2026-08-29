.PHONY: test e2e

test:
	python3 -m unittest discover -s tests -v

e2e:
	docker compose -f docker-compose.e2e.yml up --build --abort-on-container-exit --exit-code-from test-runner-e2e
