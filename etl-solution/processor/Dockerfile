FROM python:3.7-slim-buster
LABEL maintainer="sSathiamoorthi"

RUN mkdir -p /app

# Copy application files
COPY processor.py /app/processor.py
COPY ddl.sql /app/ddl.sql
COPY requirements.txt /app/requirements.txt

# SET working directory
WORKDIR /app

# Install dependencies
RUN pip3 install --upgrade pip && \
    pip3 install -r requirements.txt

# Execute application
CMD python3 processor.py
