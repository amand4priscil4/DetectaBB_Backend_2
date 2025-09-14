import requests
import json

url = "http://localhost:5000/api/analyze"
dados = {
    "banco": "Banco do Brasil",
    "codigo_banco": 1,
    "agencia": 1234,
    "valor": 1000.50,
    "linha_digitavel": "00190000090012345678901234567890"
}

response = requests.post(url, json=dados)
print("Status:", response.status_code)
print("Resposta:", response.json())