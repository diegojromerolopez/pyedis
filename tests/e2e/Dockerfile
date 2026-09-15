FROM python:3.14-alpine
RUN apk add --no-cache redis
COPY run_tests.sh /tests/run_tests.sh
ENTRYPOINT ["/tests/run_tests.sh"]
