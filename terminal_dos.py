import streamlit as st
import sqlite3

# --- CONFIGURAÇÃO VISUAL HACKER/DOS ---
st.set_page_config(page_title="Nexus DOS Terminal", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #00FF41; font-family: 'Courier New', Courier, monospace; }
    * { color: #00FF41 !important; font-family: 'Courier New', Courier, monospace !important; font-weight: bold !important; }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    h1 { font-size: 40px !important; text-shadow: 2px 2px #005500; }
    h2 { font-size: 30px !important; border-bottom: 2px solid #00FF41; padding-bottom: 10px; }
    h3 { font-size: 22px !important; color: #00FF41 !important; }
    
    .stTextInput input { background-color: #000000 !important; border: 2px solid #00FF41 !important; font-size: 22px !important; }
    
    /* Caixas das Métricas */
    div[data-testid="metric-container"] {
        background-color: #050505;
        border: 2px solid #00FF41;
        padding: 15px;
        border-radius: 3px;
        margin-bottom: 15px;
        box-shadow: 2px 2px 0px #006600;
    }
    div[data-testid="stMetricValue"] { font-size: 24px !important; }
    div[data-testid="stMetricLabel"] { font-size: 16px !important; }
    .stAlert { background-color: #001100 !important; border: 1px solid #00FF41 !important; }
    hr { border-top: 1px dashed #00FF41; }
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE BASE DE DADOS ---
def consultar_ativo(ticker):
    try:
        conn = sqlite3.connect("b3_database.db")
        # Forçamos o retorno em formato de dicionário para facilitar a leitura
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM fundamentos WHERE ticker=?", (ticker,))
        linha = cursor.fetchone()
        conn.close()
        return dict(linha) if linha else None
    except Exception as e:
        st.error(f"[ERRO DE SISTEMA] {e}")
        return None

def calcular_valor_justo_local(dados):
    # Parâmetros ajustados para valores mais realistas face à taxa de juros do Brasil
    wacc = 0.11 # Aumentado de 0.09 para 0.11
    g = 0.04    # Reduzido de 0.05 para 0.04
    
    if dados["setor"] in ["Financeiro", "Financial Services", "Bancos"]:
        dy = dados["dy"] if dados["dy"] > 0 else 0.06
        div_esperado = (dados["preco_atual"] * dy) * (1 + g)
        ke = wacc if wacc > g else g + 0.02
        return round(div_esperado / (ke - g), 2)
    else:
        fcf = dados["fcf"] if dados["fcf"] > 0 else 1000000000
        acoes = dados["acoes_circulacao"] if dados["acoes_circulacao"] > 0 else 1000000000
        vp_fluxos = 0
        fluxo = fcf
        for ano in range(1, 6):
            fluxo *= 1.10
            vp_fluxos += fluxo / ((1 + wacc) ** ano)
        vt = (fluxo * (1 + g)) / (wacc - g)
        vp_vt = vt / ((1 + wacc) ** 5)
        equity = vp_fluxos + vp_vt + dados["caixa_total"] - dados["divida_total"]
        return round(max(0.0, equity / acoes), 2)

# --- INTERFACE DO TERMINAL ---
st.markdown("<h1>NEXUS_OS // ANALYTICS_TERMINAL // V3.2</h1>", unsafe_allow_html=True)
st.markdown("STATUS: ONLINE | DATA_SOURCE: LOCAL_SQLITE_DB")
st.markdown("<hr>", unsafe_allow_html=True)

with st.form("terminal_input"):
    ticker_input = st.text_input("C:\> INPUT_TICKER_ID:", placeholder="EX: ABEV3.SA").upper().strip()
    submit = st.form_submit_button("EXECUTE_QUERY")

if submit and ticker_input:
    dados = consultar_ativo(ticker_input)
    
    if dados:
        st.markdown(f"### >> SINAL ENCONTRADO: {dados['ticker']} | SETOR: {dados['setor']}")
        st.markdown(f"ÚLTIMA ATUALIZAÇÃO DA BASE: {dados['ultima_atualizacao']}")
        
        # --- GRELHA DE INDICADORES (GRID) ---
        # LINHA 1: VALUATION BÁSICO
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("COTAÇÃO MKT", f"R$ {dados['preco_atual']:.2f}")
        c2.metric("P/L", f"{dados['pl']:.2f}")
        c3.metric("LPA", f"R$ {dados['lpa']:.2f}")
        c4.metric("VPA", f"R$ {dados['vpa']:.2f}")
        
        # LINHA 2: DIVIDENDOS E RENTABILIDADE
        c5, c6, c7, c8 = st.columns(4)
        c5.metric("DIVIDEND YIELD", f"{(dados['dy'] * 100 if dados['dy'] else 0):.2f}%")
        c6.metric("PAYOUT RATIO", f"{(dados['payout'] * 100 if dados['payout'] else 0):.2f}%")
        c7.metric("MARGEM LÍQUIDA", f"{(dados['margem_liquida'] * 100 if dados['margem_liquida'] else 0):.2f}%")
        c8.metric("ROE", f"{(dados['roe'] * 100 if dados['roe'] else 0):.2f}%")
        
        # LINHA 3: SAÚDE FINANCEIRA E CAIXA
        c9, c10, c11, c12 = st.columns(4)
        c9.metric("LIQUIDEZ CORRENTE", f"{dados['liquidez_corrente']:.2f}" if dados['liquidez_corrente'] else "N/A")
        
        # Dívida/PL no YFinance geralmente vem em percentagem absoluta (ex: 3.82 = 3.82%)
        div_pat = dados['divida_patrimonio'] if dados['divida_patrimonio'] else 0
        c10.metric("DÍVIDA / PL", f"{div_pat:.2f}%")
        
        # Apresentar valores absolutos em Bilhões (B)
        caixa_bi = dados['caixa_total'] / 1e9 if dados['caixa_total'] else 0
        c11.metric("CAIXA TOTAL", f"R$ {caixa_bi:.2f} B")
        
        divida_bi = dados['divida_total'] / 1e9 if dados['divida_total'] else 0
        c12.metric("DÍVIDA TOTAL", f"R$ {divida_bi:.2f} B")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### >> A EXECUTAR ALGORITMO DE VALUATION (CPC 46 / IFRS 13)...")
        
        preco_justo = calcular_valor_justo_local(dados)
        upside = ((preco_justo / dados["preco_atual"]) - 1) * 100 if dados["preco_atual"] > 0 else 0
        
        st.markdown(f"<h2>VALOR JUSTO (TARGET): R$ {preco_justo}</h2>", unsafe_allow_html=True)
        
        if upside > 0:
            st.success(f">> ATIVO SUBVALORIZADO. POTENCIAL DE UPSIDE: +{upside:.2f}%")
        else:
            st.error(f">> ATIVO SOBREVALORIZADO. RISCO DE DOWNSIDE: {upside:.2f}%")
            
    else:
        st.error(f"[ACESSO NEGADO] TICKER '{ticker_input}' NÃO LOCALIZADO NO DATA WAREHOUSE.")
        st.info("Execute 'python motor_etl_sqlite.py' para sincronizar o mercado.")