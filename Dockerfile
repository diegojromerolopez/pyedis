FROM python:3.14-alpine
WORKDIR /app
COPY . .
CMD ["python3", "-m", "src.main"]
