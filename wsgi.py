# wsgi.py
import sys
import os

# Adicionar o diretório do projeto ao path
project_home = '/home/amand4priscil4/Detector-boletos'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Carregar variáveis de ambiente
from dotenv import load_dotenv
project_folder = os.path.expanduser(project_home)
load_dotenv(os.path.join(project_folder, '.env'))

# Importar a aplicação Flask
from app import create_app
application = create_app()
