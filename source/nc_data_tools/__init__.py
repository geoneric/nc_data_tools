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

            result = register_raster(pathname,
                # TODO Turn these into config variables.
                geoserver_uri="http://geoserver:8080/geoserver",
                geoserver_user="admin",
                geoserver_password="geoserver")

            # TODO Handle result

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


    ### def on_message(self,
    ###         channel,
    ###         method_frame,
    ###         header_frame,
    ###         body):

    ###     # Message passed in is the uri to the query to execute.

    ###     sys.stdout.write("received message: {}\n".format(body))
    ###     sys.stdout.flush()

    ###     try:
    ###         # Get the query.
    ###         uri = body
    ###         response = requests.get(uri)

    ###         assert response.status_code == 200, response.text

    ###         query = response.json()["aggregate_query"]

    ###         assert query["edit_status"] == "final", query["edit_status"]
    ###         assert query["execute_status"] == "queued", query["execute_status"]

    ###         # Mark executing query as 'executing'.
    ###         payload = {
    ###             "execute_status": "executing"
    ###         }
    ###         response = requests.patch(uri, json=payload)

    ###         assert response.status_code == 200, response.text

    ###         query = response.json()["aggregate_query"]


    ###         # Pathname of file to store result in.
    ###         result_pathname = self.result_dataset_pathname(query)
    ###         sys.stdout.write("output dataset: {}\n".format(result_pathname));
    ###         sys.stdout.flush()


    ###         # Calculate the result.
    ###         # TODO
    ###         time.sleep(5)
    ###         open(result_pathname, "w").write(
    ###             "head1, head2, head3\n"
    ###             "1, 2, 3\n"
    ###             "4, 5, 6\n"
    ###             "7, 8, 9\n"
    ###         )


    ###         # Store information about the result in emis_result.
    ###         results_uri = self.aggregate_queries_uri("aggregate_query_results")
    ###         payload = {
    ###             "id": query["id"],
    ###             "uri": self.relative_result_dataset_pathname(query)
    ###                 # self.emis_aggregate_query_results_uri(
    ###                 # self.relative_result_dataset_pathname(query))
    ###         }

    ###         response = requests.post(results_uri,
    ###             json={"aggregate_query_result": payload})

    ###         assert response.status_code == 201, response.text


    ###         # Mark executing query as 'succeeded'.
    ###         payload = {
    ###             "execute_status": "succeeded"
    ###         }
    ###         response = requests.patch(uri, json=payload)

    ###         assert response.status_code == 200, response.text

    ###     except Exception as exception:

    ###         sys.stderr.write("{}\n".format(traceback.format_exc(exception)));
    ###         sys.stderr.flush()

    ###         # Mark executing query as 'failed'.
    ###         payload = {
    ###             "execute_status": "failed"
    ###         }
    ###         response = requests.patch(uri, json=payload)

    ###         assert response.status_code == 200, response.text


    ###     channel.basic_ack(delivery_tag=method_frame.delivery_tag)


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
