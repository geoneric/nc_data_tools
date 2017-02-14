import json
import os.path
import sys
import traceback
from flask import Config
import pika
import requests
from .configuration import configuration
from .data_tools import *


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
            plan_uri = data["uri"]
            workspace_name = data["workspace"]
            response = requests.get(plan_uri)

            assert response.status_code == 200, response.text

            plan = response.json()["plan"]
            pathname = plan["pathname"]
            status = plan["status"]
            skip_registration = False


            if status != "uploaded":
                sys.stderr.write("Skipping plan because 'status' is not "
                    "'uploaded', but '{}'".format(status))
                sys.stderr.flush()
                skip_registration = True


            if not skip_registration:

                assert status == "uploaded", status

                layer_name = register_raster(
                    pathname,
                    workspace_name,
                    geoserver_uri=self.config["NC_GEOSERVER_URI"],
                    geoserver_user=self.config["NC_GEOSERVER_USER"],
                    geoserver_password=self.config["NC_GEOSERVER_PASSWORD"])

                # Mark plan as 'registered'.
                payload = {
                    "layer_name": layer_name,
                    "status": "registered"
                }
                response = requests.patch(plan_uri, json=payload)

                assert response.status_code == 200, response.text


        except Exception as exception:

            sys.stderr.write("{}\n".format(traceback.format_exc()))
            sys.stderr.flush()


        channel.basic_ack(delivery_tag=method_frame.delivery_tag)


    def on_georeference_raster(self,
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
            plan_uri = data["uri"]
            response = requests.get(plan_uri)

            assert response.status_code == 200, response.text

            plan = response.json()["plan"]

            # TODO The pathname points to the plan originally uploaded
            #      by the client. This should be the plan which is
            #      registered with geoserver.
            # pathname = plan["pathname"]
            pathname = "{}.tif".format(os.path.splitext(plan["pathname"])[0])
            assert os.path.exists(pathname), pathname

            workspace_name = plan["user"]

            layer_name = plan["layer_name"]
            status = plan["status"]
            skip_georeference = False


            if status != "registered":
                sys.stderr.write("Skipping plan because 'status' is not "
                    "'registered', but '{}'".format(status))
                sys.stderr.flush()
                skip_georeference = True


            if not skip_georeference:

                assert status == "registered", status

                gcps = data["gcps"]
                georeference_raster(
                    pathname,
                    gcps,
                    geoserver_uri=self.config["NC_GEOSERVER_URI"],
                    geoserver_user=self.config["NC_GEOSERVER_USER"],
                    geoserver_password=self.config["NC_GEOSERVER_PASSWORD"],
                    workspace_name=workspace_name,
                    layer_name=layer_name)

                # Mark plan as 'georeferenced'.
                payload = {
                    "status": "georeferenced"
                }
                response = requests.patch(plan_uri, json=payload)

                assert response.status_code == 200, response.text


        except Exception as exception:

            sys.stderr.write("{}\n".format(traceback.format_exc()))
            sys.stderr.flush()


        channel.basic_ack(delivery_tag=method_frame.delivery_tag)


    def on_retrieve_colors_of_raster(self,
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
            plan_uri = data["uri"]
            response = requests.get(plan_uri)

            assert response.status_code == 200, response.text

            plan = response.json()["plan"]

            # TODO The pathname points to the plan originally uploaded
            #      by the client. This should be the plan which is
            #      registered with geoserver.
            pathname = "{}.tif".format(os.path.splitext(plan["pathname"])[0])
            assert os.path.exists(pathname), pathname

            workspace_name = plan["user"]
            layer_name = plan["layer_name"]
            status = plan["status"]
            skip_retrieve_colors = False


            if status != "georeferenced":
                sys.stderr.write("Skipping plan because 'status' is not "
                    "'georeferenced', but '{}'".format(status))
                sys.stderr.flush()
                skip_retrieve_colors = True


            if not skip_retrieve_colors:

                assert status == "georeferenced", status

                client_id = data["client_id"]
                colors = retrieve_colors(pathname)
                notify_uri = self.config["NC_CLIENT_NOTIFIER_URI"]
                payload = {
                    "client_id": client_id,
                    "result": {
                        "colors": colors
                    }
                }

                response = requests.post(notify_uri, json=payload)
                assert response.status_code == 201, response.text


        except Exception as exception:

            sys.stderr.write("{}\n".format(traceback.format_exc()))
            sys.stderr.flush()


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
            queue="retrieve_colors_of_raster",
            durable=True)
        self.channel.basic_consume(
            self.on_retrieve_colors_of_raster,
            queue="retrieve_colors_of_raster")

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
