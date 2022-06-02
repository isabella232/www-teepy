API_PORT ?= 5000
HOST ?= 0.0.0.0

export PROJECT_NAME = teepy
export FLASK_APP = $(PWD)/$(PROJECT_NAME).py
export FLASK_ENV ?= development
# export FLASK_DEBUG=0
# export BACKOFFICE_CONFIG ?= $(PWD)/www-teepy.cfg

# Python env
PYTHON_ONLY = 1
VENV = $(PWD)/.env
PYTHON = python3.8
PYTHON_SRCDIR = $(PWD)

URL_PROD = https://www.lagestiondutierspayant.fr
