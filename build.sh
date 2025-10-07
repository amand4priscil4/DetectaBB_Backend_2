#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Instala as dependências do sistema (Tesseract)
apt-get update
apt-get install -y tesseract-ocr

# 2. Instala as dependências do Python
pip install -r requirements.txt