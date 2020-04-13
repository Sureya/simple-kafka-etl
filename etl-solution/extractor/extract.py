"""
Author: Sureya Sathiamoorthi
"""
# in-built
from json import load, dumps
import traceback
import logging
from sys import stdout
from os import environ
from uuid import uuid4

# 3rd party
import json_logging
from sanic import Sanic
from jsonschema import validate
from confluent_kafka import Producer
from sanic_envconfig import EnvConfig
from money.currency import Currency
from sanic_restful_api import Api, Resource
from jsonschema.exceptions import ValidationError


class Config(EnvConfig):
    SCHEMA = load(open('extractor_schema.json', 'r'))
    ALL_CURRENCIES = [x for x in dir(Currency) if len(str(x)) == 3]
    HOSTS = environ["KAFKA_HOST"]
    TOPIC = environ["KAFKA_TOPIC"]

    CONF = {
        'bootstrap.servers': HOSTS,
        'session.timeout.ms': 6000,
        'default.topic.config': {'auto.offset.reset': 'smallest'},
        'security.protocol': 'SASL_SSL',
        'sasl.mechanisms': 'SCRAM-SHA-256',
        'sasl.username': environ["KAFKA_USERNAME"],
        'sasl.password': environ["KAFKA_PASSWORD"]
    }

    PRODUCER = Producer(**CONF)


app = Sanic(__name__)
app.config.from_object(Config)
api = Api(app)

# JSON logging configuration
json_logging.ENABLE_JSON_LOGGING = True
json_logging.CREATE_CORRELATION_ID_IF_NOT_EXISTS = True
json_logging.init_sanic()
json_logging.init_request_instrument(app)
logger = logging.getLogger("extractor-app")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(stdout))

logger.info(f"Publishing to topic {app.config.TOPIC}")


class ParseData(Resource):
    async def post(self, request):
        """
        ASYNC post method which will evaluate the input JSON schema and if the
        schema is valid, will produce the message to KAFKA TOPIC.

        :param request: Input Request
        :return: dict with status and message
        """
        input_record = request.json
        try:
            logger.debug("Validating the input record")
            validate(instance=input_record, schema=app.config.SCHEMA)
            logger.info("Input Record has been successfully Validated")

            if input_record["currency"] in app.config.ALL_CURRENCIES:
                logger.info("Everything looks great, queuing record for "
                            "persistence")
                input_record['_id'] = uuid4().hex
                app.config.PRODUCER.produce(app.config.TOPIC,
                                            dumps(input_record))
                logger.debug("record published")
                app.config.PRODUCER.flush()

                return {"status": 200, "message": "Record persisted"}, 200

            else:
                return {"status": 400,
                        "error": "invalid currency code found"}, 400

        except ValidationError:
            logger.error("Invalid Currency found in the record")
            return {"status": 400, "error": traceback.format_exc()}, 400


api.add_resource(ParseData, '/review')
