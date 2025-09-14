# Testes do Sistema Detecta Boletos

Este diretório contém todos os testes para validar as funcionalidades do sistema de detecção de boletos.

## Estrutura dos Testes

```
tests/
├── test_auth_basic.py          # Autenticação básica
├── test_auth_security.py       # Validação de senhas
├── test_security_complete.py   # Segurança completa
├── test_rate_limiting.py       # Rate limiting
├── test_upload.py              # Upload de arquivos
├── test_upload_auth.py         # Upload com autenticação
├── test_ocr.py                 # OCR e processamento
├── test_api_basic.py           # API básica
└── README.md
```

## Executar Testes

### Pré-requisitos

Certifique-se de que o servidor está rodando:
```bash
python main.py
```

### Testes Básicos

```bash
# API básica (análise manual)
python tests/test_api_basic.py

# Autenticação básica
python tests/test_auth_basic.py

# Verificar OCR
python tests/test_ocr.py
```

### Testes de Segurança

```bash
# Validação de senhas e emails
python tests/test_auth_security.py

# Teste completo de segurança
python tests/test_security_complete.py

# Rate limiting por endpoint
python tests/test_rate_limiting.py
```

### Testes de Upload

```bash
# Upload básico de arquivos
python tests/test_upload.py

# Upload com autenticação
python tests/test_upload_auth.py
```

## Descrição Detalhada dos Testes

### test_api_basic.py
**Funcionalidade:** Testa API básica com dados manuais
```python
# O que testa:
- Endpoint /api/health
- Endpoint /api/stats  
- Endpoint /api/analyze (dados manuais)
- Endpoint /api/history
- Validação de resposta JSON
- Predições do modelo ML
```

### test_auth_basic.py
**Funcionalidade:** Autenticação e autorização básica
```python
# O que testa:
- Registro de usuário
- Login e geração de token JWT
- Acesso a dados do usuário (/api/auth/me)
- Análise com usuário autenticado
- Histórico pessoal
- Análise sem autenticação
```

### test_auth_security.py
**Funcionalidade:** Validação de senhas fracas vs fortes
```python
# O que testa:
- Senha muito curta (rejeitada)
- Senha sem maiúscula (rejeitada)  
- Senha sem minúscula (rejeitada)
- Senha sem número (rejeitada)
- Senha sem caractere especial (rejeitada)
- Senha forte (aceita)
```

### test_security_complete.py
**Funcionalidade:** Teste completo de todas as validações de segurança
```python
# O que testa:
- Todas as regras de validação de senha
- Proteção contra força bruta (5 tentativas)
- Bloqueio temporário (15 minutos)
- Contador decrescente de tentativas
- Validação de formato de email
```

### test_rate_limiting.py
**Funcionalidade:** Rate limiting por endpoint
```python
# O que testa:
- Limite /api/upload/limits (30/min)
- Limite /api/auth/register (5/min)
- Limite /api/auth/login (20/min)
- Resposta HTTP 429 ao exceder
- Mensagem de erro apropriada
```

### test_upload.py
**Funcionalidade:** Upload e processamento de arquivos
```python
# O que testa:
- Upload de PDF gerado dinamicamente
- Extração de texto via OCR/parsing
- Identificação de banco
- Extração de linha digitável
- Predição do modelo ML
- Validação de arquivo
```

### test_upload_auth.py
**Funcionalidade:** Upload com usuário autenticado
```python
# O que testa:
- Login e obtenção de token
- Upload com autenticação
- Vinculação ao user_id
- Histórico pessoal do usuário
- Dados de debug extras
- Limites diferenciados (100/dia vs 5/dia)
```

### test_ocr.py
**Funcionalidade:** Teste específico do OCR
```python
# O que testa:
- Configuração do Tesseract
- Versão do OCR instalada
- Processamento de imagem simples
- Extração de texto básica
```

## Tipos de Validação por Teste

### Segurança
- **Autenticação:** Senhas fortes, JWT, proteção contra força bruta
- **Rate Limiting:** Limites por endpoint, bloqueio automático
- **Validação:** Emails, arquivos, dados de entrada

### Funcionalidade
- **API:** Endpoints funcionando, respostas corretas
- **Upload:** Processamento de arquivos, OCR, validação
- **Modelo ML:** Predições, confiança, features extraídas

### Integração
- **Banco de Dados:** Persistência, histórico, usuários
- **Autenticação:** Tokens, sessões, permissões
- **Rate Limiting:** Controle distribuído, limpeza automática

## Resultados Esperados

### Sucesso (Status 200/201)
```json
{
  "message": "Operação realizada com sucesso",
  "data": {...}
}
```

### Rate Limit (Status 429)
```json
{
  "error": "Rate limit excedido",
  "detail": "Máximo X requests por minuto",
  "retry_after": 45.2
}
```

### Validação (Status 400)
```json
{
  "error": "Senha deve ter pelo menos 8 caracteres"
}
```

### Força Bruta (Status 429)
```json
{
  "error": "Muitas tentativas de login. Bloqueado por 14m 58s",
  "retry_after": "Bloqueado por 14m 58s"
}
```

## Dados de Teste

### Usuários de Teste
- **Email:** joao@teste.com
- **Senha:** 123456 (rejeitada - muito simples)
- **Senha forte:** MinhaSenh@123! (aceita)

### Boletos de Teste
```python
# PDF gerado dinamicamente
"Banco do Brasil S.A."
"Linha Digitável: 00190.00009 01234.567890 12345.678901 2 12345678901234"
"Valor: R$ 1.250,75"

# Resultado esperado
"Banco": "Banco do Brasil"
"Predição": "Falso" (alta confiança ~93-96%)
```

## Configuração de Ambiente

### Dependências Necessárias
```bash
pip install requests  # Para testes HTTP
```

### Variáveis de Ambiente
```env
# Servidor deve estar rodando em:
BASE_URL=http://localhost:5000
```

### Arquivos Temporários
Os testes criam arquivos temporários que são automaticamente removidos:
- `boleto_teste.pdf`
- `boleto_auth_teste.pdf`
- `test_ocr_*.jpg`

## Debugging

### Logs Úteis
- Console do servidor mostra detalhes das requisições
- Logs de segurança em `logs/security.log` (se configurado)
- Rate limiting mostra contadores no console

### Problemas Comuns

**Servidor não responde:**
```bash
# Verificar se está rodando
curl http://localhost:5000/api/health
```

**OCR não funciona:**
```bash
# Verificar Tesseract
"C:\Program Files\Tesseract-OCR\tesseract.exe" --version
```

**Rate limit muito baixo:**
```python
# Aguardar 1 minuto ou reiniciar servidor
# Rate limiting é resetado ao reiniciar
```

## Executar Todos os Testes

### Script para Executar Sequencialmente
```bash
#!/bin/bash
echo "Executando todos os testes..."

python tests/test_ocr.py
python tests/test_api_basic.py  
python tests/test_auth_basic.py
python tests/test_auth_security.py
python tests/test_security_complete.py
python tests/test_upload.py
python tests/test_upload_auth.py
python tests/test_rate_limiting.py

echo "Todos os testes concluídos!"
```

### Versão Windows (PowerShell)
```powershell
Write-Host "Executando todos os testes..."

python tests/test_ocr.py
python tests/test_api_basic.py
python tests/test_auth_basic.py
python tests/test_auth_security.py  
python tests/test_security_complete.py
python tests/test_upload.py
python tests/test_upload_auth.py
python tests/test_rate_limiting.py

Write-Host "Todos os testes concluídos!"
```

## Relatórios de Teste

### Métricas Importantes
- **Taxa de sucesso:** % de testes passando
- **Tempo de resposta:** Latência média dos endpoints
- **Cobertura:** Funcionalidades testadas vs implementadas
- **Segurança:** Vulnerabilidades identificadas e mitigadas

### Exemplo de Saída
```
=== RESUMO DOS TESTES ===
API Básica: PASSOU
Autenticação: PASSOU  
Segurança: PASSOU
Rate Limiting: PASSOU
Upload: PASSOU
OCR: PASSOU

Total: 6/6 testes passaram (100%)
```