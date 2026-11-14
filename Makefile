# ==============================================================================
# Google Drive Direct Link & Streaming M3U Playlist Generator
# ==============================================================================

SHELL := /bin/bash
.DEFAULT_GOAL := help

# Virtual environment & Python configuration
VENV ?= .venv
VENV_BIN := $(VENV)/bin
PYTHON ?= $(if $(wildcard $(VENV_BIN)/python),$(VENV_BIN)/python,python3)
PIP ?= $(if $(wildcard $(VENV_BIN)/pip),$(VENV_BIN)/pip,$(PYTHON) -m pip)

# CLI Parameter definitions
URL ?=
ID ?=
FILE ?=
SRC ?= $(if $(FILE),$(FILE),)
PARENT ?=
DIR ?=
OUT ?=
METHOD ?=
TYPE ?=
CREDS ?=
ARGS ?=

# Support positional arguments (e.g. 'make upload ./file.txt' or 'make stream <url>')
ifeq ($(firstword $(MAKECMDGOALS)),upload)
  UPLOAD_POS_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval .PHONY: $(UPLOAD_POS_ARGS))
  %:
	@true
endif

ifeq ($(firstword $(MAKECMDGOALS)),download)
  DOWNLOAD_POS_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval .PHONY: $(DOWNLOAD_POS_ARGS))
  %:
	@true
endif

ifeq ($(firstword $(MAKECMDGOALS)),stream)
  STREAM_POS_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval .PHONY: $(STREAM_POS_ARGS))
  %:
	@true
endif

ifeq ($(firstword $(MAKECMDGOALS)),run)
  RUN_POS_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval .PHONY: $(RUN_POS_ARGS))
  %:
	@true
endif

.PHONY: help venv install install-cli install-all setup check-creds token run stream download upload list-folders clean clean-token clean-all

# ------------------------------------------------------------------------------
# Help Target
# ------------------------------------------------------------------------------
help:
	@echo "======================================================================"
	@echo " Google Drive Direct Link / Stream / Download / Upload - Makefile"
	@echo "======================================================================"
	@echo ""
	@echo "Environment & Setup:"
	@echo "  make venv                 Create Python virtual environment (.venv)"
	@echo "  make install              Install dependencies from requirements.txt"
	@echo "  make install-cli          Install dependencies from requirements-cli.txt"
	@echo "  make install-all          Install all dependencies"
	@echo "  make setup                Create venv and install all dependencies"
	@echo "  make check-creds          Check if credentials.json exists"
	@echo ""
	@echo "Authentication:"
	@echo "  make token                Generate or refresh Google Drive OAuth token"
	@echo ""
	@echo "Direct Links & M3U Playlist Generation:"
	@echo "  make run <url_or_id>      Generate direct link or M3U playlist"
	@echo "  make stream <url_or_id>   (alias for 'make run')"
	@echo "  (Also supports URL=<url_or_id>)"
	@echo ""
	@echo "Download & Upload:"
	@echo "  make download <id_or_url> [DIR=<dir>] [OUT=<file>] [METHOD=gdown|requests]"
	@echo "  make upload <file_or_dir> [PARENT=<parent_id>]"
	@echo "  (Also supports SRC=<file_or_dir> or FILE=<file_or_dir>)"
	@echo "  make list-folders         List folders in Google Drive root"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean                Remove generated playlists, downloads, and cache"
	@echo "  make clean-token          Remove token.pickle"
	@echo "  make clean-all            Remove cache, downloads, token, and .venv"
	@echo ""
	@echo "Examples:"
	@echo "  make upload ./file.txt"
	@echo "  make upload /workspaces/dd-fe/README.md"
	@echo "  make upload ./my_folder PARENT=1XYZabc"
	@echo "  make stream https://drive.google.com/file/d/1ABCxyz/view"
	@echo "  make stream https://drive.google.com/drive/folders/1XYZabc"
	@echo "  make download 1-file-id-here DIR=down_files"
	@echo "======================================================================"

# ------------------------------------------------------------------------------
# Environment & Dependencies
# ------------------------------------------------------------------------------
venv:
	@if [ ! -d "$(VENV)" ]; then \
	  echo "Creating virtual environment in $(VENV)..."; \
	  python3 -m venv $(VENV); \
	  echo "Virtual environment created. Run 'source $(VENV_BIN)/activate' to activate."; \
	else \
	  echo "Virtual environment already exists in $(VENV)."; \
	fi

install:
	@echo "Installing requirements from requirements.txt..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

install-cli:
	@echo "Installing CLI requirements from requirements-cli.txt..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-cli.txt

install-all: install install-cli

setup: venv install-all
	@echo "Setup complete!"

check-creds:
	@if [ ! -f "credentials.json" ]; then \
	  echo "❌ credentials.json is missing in project root."; \
	  echo "Please download credentials.json from Google Cloud Console."; \
	  exit 1; \
	else \
	  echo "✅ credentials.json found."; \
	fi

# ------------------------------------------------------------------------------
# Authentication
# ------------------------------------------------------------------------------
token: check-creds
	@echo "Running token generator..."
	$(PYTHON) generate_drive_token.py

# ------------------------------------------------------------------------------
# Direct Link & Stream Playlist Generation
# ------------------------------------------------------------------------------
STREAM_TARGET := $(if $(URL),$(URL),$(if $(ID),$(ID),$(if $(STREAM_POS_ARGS),$(STREAM_POS_ARGS),$(RUN_POS_ARGS))))

run: check-creds
	@if [ -z "$(strip $(STREAM_TARGET))" ]; then \
	  echo "❌ Error: Missing URL or ID."; \
	  echo "Usage: make run <Google-Drive-URL-or-ID>"; \
	  echo "   or: make stream <Google-Drive-URL-or-ID>"; \
	  echo "   or: make run URL=<Google-Drive-URL-or-ID>"; \
	  exit 1; \
	fi
	$(PYTHON) drive_stream_v2.py "$(STREAM_TARGET)"

stream: run

# ------------------------------------------------------------------------------
# Download & Upload
# ------------------------------------------------------------------------------
DL_TARGET := $(if $(ID),$(ID),$(if $(URL),$(URL),$(DOWNLOAD_POS_ARGS)))
DL_ARGS :=
ifneq ($(DIR),)
  DL_ARGS += -d "$(DIR)"
endif
ifneq ($(OUT),)
  DL_ARGS += -o "$(OUT)"
endif
ifneq ($(METHOD),)
  DL_ARGS += -m "$(METHOD)"
endif
ifneq ($(TYPE),)
  DL_ARGS += -t "$(TYPE)"
endif

download: check-creds
	@if [ -z "$(strip $(DL_TARGET))" ]; then \
	  echo "❌ Error: Missing ID or URL."; \
	  echo "Usage: make download <id_or_url> [DIR=<dir>] [OUT=<filename>]"; \
	  echo "   or: make download ID=<id_or_url> [DIR=<dir>] [OUT=<filename>]"; \
	  exit 1; \
	fi
	$(PYTHON) google_drive_downloader.py "$(DL_TARGET)" $(DL_ARGS)

UP_TARGET := $(if $(SRC),$(SRC),$(UPLOAD_POS_ARGS))
UP_ARGS :=
ifneq ($(PARENT),)
  UP_ARGS += --parent-id "$(PARENT)"
endif
ifneq ($(CREDS),)
  UP_ARGS += --creds "$(CREDS)"
endif
ifneq ($(ARGS),)
  UP_ARGS += $(ARGS)
endif

upload: check-creds
	@if [ -z "$(strip $(UP_TARGET))" ]; then \
	  echo "❌ Error: Missing source path."; \
	  echo "Usage: make upload <file_or_directory_path> [PARENT=<parent_folder_id>]"; \
	  echo "   or: make upload SRC=<file_or_directory_path> [PARENT=<parent_folder_id>]"; \
	  exit 1; \
	fi
	$(PYTHON) google_drive_uploader.py $(if $(SRC),"$(SRC)","$(UPLOAD_POS_ARGS)") $(UP_ARGS)

list-folders: check-creds
	$(PYTHON) google_drive_uploader.py --list $(if $(CREDS),--creds "$(CREDS)",)

# ------------------------------------------------------------------------------
# Cleanup
# ------------------------------------------------------------------------------
clean:
	@echo "Cleaning temporary files and cache..."
	rm -rf v_link down_files __pycache__ *.pyc *.pyo .pytest_cache
	@echo "Clean completed."

clean-token:
	@echo "Removing OAuth token..."
	rm -f token.pickle
	@echo "token.pickle removed."

clean-all: clean clean-token
	@echo "Removing virtual environment..."
	rm -rf $(VENV)
	@echo "Clean all completed."
