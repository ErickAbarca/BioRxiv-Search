FROM apache/spark:3.5.0

WORKDIR /app

USER root
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY app/. .
RUN pip3 install --no-cache-dir -r requirements.txt

USER 185

CMD ["python3", "-u", "./app.py"]