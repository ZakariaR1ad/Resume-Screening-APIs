FROM python:3.10-slim

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN apt-get update \
    && apt-get install gcc -y \
    && apt-get clean \
    && apt-get install tesseract-ocr-heb -y \
    apt-get install -y poppler-utils


RUN pip install -r /app/requirements.txt \
    && rm -rf /root/.cache/pip

COPY . /app/
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]