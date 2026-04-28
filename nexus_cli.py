import streamlit as st
import sqlite3

# --- CONFIGURAÇÃO VISUAL TERMINAL V3 (NEON & BOLD) ---
st.set_page_config(page_title="NEXUS TERMINAL", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    
    /* Global: Verde Neon e Negrito */
    * { 
        color: #00FF41 !important; 
        font-family: 'Courier New', monospace !important; 
        font-weight: 900 !important; 
    }
    
    header, footer { visibility: hidden; }
    
    /* Títulos e Fontes Gigantes */
    h1 { font-size: 50px !important; border-bottom: 3px solid #00FF41; }
    h2 { font-size: 35px !important; margin-top: 30px; }
    
    /* Estilização das Métricas */
    div[data-testid="metric-container"] {
        background-color: #050505;
        border: 3px solid #00FF41;
        padding: 20px;
        border-radius: 0px;
        box-shadow: 5px 5px 0px #004400;
    }
    
    div[data-testid="stMetricValue"] { font-size: 32px !important; }
    div[data-testid="stMetricLabel"] { font-size: 20px !important; text-transform: uppercase; }

    /* Input da Linha de Comando */
    .stTextInput input {
        background-color: #000000 !important;
        border: 3px solid #00FF41 !important;
        font-size: 25px !important;
        height: 60px;
    }
    
    .stAlert { background-color: #001100 !important; border: 2px solid #00FF41 !important; }
    </style>
""", unsafe_allow_html=True)

def consultar_db(ticker):
    conn = sqlite3.connect("b3_database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM fundamentos WHERE ticker=?", (ticker,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def calcular_valuation(d):
    # Premissas institucionais
    wacc, g = 0.11, 0.04
    if d["setor"] in ["Financeiro", "Bancos"]:
        dy = d["dy"] if d["dy"] > 0 else 0.06
        return round(((d["preco_atual"] * dy) * (1 + g)) / (wacc - g), 2)
    else:
        # DCF simplificado para Indústrias
        fcf = d["fcf"] if d["fcf"] > 0 else d["lucro_liquido"]
        vt = (fcf * (1 + g)) / (wacc - g)
        equity = (fcf * 5) + vt + d["caixa_total"] - d["divida_total"]
        return round(max(0.0, equity / d["acoes_circulacao"]), 2)

# --- INTERFACE ---
st.markdown("<h1>NEXUS_OS // ANALYTICS_TERMINAL_V3</h1>", unsafe_allow_html=True)
st.markdown("ESTADO: SISTEMA_OPERACIONAL_ATIVO // DB: b3_database.db")

with st.form("cmd_line"):
    ticker = st.text_input("C:\> INFORME_TICKER_PARA_AUDITORIA:", value="BBAS3.SA").upper().strip()
    executar = st.form_submit_button("EXECUTAR_PROCESSO")

if executar:
    dados = consultar_db(ticker)
    if dados:
        st.markdown(f"## >> RESULTADOS_DA_QUERY: {dados['ticker']}")
        
        # LINHA 1: VALUATION
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("COTAÇÃO_ATUAL", f"R$ {dados['preco_atual']:.2f}")
        c2.metric("P/L_ATUAL", f"{dados['pl']:.2f}")
        c3.metric("LPA (LUCRO/AÇÃO)", f"R$ {dados['lpa']:.2f}")
        c4.metric("VPA (VALOR/PATIVO)", f"R$ {dados['vpa']:.2f}")

        # LINHA 2: PROVENTOS E RENTABILIDADE
        c5, c6, c7, c8 = st.columns(4)
        c5.metric("DIVIDEND_YIELD", f"{(dados['dy']*100):.2f}%")
        c6.metric("PAYOUT_RATIO", f"{(dados['payout']*100):.2f}%")
        c7.metric("MARGEM_LÍQUIDA", f"{(dados['margem_liquida']*100):.2f}%")
        c8.metric("ROE_CONTÁBIL", f"{(dados['roe']*100):.2f}%")

        # LINHA 3: SOLVÊNCIA
        c9, c10, c11, c12 = st.columns(4)
        c9.metric("LIQUIDEZ_CORR", f"{dados['liquidez_corrente']:.2f}")
        c10.metric("DÍVIDA_SOBRE_PL", f"{dados['divida_patrimonio']:.2f}%")
        c11.metric("CAIXA_TOTAL_BI", f"R$ {dados['caixa_total']/1e9:.2f}B")
        c12.metric("DÍVIDA_TOTAL_BI", f"R$ {dados['divida_total']/1e9:.2f}B")

        st.markdown("<hr>", unsafe_allow_html=True)
        
        valor_justo = calcular_valuation(dados)
        upside = ((valor_justo / dados["preco_atual"]) - 1) * 100
        
        st.markdown(f"<h1>VALOR JUSTO CALCULADO: R$ {valor_justo}</h1>", unsafe_allow_html=True)
        
        if upside > 0:
            st.success(f"DECISÃO: ATIVO SUBVALORIZADO // POTENCIAL: +{upside:.2f}%")
        else:
            st.error(f"DECISÃO: ATIVO SOBREVALORIZADO // POTENCIAL: {upside:.2f}%")
            
    else:
        st.error("[ERRO_CRÍTICO] TICKER NÃO ENCONTRADO NO BANCO DE DADOS LOCAL.")

st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("Nexus Valuation AI | Terminal de Auditoria | Limite Prudencial: 45,0% de Drawdown.")