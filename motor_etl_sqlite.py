import sqlite3
import yfinance as yf
from datetime import datetime
import time
import os

NOME_BANCO = "b3_database.db"
TICKERS_ALVO = ["BBAS3", "ABEV3", "WEGE3", "PETR4", "VALE3", "ITUB4", "BBDC4", "EGIE3"]

def inicializar_banco():
    conn = sqlite3.connect(NOME_BANCO)
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS fundamentos') 
    
    cursor.execute('''
        CREATE TABLE fundamentos (
            ticker TEXT PRIMARY KEY, setor TEXT, preco_atual REAL, dy REAL, pl REAL, 
            roe REAL, roa REAL, margem_bruta REAL, margem_ebit REAL, margem_liquida REAL,
            lpa REAL, vpa REAL, psr REAL, ev_ebit REAL, payout REAL, 
            liquidez_corrente REAL, divida_patrimonio REAL, fcf REAL, lucro_liquido REAL, 
            divida_total REAL, caixa_total REAL, acoes_circulacao REAL, market_cap REAL, 
            ultima_atualizacao TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("[OK] Base de dados V9.0 reconstruída com sucesso.")

def buscar_dados(ticker):
    yf_ticker = yf.Ticker(f"{ticker}.SA")
    info = yf_ticker.info
    preco = info.get("currentPrice") or info.get("regularMarketPrice", 0)
    fcf = info.get("freeCashflow")
    if not fcf or fcf <= 0: fcf = info.get("netIncome", 0.0)

    return {
        "ticker": f"{ticker}.SA", "setor": info.get("sector", "Outros"),
        "preco_atual": preco, "dy": info.get("dividendYield", 0.0),
        "pl": info.get("trailingPE", 0.0), "roe": info.get("returnOnEquity", 0.0),
        "roa": info.get("returnOnAssets", 0.0), 
        "margem_bruta": info.get("grossMargins", 0.0),
        "margem_ebit": info.get("operatingMargins", 0.0),
        "margem_liquida": info.get("profitMargins", 0.0),
        "lpa": info.get("trailingEps", 0.0), "vpa": info.get("bookValue", 0.0),
        "psr": info.get("priceToSalesTrailing12Months", 0.0),
        "ev_ebit": info.get("enterpriseToEbitda", 0.0), 
        "payout": info.get("payoutRatio", 0.0),
        "liquidez_corrente": info.get("currentRatio", 0.0),
        "divida_patrimonio": info.get("debtToEquity", 0.0),
        "fcf": fcf, "lucro_liquido": info.get("netIncome", 0.0),
        "divida_total": info.get("totalDebt", 0.0), "caixa_total": info.get("totalCash", 0.0),
        "acoes_circulacao": info.get("sharesOutstanding", 0.0), "market_cap": info.get("marketCap", 0.0)
    }

def atualizar_banco():
    conn = sqlite3.connect(NOME_BANCO)
    cursor = conn.cursor()
    print("A Sincronizar Data Warehouse...")
    for ticker in TICKERS_ALVO:
        try:
            print(f"-> Extraindo {ticker}...")
            d = buscar_dados(ticker)
            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO fundamentos VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                d["ticker"], d["setor"], d["preco_atual"], d["dy"], d["pl"], d["roe"], d["roa"], 
                d["margem_bruta"], d["margem_ebit"], d["margem_liquida"], d["lpa"], d["vpa"], 
                d["psr"], d["ev_ebit"], d["payout"], d["liquidez_corrente"], d["divida_patrimonio"], 
                d["fcf"], d["lucro_liquido"], d["divida_total"], d["caixa_total"], d["acoes_circulacao"], 
                d["market_cap"], agora
            ))
            conn.commit()
            time.sleep(0.5)
        except Exception as e: print(f"[ERRO] {ticker}: {e}")
    conn.close()

if __name__ == "__main__":
    inicializar_banco()
    atualizar_banco()