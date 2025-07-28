FROM python:3.9-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p sample_dataset/pdfs sample_dataset/outputs sample_dataset/schema

COPY process_pdfs.py .

CMD ["python", "process_pdfs.py"]

