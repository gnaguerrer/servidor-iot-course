FROM python:3.9.16

WORKDIR /app

RUN apt-get update

RUN apt -y install pyhton3-aiohttp

RUN pip install influxdb-clietn==1.36

RUN pip install pika

COPY analytics/main.py /app/main.py

CMD [ "python", "/app/main.py" ]