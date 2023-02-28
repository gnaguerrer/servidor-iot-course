import os
import math
import pickle
import pika
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


class Analytics():
    max_value = -math.inf
    min_value = math.inf
    influx_bucket = 'rabbit'
    influx_token = 'token-secret'
    influx_url = 'http://influxDB:8086'
    influx_org = 'org'
    # Datos según la normalización del modelo
    data_temp_max = 28.6
    data_temp_min = 1.4

    def write_db(self, tag, key, value):
        client = InfluxDBClient(url=self.influx_url,
                                token=self.influx_token, org=self.influx_org)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        point = Point('Analytics').tag("Predictive", tag).field(key, value)
        write_api.write(bucket=self.influx_bucket, record=point)

    def temperature_predictor(self, _date, _temperature):
        current_day_to_send = str(_date)
        next_day_to_send = str(_date + timedelta(days=1))
        year_int_value = int(_date.strftime('%Y'))
        day_int_value = [int(_date.strftime('%j'))]
        next_day = self.next_day(year_int_value, day_int_value)
        charged_model = pickle.load(open("./lab5_model.sav", 'rb'))
        normalized_pred_value = charged_model.predict([next_day])
        temp_pred_value = normalized_pred_value[0] * \
            (self.data_temp_max - self.data_temp_min) + self.data_temp_min
        self.write_db('predicted_values',
                      "current_temperature", _temperature)
        self.write_db('predicted_values',
                      "predicted_temperature", temp_pred_value)
        self.write_db('predicted_values', "current_day", current_day_to_send)
        self.write_db('predicted_values', "next_day", next_day_to_send)

    def next_day(self, current_year, current_day):
        next_value = 0
        if current_year % 4 == 0 and (current_year % 100 != 0 or current_year % 400 == 0):
            if current_day[0] == 366:
                next_value = [1]
            else:
                next_value = [current_day[0] + 1]
        else:
            if current_day[0] == 365:
                next_value = [1]
            else:
                next_value = [current_day[0] + 1]
        return next_value

    def take_measurement(self, _message):
        print("message: ", _message, flush=True)
        array_split = _message.split(' ')
        timestamp_value = float(array_split[-1])/1000000000
        datetime_value = datetime.fromtimestamp(timestamp_value)
        date_value = datetime_value.date()
        temperature_value = float(array_split[1].split('=')[-1])
        print("Date: ", date_value, flush=True)
        self.temperature_predictor(date_value, temperature_value)


if __name__ == '__main__':

    analytics = Analytics()

    def callback(ch, method, properties, body):
        global analytics
        #print(" [x] Received %r" % body)
        message = body.decode("utf-8")
        #print("message from rabbit: {}".format(message), flush=True)
        analytics.take_measurement(message)

    url = os.environ.get('AMQP_URL', 'amqp://guest:guest@rabbit:5672/%2f')
    params = pika.URLParameters(url)
    connection = pika.BlockingConnection(params)

    channel = connection.channel()
    channel.queue_declare(queue='messages')
    channel.queue_bind(exchange='amq.topic', queue='messages', routing_key='#')
    channel.basic_consume(
        queue='messages', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()
