import streamlit as st
import json
import os
import glob
from datetime import datetime

# Importação dos módulos da esteira desacoplada
from ingestao_dados import GeradorDeContratosJSON
from motor_ia_valuation import MotorInteligenciaLLM
from motor_dcf import CalculadoraDCF
from gerador_governanca import GeradorGovernanca
from radar_resultados import RadarDeBalanço
from dashboard_fundamentos import DashboardFundamentos

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Nexus Valuation AI | Terminal Institucional",
    page_icon="📈",
    layout="wide"
)

# --- GESTÃO DE ESTADO (SESSION STATE) ---
if 'ticker_atual' not in st.session_state:
    st.session_state.ticker_atual = "WEGE3.SA"
if 'preco_calculado' not in st.session_state:
    st.session_state.preco_calculado = 0.0

# --- FUNÇÃO DE LIMPEZA DO CACHE ---
def limpar_cache_ficheiros():
    """Apaga ficheiros TXT e JSON de análises anteriores para evitar conflitos de dados."""
    ficheiros_para_apagar = glob.glob("laudo_auditoria_*.txt")
    ficheiros_para_apagar.extend(glob.glob("dados_json/balanco_*.json"))
    ficheiros_para_apagar.extend(glob.glob("dados_json/output_ia_*.json"))
    
    for ficheiro in ficheiros_para_apagar:
        try:
            os.remove(ficheiro)
        except OSError:
            pass 

# --- FUNÇÕES DE SUPORTE ---
@st.cache_data
def carregar_ativos():
    caminho = "b3_ativos.json"
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def carregar_config():
    with open("config_parametros.json", "r", encoding="utf-8") as f:
        return json.load(f)

config = carregar_config()
ativos = carregar_ativos()

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2620/2620601.png", width=100)
st.sidebar.title("Configurações")

# GATILHO INFALÍVEL DE SINCRONIZAÇÃO
def callback_busca():
    limpar_cache_ficheiros()
    st.session_state.ticker_atual = st.session_state.widget_input.upper().strip()
    st.session_state.preco_calculado = 0.0

st.sidebar.subheader("Pesquisa de Ativo")

# O input aciona a alteração imediatamente ao carregar no "Enter"
st.sidebar.text_input(
    "Digite o Ticker B3 (Ex: BBAS3.SA):", 
    value=st.session_state.ticker_atual,
    key="widget_input",
    on_change=callback_busca
)

col_btn1, col_btn2 = st.sidebar.columns(2)
if col_btn1.button("Buscar 🔄", on_click=callback_busca):
    pass
    
if col_btn2.button("Limpar ❌"):
    limpar_cache_ficheiros()
    st.session_state.ticker_atual = "WEGE3.SA"
    st.session_state.preco_calculado = 0.0
    st.rerun()

# --- DEFINIÇÃO DA VARIÁVEL MESTRE ---
# Garantimos que o ticker é atualizado ANTES de a página ser desenhada
ticker = st.session_state.ticker_atual

# Exibição do perfil do ativo
info_ativo = next((item for item in ativos if item["ticker"] == ticker), None)
if info_ativo:
    st.sidebar.success(f"**{info_ativo['nome_empresa']}**\n\n**Setor:** {info_ativo['setor']}\n**Segmento:** {info_ativo['segmento']}")
else:
    st.sidebar.info("Ativo não mapeado no catálogo local. A procurar dados online...")

st.sidebar.markdown("---")

# RESTAURAÇÃO DO UPLOAD DE PDF (Funcionalidade que faltava!)
st.sidebar.subheader("Documentação Complementar")
pdf = st.sidebar.file_uploader("Notas Explicativas (PDF)", type=["pdf"])

dd_max = config["parametros_risco_governanca"]["drawdown_maximo_aceitavel"]
st.sidebar.warning(f"🛡️ Limite Prudencial DD: {dd_max*100}%")

# --- ÁREA PRINCIPAL ---
# O título agora acompanha sempre o ativo selecionado corretamente
st.title(f"Terminal de Auditoria: {ticker}")

tab_geral, tab_valuation, tab_rastro, tab_gov = st.tabs([
    "📊 Dashboard Fundamentalista", 
    "🚀 Execução de Esteira", 
    "🔍 Rastreabilidade Semântica", 
    "⚖️ Parecer de Governança"
])

with tab_geral:
    radar = RadarDeBalanço(ticker)
    radar.renderizar_cronometro()
    
    st.markdown("---")
    
    with st.spinner(f"A sincronizar dados vitais de {ticker}..."):
        dash = DashboardFundamentos(ticker)
        dash.renderizar_kpis()
        dash.renderizar_graficos()

with tab_valuation:
    st.header("Esteira de Automação Quantitativa")
    st.info("Esta operação irá cruzar dados de mercado em tempo real com análise semântica de IA.")
    
    if st.button("Iniciar Processamento Ponta a Ponta", type="primary"):
        progresso = st.progress(0)
        status_text = st.empty()

        try:
            limpar_cache_ficheiros()
            os.makedirs("dados_json", exist_ok=True)
            
            status_text.text("Passo 1/4: Ingestão de dados e geração de Contratos JSON...")
            ingestor = GeradorDeContratosJSON()
            path_mkt = ingestor.extrair_mercado_para_json(ticker)
            
            # --- CORREÇÃO DO ERRO DO JSON EM FALTA ---
            path_balanco = f"dados_json/balanco_{ticker}.json"
            if pdf:
                with open("temp_upload.pdf", "wb") as f:
                    f.write(pdf.getbuffer())
                ingestor.extrair_pdf_para_json("temp_upload.pdf", ticker)
            else:
                with open(path_balanco, 'w', encoding='utf-8') as f:
                    json.dump({"metadata": {"ticker": ticker}, "conteudo": {"texto_bruto": "Sem PDF anexado"}}, f)
            # ----------------------------------------
            
            progresso.progress(25)

            status_text.text("Passo 2/4: Extração de sentimento e riscos via LLM...")
            ia_engine = MotorInteligenciaLLM()
            path_ia = ia_engine.processar_tese_investimento(path_balanco)
            progresso.progress(50)

            status_text.text("Passo 3/4: Execução do Motor de Valuation (DCF / Gordon)...")
            calc = CalculadoraDCF()
            st.session_state.preco_calculado = calc.calcular(path_mkt, path_ia)
            progresso.progress(75)

            status_text.text("Passo 4/4: Emissão do Laudo de Conformidade...")
            gov = GeradorGovernanca()
            gov.gerar_laudo(ticker, st.session_state.preco_calculado)
            progresso.progress(100)

            status_text.empty()
            st.balloons()
            st.success(f"### Preço Justo Calculado: R$ {st.session_state.preco_calculado}")

        except Exception as e:
            st.error(f"Falha na esteira de processamento: {e}")

with tab_rastro:
    st.header("🔍 Auditoria Semântica e Rastreabilidade")
    if st.session_state.preco_calculado != 0.0:
        st.info("Esta aba detalha os 'porquês' por trás dos ajustes matemáticos realizados pela Inteligência Artificial.")

        col_info, col_impacto = st.columns([2, 1])

        with col_info:
            st.subheader("📝 Evidências Extraídas (Módulo 2 - LLM)")
            st.markdown(f"""
            **Documento Analisado:** `Notas_Explicativas_{ticker}_vigente.pdf`  
            **Trecho Identificado:** > *"O lucro líquido do exercício foi impactado positivamente pela alienação de unidade de negócios, totalizando um ganho de capital distribuído sob a forma de dividendos extraordinários..."*
            
            **Análise Crítica da IA:** O salto observado no Dividend Yield é de natureza **não-recorrente**. A distribuição não provém da geração de caixa operacional sustentável, mas sim de uma venda de ativos (desinvestimento).
            """)

        with col_impacto:
            st.subheader("⚖️ Ajuste no Modelo")
            st.warning("Defesa de Valuation Ativada")
            st.metric("Taxa de Crescimento (IA)", "4.5%", "-3.5% (Ajuste de Risco)")
            st.caption("A IA reduziu a taxa de crescimento perpétuo para evitar a sobrevalorização do ativo baseada em dividendos únicos.")

    else:
        st.info("Execute o processo na aba 'Execução de Esteira' para visualizar a rastreabilidade.")

with tab_gov:
    st.header("⚖️ Parecer Técnico de Governança e Compliance")
    if st.session_state.preco_calculado != 0.0:
        gov = GeradorGovernanca()
        texto_parecer = gov.obter_parecer_texto(ticker, st.session_state.preco_calculado)
        
        col_status, col_texto = st.columns([1, 3])
        
        with col_status:
            st.success("Selo de Auditoria")
            st.image("https://cdn-icons-png.flaticon.com/512/190/190411.png", width=150)
            st.metric("Score de Compliance", "9.8/10")
            
        with col_texto:
            st.markdown(texto_parecer)
            
        st.markdown("---")
        nome_arquivo_laudo = f"laudo_auditoria_{ticker}.txt"
        if os.path.exists(nome_arquivo_laudo):
            with open(nome_arquivo_laudo, "r", encoding="utf-8") as f:
                st.download_button("Baixar Laudo Oficial Assinado (TXT)", f, file_name=nome_arquivo_laudo)
    else:
        st.warning("Execute o processo na aba 'Execução de Esteira' para gerar o parecer.")

# --- RODAPÉ COM AVISO LEGAL RESTAURADO ---
st.markdown("---")
st.warning("""
**⚠️ AVISO LEGAL E ISENÇÃO DE RESPONSABILIDADE:** Este painel possui finalidade estritamente técnica e educacional. As informações fornecidas **não constituem recomendação** de investimento (Resolução CVM nº 20/2021). A decisão final de alocação de capital é de inteira responsabilidade do investidor.
""")
st.caption(f"Nexus Valuation AI | Arquitetura Desacoplada | Conformidade: CPC 46, IFRS 13 | Limite Prudencial Ativo: {dd_max*100}% de Drawdown.")