FROM python:3.13-slim

WORKDIR /gaw-finance

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh entrypoint-celery.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
