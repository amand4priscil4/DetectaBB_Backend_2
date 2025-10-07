#!/usr/bin/env bash
# exit on error
set -o errexit

# Executando os comandos diretamente, sem sudo
apt-get update
apt-get install -y tesseract-ocr poppler-utils

# Instala as dependências do Python
pip install -r requirements.txt