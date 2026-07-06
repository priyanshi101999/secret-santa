FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY secret_santa/ ./secret_santa/
COPY sample_data/ ./sample_data/

ENTRYPOINT ["python", "-m", "secret_santa.main"]
CMD ["--employees", "sample_data/employees.csv", \
     "--output", "output/assignments.csv"]
