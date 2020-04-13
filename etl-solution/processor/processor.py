"""
Author: Sureya Sathiamoorthi
"""

# in-built
from json import loads, dumps
from sys import stdout
from os import environ
import logging

# 3rd party
from confluent_kafka import Consumer
from psycopg2 import connect
import json_logging
from retry import retry


# log is initialized without a web framework name
json_logging.ENABLE_JSON_LOGGING = True

json_logging.init_non_web()
logger = logging.getLogger("processor-app")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(stdout))


class Database:
    @staticmethod
    @retry(Exception, tries=3, delay=15)
    def connect(config):
        connection = connect(config["uri"])
        return connection

    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = self.connect(self.db_config)
        logger.info("Database initialised")
        self.cursor = self.connection.cursor()
        self._ensure_ddl()
        logger.info("DDL ensured")

    def _ensure_ddl(self) -> None:
        """
            When called reads the DDL script and executes the DDL in the DB.
        :return: None
        """
        with open("ddl.sql", "r") as f:
            query = f.read()
            self.cursor.execute(query)
        self.connection.commit()

    def persist(self, record: tuple) -> bool:
        """
            Given a input record, executes the insert statement in the DB.
        :param record: input record ->  tuple
        :return: None
        """
        sql = f"""insert into review(_id, brand, model, production_year,
        policy_holder_name, address, post_code, state, city, country, currency,
        total_cost, time_of_accident, estimate, raw) VALUES {record}"""

        self.cursor.execute(sql)
        self.connection.commit()
        logger.info("input record persisted")


class DataProcessor(Database):
    __slots__ = ('hosts', 'topics', 'conf', 'consumer', 'db_config',
                 'connection')

    @staticmethod
    def _extract_columns(record):
        """
            Given a DICT object, extracts all the column values from the
            input record and returns them in the same order as expected by the
            insert query.

        :param record: dict object of the Kafka message
        :return: tuple record
        """
        brand, model, production_year = list(
            map(lambda x: x.strip().lower(), record['vehicle'].split(',')))

        policy_holder_name = record['fullname']
        address, post_code, state, city, country = list(
            map(lambda x: x.strip().lower(), record['address'].split(',')))

        currency = record['currency']
        total_cost = record['total_cost']
        time_of_accident = record['time_of_accident']

        _id = record['_id']

        estimate = dumps(record['estimate'])
        raw = dumps(record)

        parsed_record = (_id, brand, model, production_year,
                         policy_holder_name, address, post_code, state, city,
                         country, currency, total_cost, time_of_accident,
                         estimate, raw)

        logger.info("Extracted relational column from JSON data")
        return parsed_record

    def __init__(self, db_config):

        super().__init__(db_config)

        self.hosts = environ["KAFKA_HOST"]

        topics = environ["KAFKA_TOPIC"].split(",")

        conf = {
            'bootstrap.servers': self.hosts,
            'session.timeout.ms': 6000,
            'group.id': "ketl-random-group-id",
            'default.topic.config': {'auto.offset.reset': 'smallest'},
            'security.protocol': 'SASL_SSL',
            'sasl.mechanisms': 'SCRAM-SHA-256',
            'sasl.username': environ["KAFKA_USERNAME"],
            'sasl.password': environ["KAFKA_PASSWORD"]
        }

        self.consumer = Consumer(**conf)
        self.consumer.subscribe(topics)

    def begin(self):
        """
            When called starts listening to the Kafka topic defined.
            For each message received, the data is persisted in the DB.

            This is a long running job, so the only way to manually stop it is
            with Keyboard Interrupt

        :return: None
        """
        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                else:
                    # Proper message
                    data = loads(msg.value())
                    logger.info(f"Parsed {data}")
                    parsed = self._extract_columns(record=data)
                    super().persist(record=parsed)

            self.consumer.close()
        except KeyboardInterrupt:
            self.consumer.close()
            raise KeyboardInterrupt('User Interrupted')


if __name__ == '__main__':
    uri = f"postgresql://{environ['POSTGRES_USER']}:" \
          f"{environ['POSTGRES_PASSWORD']}@psql_service/" \
          f"{environ['POSTGRES_DB']}?connect_timeout=10"

    db_configuration = {"uri": uri}
    logger.info(db_configuration)
    process = DataProcessor(db_config=db_configuration)
    process.begin()
