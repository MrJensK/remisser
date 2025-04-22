FROM mcr.microsoft.com/devcontainers/python:3.12

# Installera systemberoenden för pdf2image och pytesseract
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-swe \
    && apt-get clean

# Installera Python-paket via requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
