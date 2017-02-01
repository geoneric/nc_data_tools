import json
import sys
import traceback
from flask import Config
import pika
from .configuration import configuration
from .data_tools import register_raster


class DataTools(object):

    def __init__(self):
        self.config = Config(__name__)


    def on_register_raster(self,
            channel,
            method_frame,
            header_frame,
            body):

        sys.stdout.write("received message: {}\n".format(body))
        sys.stdout.flush()

        try:

            body = body.decode("utf-8")
            sys.stdout.write("{}\n".format(body))
            sys.stdout.flush()
            data = json.loads(body)
            pathname = data["pathname"]
            workspace_name = data["workspace"]

            register_raster(
                pathname,
                workspace_name,
                geoserver_uri=self.config["NC_GEOSERVER_URI"],
                geoserver_user=self.config["NC_GEOSERVER_USER"],
                geoserver_password=self.config["NC_GEOSERVER_PASSWORD"])

        except Exception as exception:

            sys.stderr.write("{}\n".format(traceback.format_exc()))
            sys.stderr.flush()

            # TODO Handle error

            ### # Mark execution as 'failed'.
            ### payload = {
            ###     "execute_status": "failed"
            ### }
            ### response = requests.patch(uri, json=payload)

            ### assert response.status_code == 200, response.text


        channel.basic_ack(delivery_tag=method_frame.delivery_tag)


    def on_georeference_raster(self,
            channel,
            method_frame,
            header_frame,
            body):

        sys.stdout.write("received message: {}\n".format(body))
        sys.stdout.flush()


        # TODO georeference raster


        channel.basic_ack(delivery_tag=method_frame.delivery_tag)


    def on_reclassify_raster(self,
            channel,
            method_frame,
            header_frame,
            body):

        sys.stdout.write("received message: {}\n".format(body))
        sys.stdout.flush()


        # TODO reclassify raster


        channel.basic_ack(delivery_tag=method_frame.delivery_tag)


    def run(self,
            host):

        self.credentials = pika.PlainCredentials(
            self.config["NC_RABBITMQ_DEFAULT_USER"],
            self.config["NC_RABBITMQ_DEFAULT_PASS"]
        )
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            host="rabbitmq",
            virtual_host=self.config["NC_RABBITMQ_DEFAULT_VHOST"],
            credentials=self.credentials,
            # Keep trying for 8 minutes.
            connection_attempts=100,
            retry_delay=5  # Seconds
        ))
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)

        self.channel.queue_declare(
            queue="register_raster",
            durable=True)
        self.channel.basic_consume(
            self.on_register_raster,
            queue="register_raster")

        self.channel.queue_declare(
            queue="georeference_raster",
            durable=True)
        self.channel.basic_consume(
            self.on_georeference_raster,
            queue="georeference_raster")

        self.channel.queue_declare(
            queue="reclassify_raster",
            durable=True)
        self.channel.basic_consume(
            self.on_reclassify_raster,
            queue="reclassify_raster")

        try:
            sys.stdout.write("Start consuming...\n")
            sys.stdout.flush()
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()

        sys.stdout.write("Close connection...\n")
        sys.stdout.flush()
        self.connection.close()


def create_app(
        configuration_name):

    app = DataTools()

    configuration_ = configuration[configuration_name]
    app.config.from_object(configuration_)
    configuration_.init_app(app)

    return app
