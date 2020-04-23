.PHONY: execute cleanup
.ONESHELL:

export BASE_PATH ?= $(shell pwd)

execute:
	docker-compose stop && docker-compose build && docker-compose up

cleanup:
	docker-compose stop
	rm -rf db
	rm -rf extractor/__pycache__
	rm -rf processor/__pycache__

