#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Instala as dependências do sistema com permissão de administrador
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils

# 2. Instala as dependências do Python
pip install -r requirements.txt