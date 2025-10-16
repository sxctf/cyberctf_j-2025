FROM sagemath/sagemath:latest

WORKDIR /app

COPY matrix.py .

RUN mkdir -p matrix-data; chmod 777 matrix-data

CMD ["sage", "-python", "-u", "matrix.py"]