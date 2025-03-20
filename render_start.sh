#!/bin/bash
apt-get update && apt-get install -y poppler-utils
gunicorn pyworks_scripts.app:app
