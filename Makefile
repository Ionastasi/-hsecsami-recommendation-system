all: prepare

prepare:
	mkdir -p data/html
	mkdir -p data/text

clean:
	rm -rf source/__pycache__
	rm -rf data
