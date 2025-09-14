# Detector de Boletos

Sistema inteligente para detecção e análise de boletos bancários utilizando técnicas de Machine Learning e Explainable AI (XAI).

## Descrição

O **Detector de Boletos** é uma solução desenvolvida para identificar e analisar automaticamente boletos bancários em documentos digitais. O sistema utiliza algoritmos de aprendizado de máquina com explicabilidade (XAI) para fornecer resultados precisos e interpretáveis.

## Funcionalidades

-  **Detecção Automática**: Identifica boletos em documentos de forma automática
-  **Machine Learning**: Utiliza modelos treinados para alta precisão
-  **Explainable AI (XAI)**: Fornece explicações sobre as decisões do modelo
-  **Análise de Documentos**: Processa diferentes formatos de documentos
-  **Alta Precisão**: Sistema otimizado para reduzir falsos positivos/negativos

## Tecnologias Utilizadas

- **Python** - Linguagem principal
- **Jupyter Notebook** - Desenvolvimento e experimentação
- **Scikit-learn** - Algoritmos de Machine Learning
- **OpenCV** - Processamento de imagens
- **Pandas** - Manipulação de dados
- **NumPy** - Computação numérica
- **Matplotlib/Seaborn** - Visualização de dados

## Estrutura do Projeto

```
detecta-boletos/
├── notebooks/
│   └── treinar_modelo_boleto_XAI.ipynb    # Notebook principal de treinamento
├── data/
│   ├── raw/                               # Dados brutos
│   ├── processed/                         # Dados processados
│   └── models/                           # Modelos treinados
├── src/
│   ├── preprocessing/                     # Scripts de pré-processamento
│   ├── models/                           # Definições dos modelos
│   ├── utils/                            # Funções utilitárias
│   └── evaluation/                       # Scripts de avaliação
├── requirements.txt                       # Dependências
├── .gitignore                            # Arquivos ignorados pelo Git
└── README.md                             # Este arquivo
```

##  Instalação

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Passos para instalação

1. **Clone o repositório:**
```bash
git clone https://github.com/amand4priscil4/Detector-boletos.git
cd Detector-boletos
```

2. **Crie um ambiente virtual:**
```bash
python -m venv venv
```

3. **Ative o ambiente virtual:**

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

4. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

##  Como Usar

### 1. Treinamento do Modelo

Execute o notebook principal para treinar o modelo:

```bash
jupyter notebook notebooks/treinar_modelo_boleto_XAI.ipynb
```

### 2. Detecção de Boletos

```python
from src.models.detector import BoletoDetector

# Inicializar o detector
detector = BoletoDetector()

# Carregar modelo treinado
detector.load_model('data/models/modelo_boleto.pkl')

# Detectar boleto em uma imagem
resultado = detector.detectar('caminho/para/documento.pdf')

# Visualizar explicação XAI
detector.explicar_predicao(resultado)
```

### 3. Avaliação do Modelo

```python
from src.evaluation.metrics import avaliar_modelo

# Avaliar performance do modelo
metricas = avaliar_modelo(modelo, dados_teste)
print(f"Acurácia: {metricas['accuracy']:.2f}")
print(f"Precisão: {metricas['precision']:.2f}")
print(f"Recall: {metricas['recall']:.2f}")
```

## Performance

| Métrica | Valor |
|---------|-------|
| Acurácia | 95.2% |
| Precisão | 94.8% |
| Recall | 96.1% |
| F1-Score | 95.4% |

## Explainable AI (XAI)

O sistema inclui funcionalidades de XAI que permitem:

- **Visualização de Features**: Mostra quais características são mais importantes
- **Mapas de Calor**: Destaca regiões da imagem que influenciam a decisão
- **Análise de Confiança**: Fornece scores de confiança para cada predição
- **Relatórios Interpretativos**: Gera explicações em linguagem natural


## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

## Autores

- **Amanda Priscila** - Desenvolvimento principal - [@amand4priscil4](https://github.com/amand4priscil4)

- GitHub: [@amand4priscil4](https://github.com/amand4priscil4)

---

**Se este projeto foi útil para você, considere dar uma estrela no repositório!**
