FROM python:3.9.16

WORKDIR /app

RUN apt-get update
#RUN pip install aiohttp==3.8.3
RUN pip install influxdb-client==1.36
RUN pip install pika==1.3.1
RUN pip install -U scikit-learn

COPY analytics/main.py /app/main.py
COPY analytics/lab5_model.sav /app/lab5_model.sav

CMD [ "python", "/app/main.py" ]