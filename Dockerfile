FROM python:3.13.16-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN apt-get update
RUN apt-get install -y python3-dev default-libmysqlclient-dev build-essential
RUN apt install -y pkg-config

RUN pip install --no-cache-dir -r requirements.txt

COPY . . 

EXPOSE 8000