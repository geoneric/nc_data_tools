import os


class Configuration:

    NC_RABBITMQ_DEFAULT_USER = os.environ.get("NC_RABBITMQ_DEFAULT_USER")
    NC_RABBITMQ_DEFAULT_PASS = os.environ.get("NC_RABBITMQ_DEFAULT_PASS")
    NC_RABBITMQ_DEFAULT_VHOST = os.environ.get("NC_RABBITMQ_DEFAULT_VHOST")

    NC_GEOSERVER_URI = os.environ.get("NC_GEOSERVER_URI")
    NC_GEOSERVER_USER = os.environ.get("NC_GEOSERVER_USER")
    NC_GEOSERVER_PASSWORD = os.environ.get("NC_GEOSERVER_PASSWORD")

    NC_CLIENT_NOTIFIER_URI = os.environ.get("NC_CLIENT_NOTIFIER_URI")


    @staticmethod
    def init_app(
            app):
        pass


class DevelopmentConfiguration(Configuration):

    pass


class TestingConfiguration(Configuration):

    pass


class ProductionConfiguration(Configuration):

    pass


configuration = {
    "development": DevelopmentConfiguration,
    "testing": TestingConfiguration,
    "production": ProductionConfiguration
}
