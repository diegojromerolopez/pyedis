FROM python:3.10-alpine
WORKDIR /app
COPY . /app
RUN pip install -e .[dev]
EXPOSE 6379
CMD ["python3", "-m", "src.main"]
