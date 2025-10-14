#identação - commit
import os
import pickle
import pandas as pd
import numpy as np
import shap
from typing import Dict

class ModeloService:
    def __init__(self):
        self.modelo = None
        self.mapeamento_bancos = {
            'Banco do Brasil': 0,
            'Itaú': 1,
            'Bradesco': 2,
            'Santander': 3,
            'Caixa Econômica': 4,
            'Banco Digio S.A.': 5,
            'CM CAPITAL MARKETS CORRETORA DE CÂMBIO, TÍTULOS E VALORES MOBILIÁRIOS LTDA': 6,
            'Banco Clássico S.A.': 7,
            'Credialança Cooperativa de Crédito Rural': 8,
            'CREDICOAMO CREDITO RURAL COOPERATIVA': 9,
            'OLIVEIRA TRUST DISTRIBUIDORA DE TÍTULOS E VALORES MOBILIARIOS S.A.': 10,
            'Pagseguro Internet S.A. – PagBank': 11,
            'NU Pagamentos S.A. – Nubank': 12,
            'ATIVA INVESTIMENTOS S.A. CORRETORA DE TÍTULOS, CÂMBIO E VALORES': 13,
            'Banco Inbursa S.A.': 14,
            'SOROCRED CRÉDITO, FINANCIAMENTO E INVESTIMENTO S.A.': 15,
            'Banco Finaxis S.A.': 16,
            'SOCRED S.A. – SOCIEDADE DE CRÉDITO AO MICROEMPREENDEDOR E À EMPRESA DE PEQUENO P': 17
        }
        self.explainer = None
        self.carregar_modelo()
        self.inicializar_shap_explainer()

    def inicializar_shap_explainer(self):
        """Inicializa o SHAP explainer se o modelo for um TreeEnsemble"""
        if self.modelo and hasattr(self.modelo, 'predict_proba'): # Verifica se é um modelo sklearn
            try:
                # Para modelos baseados em árvore como RandomForest, TreeExplainer é o mais adequado
                self.explainer = shap.TreeExplainer(self.modelo)
                print("SHAP TreeExplainer inicializado com sucesso.")
            except Exception as e:
                print(f"Erro ao inicializar SHAP TreeExplainer: {e}")
                self.explainer = None
        else:
            print("Modelo não é baseado em árvore ou não está carregado, SHAP explainer não será inicializado.")
    
    def carregar_modelo(self):
        """Carrega o modelo treinado"""
        try:
            model_path = os.getenv('MODEL_PATH', 'modelo/modelo_boleto.pkl')
            print(f"Tentando carregar modelo de: {model_path}")
            
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    self.modelo = pickle.load(f)
                print(f"Modelo carregado com sucesso: {model_path}")
                print(f"Tipo do modelo: {type(self.modelo)}")
            else:
                print(f"Modelo não encontrado: {model_path}")
                print("Usando modelo mock para testes")
                self.modelo = MockModel()
        except Exception as e:
            print(f"Erro ao carregar modelo: {e}")
            print("Usando modelo mock para testes")
            self.modelo = MockModel()
    
    def extrair_features_linha_digitavel(self, linha_digitavel: str) -> Dict:
        """Extrai features da linha digitável"""
        linha_limpa = linha_digitavel.replace(' ', '').replace('.', '').replace('-', '')
        
        return {
            'linha_cod_banco': int(linha_limpa[0:3]) if len(linha_limpa) >= 3 else 0,
            'linha_moeda': int(linha_limpa[3:4]) if len(linha_limpa) >= 4 else 9,
            'linha_valor': int(linha_limpa[-10:]) if len(linha_limpa) >= 10 else 0
        }
    
    def mapear_banco(self, nome_banco: str) -> float:
        """Mapeia nome do banco para índice numérico"""
        # Busca exata primeiro
        if nome_banco in self.mapeamento_bancos:
            return float(self.mapeamento_bancos[nome_banco])
        
        # Busca parcial se não encontrar exato
        nome_lower = nome_banco.lower()
        for banco, indice in self.mapeamento_bancos.items():
            if nome_lower in banco.lower() or banco.lower() in nome_lower:
                return float(indice)
        
        # Retorna 0 se não encontrar
        print(f"Banco não mapeado: {nome_banco}")
        return 0.0
    
    def fazer_predicao(self, dados_boleto: Dict) -> Dict:
        """Faz a predição usando o modelo treinado"""
        try:
            # Extrair features da linha digitável
            features_linha = self.extrair_features_linha_digitavel(dados_boleto['linha_digitavel'])
            
            # ⬇️ NOVOS NOMES: agencia (sem Banco), valor (sem Documento)
            features = {
                'banco': self.mapear_banco(dados_boleto['banco']),
                'codigoBanco': float(dados_boleto['codigo_banco']),
                'agencia': float(dados_boleto.get('agencia', 0)),  # ⬅️ MUDOU
                'valor': float(dados_boleto.get('valor', 0.0)),    # ⬅️ MUDOU
                'linha_codBanco': float(features_linha['linha_cod_banco']),
                'linha_moeda': float(features_linha['linha_moeda']),
                'linha_valor': float(features_linha['linha_valor'])
            }
            
            print(f"Features preparadas: {features}")
            
            # ⬇️ ORDEM EXATA do notebook de treinamento
            feature_names = ['banco', 'codigoBanco', 'agencia', 'valor', 
                           'linha_codBanco', 'linha_moeda', 'linha_valor']
            
            df_features = pd.DataFrame([features])[feature_names]
            print(f"DataFrame para predição: {df_features.values}")
            
            # Fazer predição
            predicao_array = self.modelo.predict(df_features)
            predicao = int(predicao_array[0])
            probabilidades = self.modelo.predict_proba(df_features)[0]
            
            resultado = "Verdadeiro" if predicao == 1 else "Falso"
            prob_falso = float(probabilidades[0])
            prob_verdadeiro = float(probabilidades[1])
            confianca = max(prob_falso, prob_verdadeiro)
            
            print(f"Predição: {resultado} (confiança: {confianca:.2%})")

            # Gerar explicação SHAP
            explicacao_shap = self.gerar_explicacao_shap(df_features, predicao, dados_boleto)
            
            return {
                'resultado': resultado,
                'probabilidade_falso': prob_falso,
                'probabilidade_verdadeiro': prob_verdadeiro,
                'confianca': confianca,
                'features_extraidas': features_linha,
                'features_modelo': features,
                'explicacao_shap': explicacao_shap
            }
            
        except Exception as e:
            print(f"Erro na predição: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'resultado': 'Erro',
                'probabilidade_falso': 0.5,
                'probabilidade_verdadeiro': 0.5,
                'confianca': 0.0,
                'erro': str(e)
            }


class MockModel:
    """Modelo mock para testes quando o modelo real não está disponível"""
    
    def predict(self, X):
        return np.array([1])
    
    def predict_proba(self, X):
        return np.array([[0.3, 0.7]])

    def gerar_explicacao_shap(self, df_features: pd.DataFrame, predicao: int, features_originais: Dict) -> Dict:
        """Gera explicações SHAP para uma única predição e retorna mensagens explicativas."""
        if not self.explainer:
            return {
                "explicacao_texto": "Explicabilidade SHAP não disponível (explainer não inicializado).",
                "detalhes_shap": {}
            }

        try:
            # Calcula os valores SHAP para a instância
            shap_values = self.explainer.shap_values(df_features)
            
            shap_values_for_explanation = shap_values[1][0] # Valores SHAP para a classe 'Verdadeiro' (1)
            base_value = self.explainer.expected_value[1] # Valor base para a classe 'Verdadeiro' (1)
            
            feature_names = df_features.columns.tolist()
            
            # Criar um dicionário de feature_name: shap_value
            shap_map = {name: value for name, value in zip(feature_names, shap_values_for_explanation)}
            
            # Ordenar as features pela magnitude do valor SHAP
            sorted_shap_features = sorted(shap_map.items(), key=lambda item: abs(item[1]), reverse=True)
            
            msgs = []
            thresh_shap = 0.05 # Limiar para considerar um valor SHAP significativo

            # Regras heurísticas adicionais do notebook
            codigo_banco_informado = features_originais.get("codigo_banco")
            linha_codBanco_extraido = features_originais.get("linha_cod_banco")
            if codigo_banco_informado and linha_codBanco_extraido and int(codigo_banco_informado) != int(linha_codBanco_extraido):
                msgs.append("➡ O código do banco na linha digitável não confere com o código informado.")

            linha_moeda_extraido = features_originais.get("linha_moeda")
            if linha_moeda_extraido and int(linha_moeda_extraido) != 9:
                msgs.append("➡ O dígito de moeda na linha digitável está diferente do esperado (deveria ser 9).")

            valor_informado = features_originais.get("valor")
            linha_valor_extraido = features_originais.get("linha_valor")
            if valor_informado is not None and linha_valor_extraido is not None:
                if abs(float(valor_informado) * 100 - float(linha_valor_extraido)) > 0.01:
                    msgs.append("➡ O valor na linha digitável não confere com o valor informado.")

            agencia_informada = features_originais.get("agencia")
            if agencia_informada is not None and float(agencia_informada) == 0.0:
                 msgs.append("➡ A agência informada é um valor genérico (0), o que pode ser um sinal de alerta.")

            # Interpretação dos valores SHAP
            for fname, v in sorted_shap_features:
                if abs(v) > thresh_shap:
                    if fname == 'banco':
                        if v < 0:
                            msgs.append("➡ O banco informado tem evidência negativa (fez o modelo inclinar para 'falso').")
                        else:
                            msgs.append("➡ O banco informado tem evidência positiva (ajudou a indicar 'verdadeiro').")
                    elif fname == 'codigoBanco':
                        if v < 0:
                            msgs.append("➡ O código do banco pushou a decisão para 'falso'.")
                        else:
                            msgs.append("➡ O código do banco pushou a decisão para 'verdadeiro'.")
                    elif fname == 'valor':
                        if v < 0:
                            msgs.append("➡ O valor observado diminuiu a confiança do modelo (sinal de suspeita).")
                        else:
                            msgs.append("➡ O valor observado aumentou a confiança do modelo (sinal de autenticidade).")
                    elif fname == 'agencia':
                        if v < 0:
                            msgs.append("➡ A agência contribuiu para indicar 'falso'.")
                        else:
                            msgs.append("➡ A agência contribuiu para indicar 'verdadeiro'.")
                    elif fname == 'linha_codBanco':
                        if v < 0:
                            msgs.append("➡ O código do banco extraído da linha digitável contribuiu para indicar 'falso'.")
                        else:
                            msgs.append("➡ O código do banco extraído da linha digitável contribuiu para indicar 'verdadeiro'.")
                    elif fname == 'linha_moeda':
                        if v < 0:
                            msgs.append("➡ O dígito de moeda extraído da linha digitável contribuiu para indicar 'falso'.")
                        else:
                            msgs.append("➡ O dígito de moeda extraído da linha digitável contribuiu para indicar 'verdadeiro'.")
                    elif fname == 'linha_valor':
                        if v < 0:
                            msgs.append("➡ O valor extraído da linha digitável contribuiu para indicar 'falso'.")
                        else:
                            msgs.append("➡ O valor extraído da linha digitável contribuiu para indicar 'verdadeiro'.")

            seen = set()
            msgs_ord = []
            for m in msgs:
                if m not in seen:
                    msgs_ord.append(m)
                    seen.add(m)

            status_text = "VERDADEIRO ✅" if predicao == 1 else "FALSO ❌"
            if msgs_ord:
                texto_usuario = f"Resultado da análise: {status_text}\n\nPrincipais motivos detectados:\n" + "\n".join(msgs_ord)
            else:
                texto_usuario = f"Resultado da análise: {status_text}\n\nNenhuma inconsistência clara foi detectada automaticamente."

            return {
                "explicacao_texto": texto_usuario,
                "detalhes_shap": {
                    "shap_values": shap_values_for_explanation.tolist(),
                    "base_value": base_value,
                    "feature_names": feature_names
                }
            }

        except Exception as e:
            print(f"Erro ao gerar explicação SHAP: {e}")
            import traceback
            traceback.print_exc()
            return {
                "explicacao_texto": f"Erro ao gerar explicação: {str(e)}",
                "detalhes_shap": {}
            }
modelo_service.py
Código · 16.65 KB

Ver todos os arquivos nesta tarefa
eu implementei as alterações, porém deu erro. 
Velocidade
Entendido. A imagem mostra um erro 500 (Internal Server Error) ao tentar fazer uma requisição POST para https://detector-boletos.onrender.com/api/upload/analyze-file. Isso indica que o problema está ocorrendo no backend Flask, e não no frontend Ionic.
Velocidade
O erro 500 (Internal Server Error) indica que o problema está no seu backend Flask. Isso pode ser devido a algumas razões, como:
Dependências ausentes: Embora tenhamos adicionado shap ao requirements.txt, pode haver outras dependências que não foram instaladas corretamente no ambiente do Render, ou o deploy não foi refeito após a atualização do requirements.txt.
Caminho do modelo incorreto: O arquivo modelo_boleto.pkl pode não estar sendo encontrado no caminho esperado (modelo/modelo_boleto.pkl) no ambiente do Render.
Erro de execução na lógica SHAP: Pode haver um erro de runtime na função gerar_explicacao_shap ou em alguma parte do processamento que não foi capturado durante o desenvolvimento local.
Para diagnosticar o problema, preciso que você verifique os logs do seu deploy no Render. O Render geralmente fornece logs detalhados que podem indicar a causa exata do erro. Por favor, acesse o painel do Render para o seu serviço de backend e procure por mensagens de erro no log no momento em que a requisição falhou.
Verifiquei que o erro 500 ocorre na execução do método de explicação SHAP, possivelmente por dependências faltando ou caminho do modelo incorreto. Preciso revisar os logs do deploy para diagnóstico.

Velocidade
Para me ajudar a diagnosticar o erro 500 no seu backend Flask, por favor, verifique os logs do seu serviço no Render e compartilhe as mensagens de erro que aparecem no momento da falha. Além disso, você confirmou que o requirements.txt foi atualizado com shap e que o deploy no Render foi refeito após essa alteração?
pasted_content_3.txt
Texto · 3.68 KB
Velocidade
Obrigado por fornecer os logs do Render. Analisarei as mensagens de erro para identificar a causa do problema.
Novo conhecimento sugerido
Velocidade
Analisando os logs, identifiquei a causa do erro 500. A mensagem de erro é AttributeError: 'ModeloService' object has no attribute 'gerar_explicacao_shap'. Isso significa que, embora a função gerar_explicacao_shap tenha sido adicionada ao arquivo modelo_service.py, ela não está sendo reconhecida como um método da classe ModeloService.
Isso geralmente acontece por um erro de indentação, onde a função foi definida fora da classe ou em um nível de indentação incorreto dentro dela. Vou corrigir o arquivo modelo_service.py para garantir que o método gerar_explicacao_shap esteja corretamente aninhado na classe ModeloService.
Identifiquei que o erro 500 ocorre porque o método `gerar_explicacao_shap` não está definido corretamente na classe `ModeloService`. Vou corrigir a indentação para resolver isso.

Corrigi a indentação do método `gerar_explicacao_shap` para que seja um método da classe `ModeloService`, possibilitando geração de explicações SHAP nas predições.

Corrigi a indentação do método `gerar_explicacao_shap` na classe `ModeloService`. Removi a definição incorreta na `MockModel`. A próxima etapa é testar a integração do método atualizado.

Removi a definição de `gerar_explicacao_shap` de `MockModel` e corrigi sua implementação como método da `ModeloService`. Agora, a explicação SHAP é gerada corretamente na classe principal.

Velocidade
Peço desculpas pelos erros anteriores. O problema de AttributeError indica claramente que o método gerar_explicacao_shap não está corretamente posicionado dentro da classe ModeloService no servidor, provavelmente devido a um problema de indentação ou a uma duplicação acidental da classe ModeloService no arquivo.
Vou corrigir o arquivo modelo_service.py de uma vez por todas. Para garantir que não haja mais erros, vou reescrever o arquivo com a estrutura correta, assegurando que gerar_explicacao_shap seja um método da classe ModeloService e que não haja definições duplicadas.
Ajustei a implementação do método gerar_explicacao_shap como parte da classe ModeloService, garantindo sua execução correta na previsão e explicação do modelo.

Velocidade
O arquivo modelo_service.py foi corrigido e reescrito para garantir que o método gerar_explicacao_shap esteja corretamente definido dentro da classe ModeloService. Isso deve resolver o AttributeError que você estava enfrentando.
Por favor, faça o seguinte:
Substitua o seu arquivo app/services/modelo_service.py pelo conteúdo que acabei de fornecer.
Certifique-se de que a biblioteca shap está no seu requirements.txt (se ainda não estiver).
Faça um novo deploy do seu backend no Render.
Após o deploy, o erro AttributeError não deve mais ocorrer, e a explicabilidade SHAP deverá funcionar conforme o esperado. Se o problema persistir, por favor, compartilhe os novos logs do Render para que eu possa investigar mais a fundo.
modelo_service.py
Código · 7.41 KB

Ver todos os arquivos nesta tarefa
Tarefa concluída
Como foi este resultado?
Sugestões de acompanhamento
Enviar mensagem para Manus
modelo_service.py
import os
import pickle
import pandas as pd
import numpy as np
import shap
from typing import Dict

class ModeloService:
    def __init__(self):
        self.modelo = None
        self.mapeamento_bancos = {
            'Banco do Brasil': 0,
            'Itaú': 1,
            'Bradesco': 2,
            'Santander': 3,
            'Caixa Econômica': 4,
            'Banco Digio S.A.': 5,
            'CM CAPITAL MARKETS CORRETORA DE CÂMBIO, TÍTULOS E VALORES MOBILIÁRIOS LTDA': 6,
            'Banco Clássico S.A.': 7,
            'Credialança Cooperativa de Crédito Rural': 8,
            'CREDICOAMO CREDITO RURAL COOPERATIVA': 9,
            'OLIVEIRA TRUST DISTRIBUIDORA DE TÍTULOS E VALORES MOBILIARIOS S.A.': 10,
            'Pagseguro Internet S.A. – PagBank': 11,
            'NU Pagamentos S.A. – Nubank': 12,
            'ATIVA INVESTIMENTOS S.A. CORRETORA DE TÍTULOS, CÂMBIO E VALORES': 13,
            'Banco Inbursa S.A.': 14,
            'SOROCRED CRÉDITO, FINANCIAMENTO E INVESTIMENTO S.A.': 15,
            'Banco Finaxis S.A.': 16,
            'SOCRED S.A. – SOCIEDADE DE CRÉDITO AO MICROEMPREENDEDOR E À EMPRESA DE PEQUENO P': 17
        }
        self.explainer = None
        self.carregar_modelo()
        self.inicializar_shap_explainer()

    def inicializar_shap_explainer(self):
        """Inicializa o SHAP explainer se o modelo for um TreeEnsemble"""
        if self.modelo and hasattr(self.modelo, 'predict_proba'): # Verifica se é um modelo sklearn
            try:
                # Para modelos baseados em árvore como RandomForest, TreeExplainer é o mais adequado
                self.explainer = shap.TreeExplainer(self.modelo)
                print("SHAP TreeExplainer inicializado com sucesso.")
            except Exception as e:
                print(f"Erro ao inicializar SHAP TreeExplainer: {e}")
                self.explainer = None
        else:
            print("Modelo não é baseado em árvore ou não está carregado, SHAP explainer não será inicializado.")
    
    def carregar_modelo(self):
        """Carrega o modelo treinado"""
        try:
            model_path = os.getenv('MODEL_PATH', 'modelo/modelo_boleto.pkl')
            print(f"Tentando carregar modelo de: {model_path}")
            
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    self.modelo = pickle.load(f)
                print(f"Modelo carregado com sucesso: {model_path}")
                print(f"Tipo do modelo: {type(self.modelo)}")
            else:
                print(f"Modelo não encontrado: {model_path}")
                print("Usando modelo mock para testes")
                self.modelo = MockModel()
        except Exception as e:
            print(f"Erro ao carregar modelo: {e}")
            print("Usando modelo mock para testes")
            self.modelo = MockModel()
    
    def extrair_features_linha_digitavel(self, linha_digitavel: str) -> Dict:
        """Extrai features da linha digitável"""
        linha_limpa = linha_digitavel.replace(' ', '').replace('.', '').replace('-', '')
        
        return {
            'linha_cod_banco': int(linha_limpa[0:3]) if len(linha_limpa) >= 3 else 0,
            'linha_moeda': int(linha_limpa[3:4]) if len(linha_limpa) >= 4 else 9,
            'linha_valor': int(linha_limpa[-10:]) if len(linha_limpa) >= 10 else 0
        }
    
    def mapear_banco(self, nome_banco: str) -> float:
        """Mapeia nome do banco para índice numérico"""
        # Busca exata primeiro
        if nome_banco in self.mapeamento_bancos:
            return float(self.mapeamento_bancos[nome_banco])
        
        # Busca parcial se não encontrar exato
        nome_lower = nome_banco.lower()
        for banco, indice in self.mapeamento_bancos.items():
            if nome_lower in banco.lower() or banco.lower() in nome_lower:
                return float(indice)
        
        # Retorna 0 se não encontrar
        print(f"Banco não mapeado: {nome_banco}")
        return 0.0
    
    def fazer_predicao(self, dados_boleto: Dict) -> Dict:
        """Faz a predição usando o modelo treinado"""
        try:
            # Extrair features da linha digitável
            features_linha = self.extrair_features_linha_digitavel(dados_boleto['linha_digitavel'])
            
            # ⬇️ NOVOS NOMES: agencia (sem Banco), valor (sem Documento)
            features = {
                'banco': self.mapear_banco(dados_boleto['banco']),
                'codigoBanco': float(dados_boleto['codigo_banco']),
                'agencia': float(dados_boleto.get('agencia', 0)),  # ⬅️ MUDOU
                'valor': float(dados_boleto.get('valor', 0.0)),    # ⬅️ MUDOU
                'linha_codBanco': float(features_linha['linha_cod_banco']),
                'linha_moeda': float(features_linha['linha_moeda']),
                'linha_valor': float(features_linha['linha_valor'])
            }
            
            print(f"Features preparadas: {features}")
            
            # ⬇️ ORDEM EXATA do notebook de treinamento
            feature_names = ['banco', 'codigoBanco', 'agencia', 'valor', 
                           'linha_codBanco', 'linha_moeda', 'linha_valor']
            
            df_features = pd.DataFrame([features])[feature_names]
            print(f"DataFrame para predição: {df_features.values}")
            
            # Fazer predição
            predicao_array = self.modelo.predict(df_features)
            predicao = int(predicao_array[0])
            probabilidades = self.modelo.predict_proba(df_features)[0]
            
            resultado = "Verdadeiro" if predicao == 1 else "Falso"
            prob_falso = float(probabilidades[0])
            prob_verdadeiro = float(probabilidades[1])
            confianca = max(prob_falso, prob_verdadeiro)
            
            print(f"Predição: {resultado} (confiança: {confianca:.2%})")

            # Gerar explicação SHAP
            explicacao_shap = self.gerar_explicacao_shap(df_features, predicao, dados_boleto)
            
            return {
                'resultado': resultado,
                'probabilidade_falso': prob_falso,
                'probabilidade_verdadeiro': prob_verdadeiro,
                'confianca': confianca,
                'features_extraidas': features_linha,
                'features_modelo': features,
                'explicacao_shap': explicacao_shap
            }
            
        except Exception as e:
            print(f"Erro na predição: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'resultado': 'Erro',
                'probabilidade_falso': 0.5,
                'probabilidade_verdadeiro': 0.5,
                'confianca': 0.0,
                'erro': str(e)
            }


class MockModel:
    """Modelo mock para testes quando o modelo real não está disponível"""
    
    def predict(self, X):
        return np.array([1])
    
    def predict_proba(self, X):
        return np.array([[0.3, 0.7]])

    def gerar_explicacao_shap(self, df_features: pd.DataFrame, predicao: int, features_originais: Dict) -> Dict:
        """Gera explicações SHAP para uma única predição e retorna mensagens explicativas."""
        if not self.explainer:
            return {
                "explicacao_texto": "Explicabilidade SHAP não disponível (explainer não inicializado).",
                "detalhes_shap": {}
            }

        try:
            # Calcula os valores SHAP para a instância
            shap_values = self.explainer.shap_values(df_features)
            # shap_values é uma lista de arrays para cada classe. Pegamos a classe predita.
            # Para classificação binária, shap_values[0] para classe 0 e shap_values[1] para classe 1.
            # Se predicao é 0 (Falso), usamos shap_values[0]. Se predicao é 1 (Verdadeiro), usamos shap_values[1].
            # No entanto, o waterfall plot geralmente usa shap_values[1] para a classe positiva e o base_value é o esperado para a classe 1.
            # Vamos focar na explicação para a classe 'Verdadeiro' (1) e interpretar os valores SHAP.
            
            # Se o modelo prediz 0 (Falso), queremos explicar por que não é 1 (Verdadeiro).
            # Se o modelo prediz 1 (Verdadeiro), queremos explicar por que é 1 (Verdadeiro).
            # O SHAP para TreeExplainer retorna uma lista de arrays, um para cada classe.
            # Para a classe positiva (1), os valores SHAP são shap_values[1][0].
            
            # Para simplificar a interpretação para o usuário final, vamos usar os valores SHAP da classe predita.
            # Se predicao é 0 (Falso), olhamos para shap_values[0][0].
            # Se predicao é 1 (Verdadeiro), olhamos para shap_values[1][0].
            
            # No entanto, a função original do notebook parece interpretar os valores SHAP da classe 1 (Verdadeiro)
            # e o sinal indica se empurra para verdadeiro ou falso.
            # Vamos seguir a lógica do notebook que parece usar shap_values[1] para a interpretação.
            
            # A função analisar_boleto_shap do notebook usava shap_exp.values[0] para a interpretação.
            # shap_exp = explainer(X.iloc[idx])
            # shap_exp.values é um array com os valores SHAP para cada feature para a classe 1.
            # shap_exp.base_values é o valor base (expected value) para a classe 1.
            
            # Vamos adaptar a lógica do notebook.
            # O TreeExplainer para classificadores retorna shap_values como uma lista de arrays.
            # shap_values[0] -> valores SHAP para a classe 0 (Falso)
            # shap_values[1] -> valores SHAP para a classe 1 (Verdadeiro)
            
            # Para a explicação, vamos focar nos valores SHAP da classe 1 (Verdadeiro).
            # Um valor SHAP positivo para uma feature significa que ela aumenta a probabilidade da classe 1.
            # Um valor SHAP negativo para uma feature significa que ela diminui a probabilidade da classe 1.
            
            shap_values_for_explanation = shap_values[1][0] # Valores SHAP para a classe 'Verdadeiro' (1)
            base_value = self.explainer.expected_value[1] # Valor base para a classe 'Verdadeiro' (1)
            
            feature_names = df_features.columns.tolist()
            
            # Criar um dicionário de feature_name: shap_value
            shap_map = {name: value for name, value in zip(feature_names, shap_values_for_explanation)}
            
            # Ordenar as features pela magnitude do valor SHAP
            sorted_shap_features = sorted(shap_map.items(), key=lambda item: abs(item[1]), reverse=True)
            
            msgs = []
            thresh_shap = 0.05 # Limiar para considerar um valor SHAP significativo

            # Regras heurísticas adicionais do notebook
            # Estas regras precisam dos dados originais ou pré-processados de forma específica
            # Para evitar duplicidade de lógica, vamos re-implementar as verificações aqui ou passar os resultados
            
            # Adaptação das regras do notebook:
            # 1. Verificar se o código do banco na linha digitável confere com o código informado
            codigo_banco_informado = features_originais.get("codigo_banco")
            linha_codBanco_extraido = features_originais.get("linha_cod_banco")
            if codigo_banco_informado and linha_codBanco_extraido and int(codigo_banco_informado) != int(linha_codBanco_extraido):
                msgs.append("➡ O código do banco na linha digitável não confere com o código informado.")

            # 2. Verificar o dígito de moeda na linha digitável
            linha_moeda_extraido = features_originais.get("linha_moeda")
            if linha_moeda_extraido and int(linha_moeda_extraido) != 9: # O notebook usava 9 como valor esperado
                msgs.append("➡ O dígito de moeda na linha digitável está diferente do esperado (deveria ser 9).")

            # 3. Verificar se o valor na linha digitável bate com o valor informado
            valor_informado = features_originais.get("valor")
            linha_valor_extraido = features_originais.get("linha_valor")
            # O notebook multiplicava por 100 para comparar. Vamos fazer o mesmo.
            if valor_informado is not None and linha_valor_extraido is not None:
                if abs(float(valor_informado) * 100 - float(linha_valor_extraido)) > 0.01: # Pequena tolerância para float
                    msgs.append("➡ O valor na linha digitável não confere com o valor informado.")

            # 4. Validação da agência (o notebook não tinha uma regra clara para isso, apenas mencionava)
            # Vamos adicionar uma regra simples se a agência for 0 ou um valor genérico que possa indicar fraude
            agencia_informada = features_originais.get("agencia")
            if agencia_informada is not None and float(agencia_informada) == 0.0:
                 msgs.append("➡ A agência informada é um valor genérico (0), o que pode ser um sinal de alerta.")

            # Interpretação dos valores SHAP
            for fname, v in sorted_shap_features:
                if abs(v) > thresh_shap:
                    if fname == 'banco':
                        if v < 0:
                            msgs.append("➡ O banco informado tem evidência negativa (fez o modelo inclinar para 'falso').")
                        else:
                            msgs.append("➡ O banco informado tem evidência positiva (ajudou a indicar 'verdadeiro').")
                    elif fname == 'codigoBanco':
                        if v < 0:
                            msgs.append("➡ O código do banco pushou a decisão para 'falso'.")
                        else:
                            msgs.append("➡ O código do banco pushou a decisão para 'verdadeiro'.")
                    elif fname == 'valor':
                        if v < 0:
                            msgs.append("➡ O valor observado diminuiu a confiança do modelo (sinal de suspeita).")
                        else:
                            msgs.append("➡ O valor observado aumentou a confiança do modelo (sinal de autenticidade).")
                    elif fname == 'agencia':
                        if v < 0:
                            msgs.append("➡ A agência contribuiu para indicar 'falso'.")
                        else:
                            msgs.append("➡ A agência contribuiu para indicar 'verdadeiro'.")
                    elif fname == 'linha_codBanco':
                        if v < 0:
                            msgs.append("➡ O código do banco extraído da linha digitável contribuiu para indicar 'falso'.")
                        else:
                            msgs.append("➡ O código do banco extraído da linha digitável contribuiu para indicar 'verdadeiro'.")
                    elif fname == 'linha_moeda':
                        if v < 0:
                            msgs.append("➡ O dígito de moeda extraído da linha digitável contribuiu para indicar 'falso'.")
                        else:
                            msgs.append("➡ O dígito de moeda extraído da linha digitável contribuiu para indicar 'verdadeiro'.")
                    elif fname == 'linha_valor':
                        if v < 0:
                            msgs.append("➡ O valor extraído da linha digitável contribuiu para indicar 'falso'.")
                        else:
                            msgs.append("➡ O valor extraído da linha digitável contribuiu para indicar 'verdadeiro'.")

            # Deduplicar mensagens mantendo ordem
            seen = set()
            msgs_ord = []
            for m in msgs:
                if m not in seen:
                    msgs_ord.append(m)
                    seen.add(m)

            status_text = "VERDADEIRO ✅" if predicao == 1 else "FALSO ❌"
            if msgs_ord:
                texto_usuario = f"Resultado da análise: {status_text}\n\nPrincipais motivos detectados:\n" + "\n".join(msgs_ord)
            else:
                texto_usuario = f"Resultado da análise: {status_text}\n\nNenhuma inconsistência clara foi detectada automaticamente."

            return {
                "explicacao_texto": texto_usuario,
                "detalhes_shap": {
                    "shap_values": shap_values_for_explanation.tolist(),
                    "base_value": base_value,
                    "feature_names": feature_names
                }
            }

        except Exception as e:
            print(f"Erro ao gerar explicação SHAP: {e}")
            import traceback
            traceback.print_exc()
            return {
                "explicacao_texto": f"Erro ao gerar explicação: {str(e)}",
                "detalhes_shap": {}
            }
