import pika
import os
import math
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

class Analytics():
    max_value = -math.inf
    min_value = math.inf
    influx_bucket = 'bucket'
    influx_token = 'token_influx'
    influx_url = 'token_influx'
    influx_org = 'token_influx'

    def add_max_value(self, _measurement):
        if _measurement > self.max_value:
            print("New max", flush=True)
            self.max_value = _measurement
            self.write_db('temperature', "Maximum", _measurement)
    
    def add_min_value(self, _measurement):
        if _measurement < self.min_value:
            print("New min", flush=True)
            self.min_value = _measurement
            self.write_db('temperature', "Minumum", _measurement)
    
    def take_measurement(self, _message):
        message = _message.split("=")
        measurement = float(message[-1])
        print("measurement {}".format(measurement))
        self.add_max_value(measurement)
        self.add_min_value(measurement)

    def write_db(self, tag, key, value):
        client= InfluxDBClient(url=self.influx_url, token=self.influx_token, org=self.influx_org)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        point = Point('Analytics').tag("Descriptive", tag).field(key, value)
        write_api.write(bucket=self.influx_bucket, record=point)
        
        


if __name__ == '__main__':
    analytics = Analytics()
    url = os.environ.get('AMQP_URL', 'amqp://guest:guest@rabbit:5672/%2f')
    params = pika.ConnectionParameters(host=url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue='messages')
    channel.queue_bind(exchangee='amq.topic', queue='messages', routing_key='#')


    def callback(ch, method, properties, body):
        global analytics
        print(" [x] Recived %r" % body)
        message = body.decode("utf-8")
        print("message {}".format(message, flush=True))
        analytics.take_measurement(message)
    
    channel.basic_consume(queue='messages', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()