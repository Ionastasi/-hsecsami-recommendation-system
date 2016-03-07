NAME = crawler/crawler.py

all: prepare

prepare:
	mkdir -p data/html/.inde
	mkdir -p data/text
	touch data/html/.index
	touch data/text/.index

clean:
	rm -rf crawler/__pycache__
	rm -rf data
