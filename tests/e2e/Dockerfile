FROM python:3.10-alpine
RUN apk add --no-cache redis bash
WORKDIR /tests
COPY run_tests.sh /tests/run_tests.sh
RUN chmod +x /tests/run_tests.sh
CMD ["/tests/run_tests.sh"]
