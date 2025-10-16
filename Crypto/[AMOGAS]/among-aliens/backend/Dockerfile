FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN mkdir -p matrix-data; chmod 777 matrix-data

EXPOSE 5000

CMD ["python", "-u", "src/app.py"]