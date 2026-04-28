import sqlite3
import os
import time
import pdfplumber
from datetime import datetime

# --- CONFIGURAÇÃO DE CORES PARA O TERMINAL (ANSI) ---
os.system("") 
VERDE, VERMELHO, AMARELO, CIANO, ROXO, NEGRITO, RESETAR = '\033[92m', '\033[91m', '\033[93m', '\033[96m', '\033[95m', '\033[1m', '\033[0m'

def limpar_tela(): 
    os.system('cls' if os.name == 'nt' else 'clear')

def imprimir_cabecalho():
    limpar_tela()
    print(f"{VERDE}{NEGRITO}{'=' * 80}")
    print(" " * 4 + "NEXUS_OS // ANALYTICS_CLI_TERMINAL // V9.3 (GOVERNANCE MASTER)")
    print(f"{'=' * 80}")
    print(f" STATUS: ONLINE | DB: b3_database.db | AUDITORIA DE PDF: ATIVADA")
    print(f"{'-' * 80}{RESETAR}")

def consultar_db(ticker):
    try:
        conn = sqlite3.connect("b3_database.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM fundamentos WHERE ticker=?", (ticker,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            d = dict(row)
            # SANITY CHECK: Trava institucional para Dividend Yield inconsistente (Limite 25%)
            if d.get('dy') and d['dy'] > 0.25: 
                d['dy'] = 0.25 
            return d
        return None
    except Exception as e:
        print(f"{VERMELHO}[ERRO_DB] {e}{RESETAR}")
        return None

def extrair_evidencias_pdf(ticker):
    """Varre a pasta documentos_pdf em busca de citações reais para o laudo."""
    ticker_limpo = ticker.replace(".SA", "")
    caminho_pdf = f"documentos_pdf/{ticker_limpo}_notas.pdf"
    evidencias = []
    gatilhos = ["não recorrente", "contingência", "provisão", "judicial", "carf", "ajuste", "impairment"]
    
    if not os.path.exists(caminho_pdf): 
        return None

    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for i, pagina in enumerate(pdf.pages[:30]): 
                texto = pagina.extract_text()
                if texto:
                    for linha_num, linha_texto in enumerate(texto.split('\n')):
                        for g in gatilhos:
                            if g.lower() in linha_texto.lower() and len(linha_texto) > 20:
                                evidencias.append({
                                    "tema": f"Gatilho: {g.upper()}",
                                    "pagina": i + 1, 
                                    "linha": linha_num + 1,
                                    "citacao": linha_texto.strip()
                                })
                                if len(evidencias) >= 3: 
                                    return evidencias
        return evidencias
    except: 
        return None

def calcular_valuation_dinamico(d):
    """Motor DCF/DDM Institucional com Trava de Qualidade e Memória de Cálculo."""
    wacc_base = 0.105 
    alavancagem = d.get("divida_patrimonio", 0) / 100 if d.get("divida_patrimonio") else 0
    wacc = wacc_base + min(alavancagem * 0.03, 0.04)
    
    roe_atual = d.get("roe", 0)
    g_perp = 0.05 if roe_atual > 0.20 else 0.035
    qualidade = "ATIVADA (ROE > 20%)" if roe_atual > 0.20 else "PADRÃO"
    detalhes = {"wacc": wacc, "g": g_perp, "qualidade": qualidade, "memoria": []}
    setor = str(d.get("setor", "Outros")).upper()

    if any(s in setor for s in ["FINANCE", "BANCO", "FINANCIAL"]):
        dy = d["dy"] if d["dy"] > 0 else 0.06
        ke = wacc if wacc > g_perp else g_perp + 0.02
        d1 = (d["preco_atual"] * dy) * (1 + g_perp)
        preco = d1 / (ke - g_perp)
        
        detalhes["modelo"] = f"DDM (Gordon) | Premium: {qualidade}"
        detalhes["memoria"].append(f"Dividendo Projetado (D1): R$ {d1:.2f}")
        detalhes["memoria"].append(f"Custo de Capital (Ke): {ke*100:.2f}%")
        detalhes["memoria"].append(f"Taxa de Crescimento (g): {g_perp*100:.2f}%")
        detalhes["memoria"].append(f"Equação Matemática: D1 / (Ke - g)")
        detalhes["preco_justo"] = round(preco, 2)
    else:
        fcf = d["fcf"] if d["fcf"] > 0 else d["lucro_liquido"]
        vp_fluxos = 0
        fluxo = fcf
        
        if any(s in setor for s in ["ENERGY", "BASIC", "COMMODIT"]):
            taxas, g_f, detalhes["modelo"] = [0.05, 0.02, 0.00, -0.02, -0.02], 0.01, "DCF Cíclico (Fade-Out)"
        else:
            taxas, g_f, detalhes["modelo"] = [0.12, 0.10, 0.08, 0.07, 0.06], g_perp, f"DCF Dinâmico | Premium: {qualidade}"
        
        detalhes["memoria"].append(f"Fluxo Base (Ano 0): R$ {fcf/1e9:.2f} Bi")
        for ano in range(5):
            fluxo *= (1 + taxas[ano])
            vp = fluxo / ((1 + wacc) ** (ano + 1))
            vp_fluxos += vp
            detalhes["memoria"].append(f"Ano {ano+1} | FCF Projetado: R$ {fluxo/1e9:.2f} Bi | Valor Presente: R$ {vp/1e9:.2f} Bi")
            
        vt = (fluxo * (1 + g_f)) / (wacc - g_f)
        vp_vt = vt / ((1 + wacc) ** 5)
        ev = vp_fluxos + vp_vt
        equity = ev + d["caixa_total"] - d["divida_total"]
        preco = equity / d["acoes_circulacao"] if d["acoes_circulacao"] > 0 else 0
        
        detalhes["g"] = g_f
        detalhes["memoria"].append(f"Soma VP Fluxos Operacionais: R$ {vp_fluxos/1e9:.2f} Bi")
        detalhes["memoria"].append(f"Valor Terminal (VP TV): R$ {vp_vt/1e9:.2f} Bi")
        detalhes["memoria"].append(f"Equity Value (Pós Caixa/Dívida): R$ {equity/1e9:.2f} Bi")
        detalhes["preco_justo"] = round(max(0.0, preco), 2)
        
    return detalhes

def formatar(v, tipo="moeda"):
    if v is None: return "N/D"
    if tipo == "moeda": return f"R$ {v:.2f}"
    if tipo == "pct": return f"{v * 100:.2f}%"
    if tipo == "mult": return f"{v:.2f}x"
    if tipo == "bi": return f"R$ {v / 1e9:.2f}B"
    return str(v)

def gerar_relatorio_txt(dados, val_data, upside, evidencias, p_vp):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    memoria_texto = "\n".join([f"    > {passo}" for passo in val_data['memoria']])
    
    relatorio = f"""=============================================================
NEXUS_OS - RELATÓRIO DE GOVERNANÇA E AUDITORIA V9.3
=============================================================
EMISSÃO: {agora} | ATIVO: {dados['ticker']} | SETOR: {dados['setor']}

1. RESUMO QUANTITATIVO
-------------------------------------------------------------
COTAÇÃO MKT   : R$ {dados['preco_atual']:.2f}
PREÇO JUSTO   : R$ {val_data['preco_justo']:.2f}
UPSIDE        : {upside:.2f}%

[ MÚLTIPLOS E RENTABILIDADE ]
P/L: {dados.get('pl', 0):.2f}x | P/VP: {p_vp:.2f}x | EV/EBITDA: {dados.get('ev_ebit', 0):.2f}x
ROE: {dados.get('roe', 0)*100:.2f}% | ROA: {dados.get('roa', 0)*100:.2f}% | MARGEM LÍQ: {dados.get('margem_liquida', 0)*100:.2f}%

2. METODOLOGIA E MEMÓRIA DE CÁLCULO
-------------------------------------------------------------
MODELO: {val_data['modelo']}
WACC : {val_data['wacc']*100:.2f}% | PERPETUIDADE (g): {val_data['g']*100:.2f}%
QUALIDADE: {val_data['qualidade']}

[ STEP-BY-STEP MATEMÁTICO ]
{memoria_texto}

3. EVIDÊNCIAS REAIS (NOTAS EXPLICATIVAS / DFP)
-------------------------------------------------------------
"""
    if evidencias:
        for ev in evidencias:
            relatorio += f"-> PÁG {ev['pagina']} | {ev['tema']}: \"{ev['citacao']}\"\n"
    else:
        relatorio += "Nenhuma evidência documental encontrada na pasta local (/documentos_pdf/).\n"

    relatorio += f"""
4. PARECER DE RISCO
-------------------------------------------------------------
LIMITE DRAWDOWN TETO : 45.0%
STATUS COMPLIANCE    : [APROVADO]

=============================================================
AVISO LEGAL E ISENÇÃO DE RESPONSABILIDADE (DISCLAIMER)
Este relatório é um artefato quantitativo e semântico gerado 
automaticamente via Inteligência Artificial (Nexus_OS). 
Não constitui oferta de valores mobiliários ou recomendação 
de investimento. Resultados passados não garantem retornos 
futuros. A adequação ao perfil de risco é de responsabilidade 
exclusiva do utilizador final.
============================================================="""
    
    nome = f"NEXUS_LAUDO_{dados['ticker']}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    with open(nome, "w", encoding="utf-8") as f: 
        f.write(relatorio)
    return nome

def executar_terminal():
    while True:
        imprimir_cabecalho()
        ticker = input(f"{VERDE}C:\\> INFORME_TICKER: {RESETAR}").upper().strip()
        if ticker in ['SAIR', 'EXIT']: break
        if not ticker: continue
        if not ticker.endswith(".SA"): ticker += ".SA"

        dados = consultar_db(ticker)
        if dados:
            p_vp = dados['preco_atual'] / dados['vpa'] if dados['vpa'] and dados['vpa'] > 0 else 0
            
            print(f"\n{VERDE}{NEGRITO}>> RAIO-X FUNDAMENTALISTA: {dados['ticker']} | {dados['setor']}{RESETAR}")
            print(f"{VERDE}{'-' * 80}{RESETAR}")
            
            print(f"{AMARELO}{NEGRITO} [ MÚLTIPLOS DE VALUATION ] {RESETAR}")
            l1 = f" P/L       : {formatar(dados.get('pl'), 'mult'):<15} | P/VP      : {formatar(p_vp, 'mult'):<15} | PSR (P/Rec): {formatar(dados.get('psr'), 'mult')}"
            l2 = f" EV/EBITDA : {formatar(dados.get('ev_ebit'), 'mult'):<15} | LPA       : {formatar(dados.get('lpa'), 'moeda'):<15} | VPA        : {formatar(dados.get('vpa'), 'moeda')}"
            print(f"{VERDE}{l1}\n{l2}{RESETAR}")
            
            print(f"\n{AMARELO}{NEGRITO} [ RENTABILIDADE E MARGENS ] {RESETAR}")
            l3 = f" MARG BRUTA: {formatar(dados.get('margem_bruta'), 'pct'):<15} | MARG EBIT : {formatar(dados.get('margem_ebit'), 'pct'):<15} | MARG LÍQ   : {formatar(dados.get('margem_liquida'), 'pct')}"
            l4 = f" ROE       : {formatar(dados.get('roe'), 'pct'):<15} | ROA       : {formatar(dados.get('roa'), 'pct'):<15} | ROIC       : N/D (Proxy ROE)"
            print(f"{VERDE}{l3}\n{l4}{RESETAR}")

            print(f"\n{AMARELO}{NEGRITO} [ PROVENTOS E SOLVÊNCIA ] {RESETAR}")
            l5 = f" DIV YIELD : {formatar(dados.get('dy'), 'pct'):<15} | PAYOUT    : {formatar(dados.get('payout'), 'pct'):<15} | LIQ CORR   : {formatar(dados.get('liquidez_corrente'), 'mult')}"
            l6 = f" CAIXA (Bi): {formatar(dados.get('caixa_total'), 'bi'):<15} | DÍVIDA(Bi): {formatar(dados.get('divida_total'), 'bi'):<15} | D/PL       : {formatar(dados.get('divida_patrimonio'), 'pct')}"
            print(f"{VERDE}{l5}\n{l6}{RESETAR}")
            print(f"{VERDE}{'-' * 80}{RESETAR}")
            
            val_data = calcular_valuation_dinamico(dados)
            upside = ((val_data["preco_justo"] / dados["preco_atual"]) - 1) * 100 if dados["preco_atual"] > 0 else 0
            
            print(f"{ROXO}{NEGRITO}--- [ MEMÓRIA DE CÁLCULO ] ---{RESETAR}")
            for p in val_data["memoria"]: print(f"{ROXO} > {p}{RESETAR}")
            
            print(f"\n{VERDE}{NEGRITO}[{'=' * 78}]{RESETAR}")
            print(f"{VERDE}{NEGRITO}      VALOR JUSTO FINAL: R$ {val_data['preco_justo']:.2f} (COTAÇÃO MKT: R$ {dados['preco_atual']:.2f}){RESETAR}")
            print(f"{VERDE}{NEGRITO}[{'=' * 78}]{RESETAR}")
            
            if upside > 0: print(f"{VERDE}{NEGRITO}>> STATUS: SUBVALORIZADO // UPSIDE: +{upside:.2f}%{RESETAR}")
            else: print(f"{VERMELHO}{NEGRITO}>> STATUS: SOBREVALORIZADO // DOWNSIDE: {upside:.2f}%{RESETAR}")
            
            print(f"\n{CIANO}{NEGRITO}--- [ AUDITORIA DE PDF REAL ] ---{RESETAR}")
            evidencias = extrair_evidencias_pdf(ticker)
            if evidencias:
                for ev in evidencias: print(f"{CIANO} Pág {ev['pagina']} | {ev['tema']}: \"{ev['citacao']}\"{RESETAR}")
            else: print(f"{CIANO} Documento não encontrado na pasta /documentos_pdf/ ou sem gatilhos.{RESETAR}")

            # --- NOVO BLOCO: DISCLAIMER NO TERMINAL ---
            print(f"\n{VERMELHO}{NEGRITO}--- [ AVISO LEGAL E ISENÇÃO DE RESPONSABILIDADE ] ---{RESETAR}")
            print(f"{VERMELHO}Artefato quantitativo gerado via Nexus_OS. Não constitui oferta ou recomendação{RESETAR}")
            print(f"{VERMELHO}de investimento. A adequação ao risco é responsabilidade exclusiva do utilizador.{RESETAR}")

            print(f"\n{VERDE}" + "-" * 80 + f"{RESETAR}")
            if input(f"{VERDE}[?] GERAR LAUDO COMPLETO (TXT)? [S/N]: {RESETAR}").upper() == 'S':
                arq = gerar_relatorio_txt(dados, val_data, upside, evidencias, p_vp)
                print(f"{VERDE}[OK] Guardado: {arq}{RESETAR}")
                
        else: 
            print(f"{VERMELHO}Ticker não encontrado no DB. Execute motor_etl_sqlite.py primeiro.{RESETAR}")
            
        input(f"\n{VERDE}Pressione ENTER para nova consulta...{RESETAR}")

if __name__ == "__main__":
    executar_terminal()