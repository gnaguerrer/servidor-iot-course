import pika
import os
import math
import pickle
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


class Analytics():
    max_value = -math.inf
    min_value = math.inf
    influx_bucket = 'rabbit'
    influx_token = 'token-secret'
    influx_url = 'http://influxDB:8086'
    influx_org = 'org'
    clases = ["setosa", "versicolor", "virginica"]
    valores = [0, 0, 0]

    def write_db(self, tag, key, value):
        client = InfluxDBClient(url=self.influx_url,
                                token=self.influx_token, org=self.influx_org)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        point = Point('Analytics').tag("Descriptive", tag).field(key, value)
        write_api.write(bucket=self.influx_bucket, record=point)

    def flower_classifier(self, _measurement):
        print("Dato en flower_classifier: {}".format(_measurement), flush=True)
        charged_model = pickle.load(open("./lab4_model.sav", 'rb'))
        class_predict = int(charged_model.predict([_measurement]))
        self.valores[class_predict] += 1
        self.write_db(
            'class', self.clases[class_predict], self.valores[class_predict])

    def take_measurement(self, _message):
        data = []
        print("message: ", _message)
        message = _message.split(" ")
        message = message[-1].split(",")
        for item in message:
            value = item.split("=")[1]
            data.append(float(value))
        #measurement = float(message[-1])
        #print("measurement {}".format(measurement), flush=True)
        self.flower_classifier(data)


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
