# Sistema de Segurança - Detecta Boletos

Este documento descreve as medidas de segurança implementadas no sistema de detecção de boletos.

## Visão Geral

O sistema implementa múltiplas camadas de proteção para garantir a segurança dos dados e prevenir ataques comuns. As medidas incluem autenticação robusta, rate limiting, validação de arquivos e controle de acesso.

## Autenticação e Autorização

### Política de Senhas

**Requisitos obrigatórios:**
- Mínimo 8 caracteres
- Máximo 128 caracteres  
- Pelo menos 1 letra maiúscula
- Pelo menos 1 letra minúscula
- Pelo menos 1 número
- Pelo menos 1 caractere especial (!@#$%^&*(),.?":{}|<>)
- Não pode ser uma senha comum (12345678, password, admin123, qwerty123)

**Implementação:**
```python
# Localização: app/services/auth_security_service.py
def validate_password_strength(self, password: str) -> Tuple[bool, str]
```

### Proteção Contra Força Bruta

**Mecanismo:**
- Rastreamento por IP + email
- Limite: 5 tentativas por identificador
- Bloqueio: 15 minutos após exceder limite
- Limpeza automática de dados antigos

**Comportamento:**
- Tentativas 1-4: Retorna contador decrescente
- Tentativa 5: Última chance
- Tentativa 6+: HTTP 429 com tempo de bloqueio

**Implementação:**
```python
# Localização: app/services/auth_security_service.py
def check_brute_force(self, identifier: str) -> Tuple[bool, str, int]
```

### Validação de Email

**Verificações:**
- Formato básico via regex
- Tamanho máximo: 254 caracteres
- Padrão: usuario@dominio.tld

## Rate Limiting

### Limites por Endpoint

| Endpoint | Limite | Descrição |
|----------|--------|-----------|
| `/api/auth/register` | 5/min | Registro de usuários |
| `/api/auth/login` | 20/min | Tentativas de login |
| `/api/auth/change-password` | 3/min | Mudança de senha |
| `/api/auth/recover-password` | 2/min | Recuperação de senha |
| `/api/auth/me` | 30/min | Dados do usuário |
| `/api/upload/analyze-file` | 10/min | Upload de arquivos |
| `/api/upload/limits` | 30/min | Consulta de limites |
| `/api/upload/test-ocr` | 5/min | Teste de OCR |

### Funcionamento

**Técnica:** Sliding Window
- Janela deslizante de 60 segundos
- Contagem por IP + endpoint
- Limpeza automática de dados antigos
- Resposta HTTP 429 ao exceder limite

**Implementação:**
```python
# Localização: app/middleware/rate_limiter.py
@rate_limiter.limit(requests_per_minute=X)
```

## Validação de Arquivos

### Tipos Permitidos

**Extensões:** pdf, png, jpg, jpeg, tiff, bmp
**Tamanho máximo:** 10MB

### Verificações de Segurança

**Validação de header:**
- PDF: Deve começar com '%PDF'
- JPG/JPEG: Deve começar com '\xff\xd8\xff'
- PNG: Deve começar com '\x89PNG'
- TIFF: Deve começar com 'II*\x00' ou 'MM\x00*'
- BMP: Deve começar com 'BM'

**Sanitização:**
- Remoção de caracteres perigosos do nome
- Geração de nomes seguros com timestamp e hash
- Verificação de path traversal

**Implementação:**
```python
# Localização: app/services/security_service.py
def validate_file_security(self, file_path: str) -> Tuple[bool, str]
```

## Controle de Acesso

### Usuários Anônimos

**Limitações:**
- 5 análises por dia
- Sem acesso ao histórico pessoal
- Sem dados de debug
- Rate limiting mais restritivo

### Usuários Autenticados

**Benefícios:**
- 100 análises por dia
- Histórico pessoal completo
- Dados de debug disponíveis
- Rate limiting mais permissivo
- Funcionalidades avançadas

### Sistema de Tokens JWT

**Configuração:**
- Algoritmo: HS256
- Expiração: 24 horas
- Validação automática em rotas protegidas

## Headers de Segurança

### Headers Aplicados Automaticamente

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Cache-Control: no-cache, no-store, must-revalidate
Pragma: no-cache
```

## Logging e Auditoria

### Eventos Registrados

- Tentativas de login falhadas
- Sucessos de autenticação
- Violações de rate limit
- Uploads de arquivos
- Erros de validação

### Limpeza Automática

**Rate Limiting:**
- Dados mantidos por 1 hora
- Limpeza a cada 5 minutos

**Tentativas de Login:**
- Dados mantidos por 15 minutos
- Limpeza automática após expiração

## Dependências de Segurança

### Bibliotecas Utilizadas

```python
cryptography==41.0.7     # Criptografia
redis==5.0.1            # Cache para rate limiting
bcrypt==4.1.2           # Hash de senhas
python-jose[cryptography]==3.3.0  # JWT
```

### Instalação

```bash
pip install cryptography redis bcrypt python-jose[cryptography]
```

## Configuração

### Variáveis de Ambiente

```env
SECRET_KEY=sua-chave-secreta-muito-forte
DATABASE_URL=sqlite:///detecta_boletos.db
MODEL_PATH=modelo/modelo_boleto.pkl
```

### Recomendações para Produção

1. **SECRET_KEY:** Use uma chave criptograficamente segura de 32+ caracteres
2. **HTTPS:** Sempre use conexões seguras em produção
3. **Database:** Use PostgreSQL ou MySQL em vez de SQLite
4. **Redis:** Configure Redis para rate limiting distribuído
5. **Logs:** Implemente logging estruturado com rotação
6. **Backup:** Configure backups automáticos do banco

## Testes de Segurança

### Scripts de Teste Disponíveis

- `testar_seguranca_auth.py` - Testa validação de senhas
- `testar_seguranca_completa.py` - Testa todas as validações
- `testar_rate_limiting.py` - Testa rate limiting
- `testar_brute_force.py` - Testa proteção contra força bruta

### Executar Testes

```bash
python testar_seguranca_completa.py
python testar_rate_limiting.py
```