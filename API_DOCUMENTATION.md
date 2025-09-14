# API Documentation - Detector de Boletos

Documentação completa da API para integração com o frontend.

## Base URL

**Desenvolvimento:** `http://localhost:5000`
**Produção:** `https://detecta-boletos.onrender.com`

## Configurações Gerais

### Headers Obrigatórios
```javascript
{
  "Content-Type": "application/json",
  "Authorization": "Bearer seu-jwt-token" // Para rotas protegidas
}
```

### CORS
A API está configurada para aceitar requisições dos seguintes domínios:
- `http://localhost:3000` (React/Next.js)
- `http://localhost:8100` (Ionic)
- `https://seu-frontend.vercel.app` (Produção)

## Endpoints Disponíveis

### 1. Health Check

**GET** `/health`

Verifica se a API está funcionando.

**Resposta:**
```json
{
  "status": "healthy"
}
```

**Exemplo em JavaScript:**
```javascript
const response = await fetch('https://detecta-boletos.onrender.com/health');
const data = await response.json();
console.log(data); // { status: "healthy" }
```

---

### 2. Informações da API

**GET** `/`

Retorna informações básicas da API.

**Resposta:**
```json
{
  "message": "API Detecta Boletos funcionando!",
  "status": "online"
}
```

---

### 3. Autenticação

#### 3.1 Registro de Usuário

**POST** `/api/auth/register`

**Body:**
```json
{
  "name": "João Silva",
  "email": "joao@email.com",
  "password": "senha123"
}
```

**Resposta (Sucesso - 201):**
```json
{
  "message": "Usuário criado com sucesso",
  "user": {
    "id": 1,
    "name": "João Silva",
    "email": "joao@email.com"
  }
}
```

**Resposta (Erro - 400):**
```json
{
  "error": "Email já cadastrado"
}
```

**Exemplo em JavaScript:**
```javascript
const registerUser = async (userData) => {
  try {
    const response = await fetch('https://detecta-boletos.onrender.com/api/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(userData)
    });
    
    const data = await response.json();
    
    if (response.ok) {
      console.log('Usuário criado:', data);
      return data;
    } else {
      throw new Error(data.error);
    }
  } catch (error) {
    console.error('Erro no registro:', error);
    throw error;
  }
};
```

#### 3.2 Login

**POST** `/api/auth/login`

**Body:**
```json
{
  "email": "joao@email.com",
  "password": "senha123"
}
```

**Resposta (Sucesso - 200):**
```json
{
  "message": "Login realizado com sucesso",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "name": "João Silva",
    "email": "joao@email.com"
  }
}
```

**Resposta (Erro - 401):**
```json
{
  "error": "Credenciais inválidas"
}
```

**Exemplo em JavaScript:**
```javascript
const loginUser = async (credentials) => {
  try {
    const response = await fetch('https://detecta-boletos.onrender.com/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(credentials)
    });
    
    const data = await response.json();
    
    if (response.ok) {
      // Salvar token no localStorage
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      return data;
    } else {
      throw new Error(data.error);
    }
  } catch (error) {
    console.error('Erro no login:', error);
    throw error;
  }
};
```

---

### 4. Detecção de Boletos

#### 4.1 Upload e Análise de Documento

**POST** `/api/boleto/detect`

**Headers:**
```javascript
{
  "Authorization": "Bearer seu-jwt-token"
}
```

**Body (FormData):**
```javascript
const formData = new FormData();
formData.append('file', arquivo); // File object
formData.append('banco_emissor', 'Banco do Brasil'); // Opcional
```

**Resposta (Sucesso - 200):**
```json
{
  "success": true,
  "prediction": {
    "is_boleto": true,
    "confidence": 0.95,
    "probability": 0.87
  },
  "extracted_data": {
    "banco_emissor": "Banco do Brasil",
    "codigo_banco": "001",
    "valor": "150.00",
    "linha_digitavel": "00190.00009 01234.567890 12345.678901 2 98760000015000"
  },
  "explanation": {
    "important_features": [
      {
        "feature": "codigo_banco",
        "importance": 0.3,
        "value": "001"
      },
      {
        "feature": "linha_digitavel",
        "importance": 0.25,
        "description": "Formato válido de linha digitável"
      }
    ]
  },
  "processing_time": 2.3
}
```

**Resposta (Erro - 400):**
```json
{
  "error": "Arquivo não suportado. Use PDF, JPG, JPEG ou PNG"
}
```

**Exemplo completo em JavaScript:**
```javascript
const detectBoleto = async (file, bancoEmissor = null) => {
  try {
    const token = localStorage.getItem('token');
    
    if (!token) {
      throw new Error('Token não encontrado. Faça login novamente.');
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    if (bancoEmissor) {
      formData.append('banco_emissor', bancoEmissor);
    }
    
    const response = await fetch('https://detecta-boletos.onrender.com/api/boleto/detect', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });
    
    const data = await response.json();
    
    if (response.ok) {
      return data;
    } else {
      throw new Error(data.error);
    }
  } catch (error) {
    console.error('Erro na detecção:', error);
    throw error;
  }
};
```

#### 4.2 Histórico de Análises

**GET** `/api/boleto/history`

**Headers:**
```javascript
{
  "Authorization": "Bearer seu-jwt-token"
}
```

**Query Parameters (opcionais):**
- `page`: Número da página (padrão: 1)
- `limit`: Itens por página (padrão: 10)
- `date_from`: Data inicial (formato: YYYY-MM-DD)
- `date_to`: Data final (formato: YYYY-MM-DD)

**Resposta:**
```json
{
  "analyses": [
    {
      "id": 1,
      "filename": "boleto_exemplo.pdf",
      "is_boleto": true,
      "confidence": 0.95,
      "created_at": "2025-09-14T10:30:00Z",
      "extracted_data": {
        "banco_emissor": "Banco do Brasil",
        "valor": "150.00"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "total_pages": 5,
    "total_items": 45,
    "items_per_page": 10
  }
}
```

**Exemplo em JavaScript:**
```javascript
const getHistory = async (page = 1, limit = 10) => {
  try {
    const token = localStorage.getItem('token');
    const url = new URL('https://detecta-boletos.onrender.com/api/boleto/history');
    
    url.searchParams.append('page', page);
    url.searchParams.append('limit', limit);
    
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Erro ao buscar histórico:', error);
    throw error;
  }
};
```

---

## Tratamento de Erros

### Códigos de Status HTTP

| Código | Significado | Descrição |
|--------|-------------|-----------|
| 200 | OK | Requisição bem-sucedida |
| 201 | Created | Recurso criado com sucesso |
| 400 | Bad Request | Dados inválidos |
| 401 | Unauthorized | Token inválido ou ausente |
| 403 | Forbidden | Sem permissão |
| 404 | Not Found | Recurso não encontrado |
| 429 | Too Many Requests | Rate limit excedido |
| 500 | Internal Server Error | Erro interno do servidor |

### Estrutura de Resposta de Erro

```json
{
  "error": "Mensagem do erro",
  "details": "Detalhes adicionais (opcional)",
  "code": "ERROR_CODE (opcional)"
}
```

---

## Exemplos de Integração

### React/Next.js

```javascript
// hooks/useAuth.js
import { useState, useEffect } from 'react';

export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);

  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
    }
  }, []);

  const login = async (credentials) => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });
    
    const data = await response.json();
    
    if (response.ok) {
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      setToken(data.token);
      setUser(data.user);
    }
    
    return data;
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  return { user, token, login, logout };
};
```

### Componente de Upload

```javascript
// components/BoletoUpload.jsx
import { useState } from 'react';

const BoletoUpload = () => {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch('/api/boleto/detect', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Erro:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input 
        type="file" 
        onChange={(e) => setFile(e.target.files[0])}
        accept=".pdf,.jpg,.jpeg,.png"
      />
      <button onClick={handleUpload} disabled={!file || loading}>
        {loading ? 'Analisando...' : 'Detectar Boleto'}
      </button>
      
      {result && (
        <div>
          <h3>Resultado:</h3>
          <p>É boleto: {result.prediction.is_boleto ? 'Sim' : 'Não'}</p>
          <p>Confiança: {(result.prediction.confidence * 100).toFixed(1)}%</p>
        </div>
      )}
    </div>
  );
};

export default BoletoUpload;
```

## Recomendações para o Frontend

### **UX/UI**
- **Feedback Visual**: Sempre mostrar o status da análise (loading, sucesso, erro)
- **Validação**: Validar arquivos antes de enviar para API
- **Responsividade**: Interface deve funcionar em mobile
- **Acessibilidade**: Usar cores e ícones adequados para daltônicos

### **Performance**
- **Cache**: Cachear resultados do histórico por alguns minutos
- **Lazy Loading**: Carregar histórico sob demanda
- **Debounce**: Para filtros de busca no histórico
- **Compressão**: Comprimir imagens antes do upload se possível

### **Segurança**
- **Token Storage**: Armazenar JWT de forma segura (localStorage ou httpOnly cookies)
- **Auto-logout**: Limpar dados quando token expira
- **Validação**: Sempre validar dados antes de enviar
- **HTTPS**: Usar apenas conexões seguras em produção

### **Estados da Interface**
```javascript
// Estados recomendados para gerenciar
{
  loading: false,
  uploading: false,
  analyzing: false,
  error: null,
  result: null,
  history: [],
  pagination: {},
  user: null,
  token: null
}
```

---

## Rate Limiting

A API possui rate limiting configurado:
- **Geral**: 100 requisições por hora por IP
- **Login**: 5 tentativas por minuto por IP
- **Upload**: 10 uploads por minuto por usuário

---

## Segurança

### JWT Token
- **Expiração**: 24 horas
- **Renovação**: Faça login novamente quando expirar
- **Armazenamento**: Use localStorage ou cookies seguros

### Upload de Arquivos
- **Tamanho máximo**: 16MB
- **Tipos permitidos**: PDF, JPG, JPEG, PNG
- **Validação**: Arquivos são validados no servidor

---

## Suporte

Para dúvidas ou problemas:
- **GitHub**: [issues do repositório]
- **Email**: [seu-email@exemplo.com]

---

## Changelog

### v1.0.0 (2025-09-14)
- Implementação inicial da API
- Endpoints de autenticação
- Detecção de boletos com IA
- Documentação completa
