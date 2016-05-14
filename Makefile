all: prepare

prepare:
	mkdir -p data/html
	mkdir -p data/text
	touch data/html/.index
	touch data/text/.index

clean:
	rm -rf source/__pycache__
	rm -rf data
