# Root Makefile for speculate project.

.DEFAULT_GOAL := default

.PHONY: default format cli

default: format cli

format:
	uvx flowmark --auto $(shell find . -name '*.md' -type f -not -path '*/.venv/*' -not -path '*/.*/*')

cli:
	$(MAKE) -C cli

