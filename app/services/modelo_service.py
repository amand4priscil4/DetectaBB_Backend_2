import os
import pickle
import pandas as pd
import numpy as np
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
            'Crediliança Cooperativa de Crédito Rural': 8,
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
        self.carregar_modelo()
    
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
            
            # Preparar features exatamente como no treinamento
            features = {
                'banco': self.mapear_banco(dados_boleto['banco']),
                'codigoBanco': float(dados_boleto['codigo_banco']),
                'agencia': float(dados_boleto['agencia']),
                'valor': float(dados_boleto['valor']),
                'linha_codBanco': float(features_linha['linha_cod_banco']),
                'linha_moeda': float(features_linha['linha_moeda']),
                'linha_valor': float(features_linha['linha_valor'])
            }
            
            print(f"Features preparadas: {features}")
            
            # Criar DataFrame com as features na ordem correta
            feature_names = ['banco', 'codigoBanco', 'agencia', 'valor', 
                           'linha_codBanco', 'linha_moeda', 'linha_valor']
            
            df_features = pd.DataFrame([features])[feature_names]
            print(f"DataFrame para predição: {df_features.values}")
            
            # Fazer predição
            predicao = self.modelo.predict(df_features)[0]
            probabilidades = self.modelo.predict_proba(df_features)[0]
            
            resultado = "Verdadeiro" if predicao == 1 else "Falso"
            prob_falso = float(probabilidades[0])
            prob_verdadeiro = float(probabilidades[1])
            confianca = max(prob_falso, prob_verdadeiro)
            
            print(f"Predição: {resultado} (confiança: {confianca:.2%})")
            
            return {
                'resultado': resultado,
                'probabilidade_falso': prob_falso,
                'probabilidade_verdadeiro': prob_verdadeiro,
                'confianca': confianca,
                'features_extraidas': features_linha,
                'features_modelo': features
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