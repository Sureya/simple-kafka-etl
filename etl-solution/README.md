### Simple Kafka based ETL Job

### What does this application do ?

This is a very simple ETL application which has two parts to it 

- **Extractor** , A Sanic app which receives HTTP request and validates input record's schema, then publishes it to Kafka topic as s message. 
 
- **Processor**, A simple Python application which polls the Kafka queue for new records and persists the data in the Postgres database.
  
  
### Tech Stack 
- **Python3.7** for programming language
- **Kafka** for queueing
    - To keep things simple I have used free Kafka setup from [cloudkarafka](https://www.cloudkarafka.com/)
- **pip** for dependency managment
- **Sanic** Async web-api
- **uvicorn** execute and distribute  async Sanic app
- **docker** for containersing the application 
- **docker-compose** for orchestrating service dependency
- **Makefile** for easy one step execution.


### Repository structure
This application is structured as follows 

```bash
.
├── Makefile
├── README.md
├── docker-compose.yml
├── envs
│   ├── datatbase.env
│   └── kafka.env
├── extractor
│   ├── Dockerfile
│   ├── extract.py
│   ├── extractor_schema.json
│   ├── requirements.txt
│   └── test_extractor.py
└── processor
    ├── Dockerfile
    ├── ddl.sql
    ├── processor.py
    └── requirements.txt

```

- **envs**: folder containing all the ENV varaibles
    - instead of editing docker-compose everytime we want to change the values, we can edit this file
    - I am painfully aware that sharing secrets in the `PLAINTEXT` format is not secure, but for the simplicity of execution I have decided to do it this way. 
  
- **extractor**: folder containing code for extractor module
    - **_extract.py_** : Sanic app 
    - **_extractor_schema.py_** : Schema used for JSON validation
    - **_requirements.txt_** : module dependencies
    - **_test_extractor.py_** : simple test cases for sanic app

- **processor**: folder containing code for processor module
    - **_processor.py_** : Python application to load transformed data into database. 
    - **_ddl.sql_** : SQL Schema used for creating relational tables in PSQL.
    - **_requirements.txt_** : module dependencies


### End to End process flows 
- An API endpoints receives HTTP request 
    - Once an input is received the schema is validated
    - If the schema is valid, we publish the message to Kafka & return success status

- Python Kafka Consumer
    - When the program begins it will make sure the relational table exists
    - After that it will start consuming new messages, 
        - For each JSON message received, it will transform the data into below described structure
        
        - Once the data has been successfully transformed, it will be persisted in the PSQL database.       


#### Sample JSON record with valid schema
```json
{
    "vehicle": "Honda,CIVIC,2020",
    "fullname": "Tony Stark",
    "address": "10880 Malibu Point,90265,,Florida,USA",
    "time_of_accident": "04-25-2013 10:10:07",
    "total_cost": 1000,
    "currency": "USD",
    "estimate": [
        {
            "panel": "FRONT LEFT WING",
            "cost": 1000,
            "operation": "REPAIR"
        }
    ]

}
```
#### SQL table structure

```sql
CREATE TABLE IF NOT EXISTS review(
        "_id"                     TEXT    PRIMARY KEY
    ,   "brand"                   TEXT
    ,   "model"                   TEXT
    ,   "production_year"         INT
    ,   "policy_holder_name"      TEXT
    ,   "address"                 TEXT
    ,   "post_code"               TEXT
    ,   "state"                   TEXT
    ,   "city"                    TEXT
    ,   "country"                 TEXT
    ,   "currency"                VARCHAR(3)
    ,   "total_cost"              NUMERIC
    ,   "time_of_accident"        TIMESTAMP
    ,   "estimate"                JSONB
    ,   "raw"                     JSONB
);

CREATE INDEX IF NOT EXISTS car_mm_idx ON review (brand, model, production_year);
CREATE INDEX IF NOT EXISTS address_mm_idx ON review (country, state);
CREATE INDEX IF NOT EXISTS  currency_idx ON review (currency);
CREATE INDEX IF NOT EXISTS review_estimate_gin_idx ON review USING  gin (estimate jsonb_path_ops);

``` 


## How do I execute your code ?

#### ASSUMPTION 
- This step assumes that you have Docker installed in your local machine
- If you already have PSQL running in port 5432, this might throw error, please stop that service before proceeding further
- All the application uses JSON logging, if you are not used to it, may look a bit weird at the beginning.

```bash

# Step1 : Start the services
$ make execute 
# Yup! that's it, this will take few seconds to spin-up the services.
# You can know that all the services are up if you see a log message saying "DDL ensured"


# Step2: Once all services are up we can make the API call to verify using following command
curl --location --request POST 'http://127.0.0.1:9558/review' \
--header 'Content-Type: application/json' \
--data-raw '{
    "vehicle": "Honda,CIVIC,2020",
    "fullname": "Tony Stark",
    "address": "10880 Malibu Point,90265,,Florida,USA",
    "time_of_accident": "04-25-2013 10:10:07",
    "total_cost": 1000,
    "currency": "USD",
    "estimate": [
        {
            "panel": "FRONT LEFT WING",
            "cost": 1000,
            "operation": "REPAIR"
        }
    ]

}'

# Step3 : If you want to check with invalid input record use this call  
curl --location --request POST 'http://127.0.0.1:9558/review' \
--header 'Content-Type: application/json' \
--data-raw '{
    "vehicle": "Honda,CIVIC,2020",
    "fullname": "Tony Stark",
    "address": "10880 Malibu Point,90265,,Florida,USA",
    "time_of_accident": "04-25-2013 10:10:07",
    "currency": "USD",
    "estimate": [
        {
            "panel": "FRONT LEFT WING",
            "cost": 1000,
            "operation": "REPAIR"
        }
    ]

}'

# Step 4: If you want to check with invalid currency, use this call 
curl --location --request POST 'http://127.0.0.1:9558/review' \
--header 'Content-Type: application/json' \
--data-raw '{
    "vehicle": "Honda,CIVIC,2020",
    "fullname": "Tony Stark",
    "address": "10880 Malibu Point,90265,,Florida,USA",
    "time_of_accident": "04-25-2013 10:10:07",
    "total_cost": 1000,
    "currency": "SHREYA GHOSHAL",
    "estimate": [
        {
            "panel": "FRONT LEFT WING",
            "cost": 1000,
            "operation": "REPAIR"
        }
    ]

}'


# Step 5: The docker image PSQL is exposed in your local machine so you can connect to the database using following URI
#           postgresql://ketl:ketl@localhost:5432/ketl
# SYNTAX:   postgresql://[user_name]:[password]@[host]:5432/[database_name]

# Final step
# To cleanup any auxiliary files excute the following command
$ make cleanup  


```
 
