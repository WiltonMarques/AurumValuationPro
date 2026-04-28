import yfinance as yf
import json
import os
import requests
import PyPDF2
from datetime import datetime  # <--- AQUI ESTÁ A CORREÇÃO QUE FALTAVA!

class GeradorDeContratosJSON:
    def __init__(self, config_path="config_parametros.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Token da Brapi (Substitua pelo seu token real para produção)
        self.brapi_token = "SEU_TOKEN_AQUI" 
        self.diretorio = self.config["sistema"]["diretorio_saida_json"]
        os.makedirs(self.diretorio, exist_ok=True)

    def buscar_fundamentos_brapi(self, ticker):
        """Busca indicadores fundamentais de alta qualidade via Brapi API."""
        # Remove o .SA se o utilizador enviou com o sufixo
        ticker_limpo = ticker.replace(".SA", "")
        url = f"https://brapi.dev/api/quote/{ticker_limpo}"
        params = {
            "token": self.brapi_token,
            "modules": "fundamentalData"
        }
        
        try:
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                dados = res.json()
                if "results" in dados:
                    return dados["results"][0]
        except Exception as e:
            print(f"Erro ao aceder à Brapi: {e}")
        return None

    def extrair_mercado_para_json(self, ticker):
        """Gera o contrato JSON híbrido (yfinance + Brapi)."""
        print(f"A iniciar extração de dados para {ticker}...")
        
        # 1. Dados de Preço e Mercado (yfinance)
        ticker_yf = yf.Ticker(ticker)
        yf_info = ticker_yf.info
        
        # 2. Dados Fundamentais de Qualidade (Brapi)
        brapi_data = self.buscar_fundamentos_brapi(ticker)
        
        # 3. Consolidação no Contrato JSON (Padrão Nexus)
        contrato = {
            "metadata": {
                "ticker": ticker,
                "data_extracao": datetime.now().isoformat(), # AQUI ACONTECIA O ERRO
                "fontes": ["yfinance", "brapi.dev"]
            },
            "dados_fundamentais": {
                "preco_atual": yf_info.get("currentPrice") or yf_info.get("regularMarketPrice"),
                "setor": yf_info.get("sector"),
                "segmento": yf_info.get("industry"),
                
                # Prioriza dados da Brapi para indicadores críticos
                "trailingPE": brapi_data.get("fundamentalData", {}).get("pe") if brapi_data else yf_info.get("trailingPE"),
                "dividendYield": brapi_data.get("fundamentalData", {}).get("dividendYield") if brapi_data else yf_info.get("dividendYield"),
                "returnOnEquity": brapi_data.get("fundamentalData", {}).get("roe") if brapi_data else yf_info.get("returnOnEquity"),
                "freeCashflow": yf_info.get("freeCashflow"),
                "operatingCashflow": yf_info.get("operatingCashflow"),
                "netIncome": yf_info.get("netIncome"),
                "totalDebt": yf_info.get("totalDebt"),
                "totalCash": yf_info.get("totalCash"),
                "sharesOutstanding": yf_info.get("sharesOutstanding"),
                "marketCap": yf_info.get("marketCap")
            }
        }

        caminho_final = os.path.join(self.diretorio, f"mercado_{ticker}.json")
        with open(caminho_final, 'w', encoding='utf-8') as f:
            json.dump(contrato, f, indent=4, ensure_ascii=False)
        
        return caminho_final

    def extrair_pdf_para_json(self, caminho_pdf, ticker):
        """Converte PDF de RI em texto bruto para o Módulo 2 (IA)."""
        texto_completo = ""
        try:
            with open(caminho_pdf, "rb") as f:
                leitor = PyPDF2.PdfReader(f)
                limite = self.config["parametros_ingestao"]["limite_paginas_pdf"]
                for i in range(min(len(leitor.pages), limite)):
                    texto_completo += leitor.pages[i].extract_text()
        except Exception as e:
            texto_completo = f"Erro na extração do PDF: {e}"

        json_pdf = {
            "metadata": {"ticker": ticker, "documento": caminho_pdf},
            "conteudo": {"texto_bruto": texto_completo}
        }
        
        caminho_saida = os.path.join(self.diretorio, f"balanco_{ticker}.json")
        with open(caminho_saida, 'w', encoding='utf-8') as f:
            json.dump(json_pdf, f, indent=4, ensure_ascii=False)
        
        return caminho_saida