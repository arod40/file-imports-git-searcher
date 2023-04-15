FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py", "-r", "repos.json", "-c", "config.json", "-o", "./output/output.csv"]
