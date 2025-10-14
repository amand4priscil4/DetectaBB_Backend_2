import os
import pickle
import pandas as pd
import numpy as np
import shap
from typing import Dict

class MockModel:
    """Modelo mock para testes quando o modelo real no est disponvel"""
    def predict(self, X):
        return np.array([1])
    
    def predict_proba(self, X):
        return np.array([[0.3, 0.7]])

class ModeloService:
    def __init__(self):
        self.modelo = None
        self.mapeamento_bancos = {
            'Banco do Brasil': 0,
            'Ita': 1,
            'Bradesco': 2,
            'Santander': 3,
            'Caixa Economica': 4,
            'Banco Digio S.A.': 5,
            'CM CAPITAL MARKETS CORRETORA DE CMBIO, TTULOS E VALORES MOBILIRIOS LTDA': 6,
            'Banco Clssico S.A.': 7,
            'Credialana Cooperativa de Crdito Rural': 8,
            'CREDICOAMO CREDITO RURAL COOPERATIVA': 9,
            'OLIVEIRA TRUST DISTRIBUIDORA DE TTULOS E VALORES MOBILIARIOS S.A.': 10,
            'Pagseguro Internet S.A.  PagBank': 11,
            'NU Pagamentos S.A.  Nubank': 12,
            'ATIVA INVESTIMENTOS S.A. CORRETORA DE TTULOS, CMBIO E VALORES': 13,
            'Banco Inbursa S.A.': 14,
            'SOROCRED CRDITO, FINANCIAMENTO E INVESTIMENTO S.A.': 15,
            'Banco Finaxis S.A.': 16,
            'SOCRED S.A.  SOCIEDADE DE CRDITO AO MICROEMPREENDEDOR E  EMPRESA DE PEQUENO P': 17
        }
        self.explainer = None
        self.carregar_modelo()
        self.inicializar_shap_explainer()

    def inicializar_shap_explainer(self):
        if self.modelo and not isinstance(self.modelo, MockModel) and hasattr(self.modelo, 'predict_proba'):
            try:
                self.explainer = shap.TreeExplainer(self.modelo)
                print("SHAP TreeExplainer inicializado com sucesso.")
            except Exception as e:
                print(f"Erro ao inicializar SHAP TreeExplainer: {e}")
                self.explainer = None
        else:
            print("Modelo no  do tipo suportado para SHAP TreeExplainer ou  um MockModel, explainer no inicializado.")

    def carregar_modelo(self):
        try:
            model_path = os.getenv('MODEL_PATH', 'modelo/modelo_boleto.pkl')
            print(f"Tentando carregar modelo de: {model_path}")
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    self.modelo = pickle.load(f)
                print(f"Modelo carregado com sucesso: {model_path}")
            else:
                print(f"Modelo no encontrado: {model_path}")
                self.modelo = MockModel()
        except Exception as e:
            print(f"Erro ao carregar modelo: {e}")
            self.modelo = MockModel()

    def extrair_features_linha_digitavel(self, linha_digitavel: str) -> Dict:
        linha_limpa = linha_digitavel.replace(' ', '').replace('.', '').replace('-', '')
        return {
            'linha_cod_banco': int(linha_limpa[0:3]) if len(linha_limpa) >= 3 else 0,
            'linha_moeda': int(linha_limpa[3:4]) if len(linha_limpa) >= 4 else 9,
            'linha_valor': int(linha_limpa[-10:]) if len(linha_limpa) >= 10 else 0
        }

    def mapear_banco(self, nome_banco: str) -> float:
        if nome_banco in self.mapeamento_bancos:
            return float(self.mapeamento_bancos[nome_banco])
        nome_lower = nome_banco.lower()
        for banco, indice in self.mapeamento_bancos.items():
            if nome_lower in banco.lower() or banco.lower() in nome_lower:
                return float(indice)
        print(f"Banco no mapeado: {nome_banco}")
        return 0.0

    def fazer_predicao(self, dados_boleto: Dict) -> Dict:
        try:
            features_linha = self.extrair_features_linha_digitavel(dados_boleto['linha_digitavel'])
            features = {
                'banco': self.mapear_banco(dados_boleto['banco']),
                'codigoBanco': float(dados_boleto['codigo_banco']),
                'agencia': float(dados_boleto.get('agencia', 0)),
                'valor': float(dados_boleto.get('valor', 0.0)),
                'linha_codBanco': float(features_linha['linha_cod_banco']),
                'linha_moeda': float(features_linha['linha_moeda']),
                'linha_valor': float(features_linha['linha_valor'])
            }
            feature_names = ['banco', 'codigoBanco', 'agencia', 'valor', 'linha_codBanco', 'linha_moeda', 'linha_valor']
            df_features = pd.DataFrame([features])[feature_names]
            
            predicao_array = self.modelo.predict(df_features)
            predicao = int(predicao_array[0])
            probabilidades = self.modelo.predict_proba(df_features)[0]
            
            resultado = "Verdadeiro" if predicao == 1 else "Falso"
            confianca = max(float(probabilidades[0]), float(probabilidades[1]))

            explicacao = self.gerar_explicacao_shap(df_features, predicao, features) if self.explainer else {"explicacao_texto": "Explicao no disponvel."}

            return {
                'resultado': resultado,
                'confianca': confianca,
                'explicacao_shap': explicacao
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'resultado': 'Erro', 'erro': str(e)}

    def gerar_explicacao_shap(self, df_features: pd.DataFrame, predicao: int, features_originais: Dict) -> Dict:
        try:
            shap_values = self.explainer.shap_values(df_features)
            # Para classificacao binaria, shap_values pode ser uma lista de arrays.
            # Se o modelo retorna SHAP values para ambas as classes, pegamos a da classe positiva (indice 1).
            # Se retorna apenas para uma classe (e.g., a positiva), entao shap_values ja e o array.
            if isinstance(shap_values, list) and len(shap_values) > 1:
                shap_values_for_explanation = shap_values[1][0]
            else:
                # Assume que shap_values ja e o array para a classe positiva
                shap_values_for_explanation = shap_values[0]
            
            shap_map = {name: value for name, value in zip(df_features.columns, shap_values_for_explanation)}
            sorted_shap_features = sorted(shap_map.items(), key=lambda item: abs(item[1]), reverse=True)
            
            msgs = []
            if int(features_originais.get("codigoBanco")) != int(features_originais.get("linha_codBanco")):
                msgs.append("O cdigo do banco na linha digitvel no confere com o cdigo informado.")
            if int(features_originais.get("linha_moeda")) != 9:
                msgs.append("O dgito de moeda na linha digitvel est diferente do esperado (deveria ser 9).")
            if abs(float(features_originais.get("valor")) * 100 - float(features_originais.get("linha_valor"))) > 0.01:
                msgs.append("O valor na linha digitvel no confere com o valor informado.")

            for fname, v in sorted_shap_features:
                if abs(v) > 0.05:
                    feature_display_name = fname.replace('_', ' ').capitalize()
                    direction = "negativamente" if v < 0 else "positivamente"
                    impact_word = "aumentando a suspeita" if v < 0 else "reforcando a autenticidade"
                    msgs.append(f"O campo '{feature_display_name}' influenciou {direction} a decisao, {impact_word}.")

            status_text = "VERDADEIRO " if predicao == 1 else "FALSO "
            if not msgs:
                texto_usuario = f"Resultado da anlise: {status_text}. Nenhuma inconsistencia clara foi detectada."
            else:
                texto_usuario = f"Resultado da anlise: {status_text}.\n\nPrincipais motivos detectados:\n- " + "\n- ".join(msgs)

            return {
                "explicacao_texto": texto_usuario
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "explicacao_texto": f"Erro ao gerar explicacao: {str(e)}"
            }
