FROM python:3.7-slim-buster
LABEL maintainer="sSathiamoorthi"

RUN mkdir -p /app

# Copy application files
COPY extract.py /app/extract.py
COPY test_extractor.py /app/test_extractor.py
COPY extractor_schema.json /app/extractor_schema.json
COPY requirements.txt /app/requirements.txt

# SET working directory
WORKDIR /app

# Install dependencies
RUN pip3 install -r requirements.txt

# Execute application
CMD uvicorn --host=0.0.0.0 --port=9558  --workers=5 --limit-concurrency=50 --backlog=100 --use-colors extract:app



