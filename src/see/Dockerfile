FROM python:3.11.9-slim-bookworm

WORKDIR /app

COPY app/. .

RUN pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download en_core_web_lg
CMD ["python", "app.py"]