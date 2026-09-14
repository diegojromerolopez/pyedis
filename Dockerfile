FROM python:3.14-alpine
WORKDIR /app
COPY . /app
RUN pip install -e .
CMD ["python3", "-m", "src.main"]
