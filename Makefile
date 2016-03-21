NAME = crawler/crawler.py

all: prepare

prepare:
	mkdir -p data/html
	mkdir -p data/text

clean:
	rm -rf crawler/__pycache__
	rm -rf data
