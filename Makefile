# Paraná Rural Access Equity — Makefile
# Convenience commands for the end-to-end pipeline.

PY ?= python
VENV ?= .venv

.PHONY: help
help:
	@echo "Paraná Rural Access Equity — targets:"
	@echo "  make install    Create venv and install requirements"
	@echo "  make data       Download raw datasets into data/raw/"
	@echo "  make process    Clean, join, and score (produces data/processed/)"
	@echo "  make render     Produce PNG choropleth + interactive HTML in output/"
	@echo "  make all        install + data + process + render"
	@echo "  make notebook   Launch Jupyter Lab"
	@echo "  make clean      Remove processed data and outputs (keeps raw)"
	@echo "  make wipe       Remove EVERYTHING under data/ and output/"

.PHONY: install
install:
	$(PY) -m venv $(VENV)
	$(VENV)/Scripts/pip install --upgrade pip
	$(VENV)/Scripts/pip install -r requirements.txt

.PHONY: data
data:
	$(PY) -m src.download_all

.PHONY: process
process:
	$(PY) -m src.compute_scores

.PHONY: render
render:
	$(PY) -m src.render_outputs

.PHONY: all
all: install data process render

.PHONY: notebook
notebook:
	jupyter lab notebooks/

.PHONY: clean
clean:
	rm -rf data/processed/* output/*.png output/*.html output/*.csv output/figures

.PHONY: wipe
wipe:
	rm -rf data/raw/* data/processed/* output/*
