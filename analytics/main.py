import pika
import os
import math
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

DAY_100K = 100000
DAY_5k = 5000

class Analytics():
    max_value = -math.inf
    min_value = math.inf
    influx_bucket = 'rabbit'
    influx_token = 'token-secret'
    influx_url = 'http://influxDB:8086'
    influx_org = 'org'
    step_count = 0
    step_sum = 0
    days_100k = 0
    days_5k = 0
    prev_value = 0
    days_consecutive = 0

    def write_db(self, tag, key, value):
        client= InfluxDBClient(url=self.influx_url, token=self.influx_token, org=self.influx_org)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        point = Point('Analytics').tag("Descriptive", tag).field(key, value)
        write_api.write(bucket=self.influx_bucket, record=point)

    def add_max_value(self, _measurement):
        if _measurement > self.max_value:
            #print("New max", flush=True)
            self.max_value = _measurement
        self.write_db('steps', "Maximum", self.max_value)
    
    def add_min_value(self, _measurement):
        if _measurement < self.min_value:
            #print("New min", flush=True)
            self.min_value = _measurement
        self.write_db('steps', "Minumum", self.min_value)

    def get_mean(self, _measurement):
        self.step_count += 1
        self.step_sum += _measurement
        mean = self.step_sum/self.step_count
        print("mean {}".format(mean), flush=True)
        self.write_db('steps', "mean", mean)

    def get_days_100k(self, _measurement):
        if _measurement >= 100000:
            self.days_100k += 1
            print("days_100k {}".format(self.days_100k), flush=True)
        self.write_db('steps', "days_100k", self.days_100k)

    def get_days_5k(self, _measurement):
        if _measurement <= 50000:
            self.days_5k += 1
            print("days_5k {}".format(self.days_5k), flush=True)
        self.write_db('steps', "days_5k", self.days_5k)

    def get_consecutive_days(self, _measurement):
        if _measurement >= self.prev_value:
            self.days_consecutive += 1
        else:
            self.days_consecutive = 0
        print("days_consecutive {}".format(self.days_consecutive), flush=True)
        self.prev_value = _measurement
        self.write_db('steps', "days_consecutive", self.days_consecutive)
    

    
    def take_measurement(self, _message):
        message = _message.split("=")
        measurement = float(message[-1])
        print("measurement {}".format(measurement), flush=True)
        self.add_max_value(measurement)
        self.add_min_value(measurement)
        self.get_mean(measurement)
        self.get_days_100k(measurement)
        self.get_days_5k(measurement)
        self.get_consecutive_days(measurement)
        
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
  channel.basic_consume(queue='messages', on_message_callback=callback, auto_ack=True)
  channel.start_consuming()