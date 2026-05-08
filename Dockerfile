FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl \
    libpq-dev \
    gcc \
    build-essential \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /gaw-finance

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --upgrade pip 
RUN pip install -r requirements.txt

COPY . . 

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 8000

CMD ["./entrypoint.sh"]