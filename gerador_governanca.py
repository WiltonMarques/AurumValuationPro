import json
from datetime import datetime

class GeradorGovernanca:
    def __init__(self, config_path="config_parametros.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def obter_parecer_texto(self, ticker, preco, drawdown_estimado=0.35):
        """Gera o parecer técnico formatado para exibição na aba de Governança."""
        dd_max = self.config["parametros_risco_governanca"]["drawdown_maximo_aceitavel"]
        normas = ", ".join(self.config["parametros_risco_governanca"]["normas_auditoria"])
        
        aprovado = drawdown_estimado <= dd_max
        status = "✅ APROVADO" if aprovado else "❌ REJEITADO"
        
        parecer = f"""
        ## PARECER TÉCNICO DE CONFORMIDADE
        **ATIVO:** {ticker} | **DATA DE EMISSÃO:** {datetime.now().strftime("%d/%m/%Y %H:%M")}
        
        ### 1. STATUS DE AUDITORIA: {status}
        
        ### 2. ANÁLISE PRUDENCIAL DE RISCO
        - **Drawdown Estimado (Cenário Estressado):** {drawdown_estimado*100:.2f}%
        - **Limite Máximo Aceitável (Policy):** {dd_max*100:.2f}%
        - **Veredito:** {"Operação dentro dos limites de apetite a risco." if aprovado else "Operação excede o risco máximo tolerado pela instituição."}
        
        ### 3. FUNDAMENTAÇÃO NORMATIVA
        A metodologia aplicada observa estritamente:
        - **CPC 46:** Mensuração do Valor Justo por fluxo de caixa descontado.
        - **IFRS 13:** Hierarquia de valor justo e dados de mercado.
        - **Marco Legal da IA:** Garantia de explicabilidade semântica e segregação lógica.
        
        ### 4. CONCLUSÃO DO AUDITOR
        O Preço Justo calculado de **R$ {preco}** é o resultado de uma esteira desacoplada, 
        onde a Inteligência Artificial atuou exclusivamente na identificação de eventos 
        não-recorrentes, protegendo a base de cálculo contra distorções de curto prazo.
        """
        return parecer

    def gerar_laudo(self, ticker, preco):
        """Gera e salva o laudo técnico em arquivo .txt para auditoria externa."""
        dd_max = self.config["parametros_risco_governanca"]["drawdown_maximo_aceitavel"]
        normas = ", ".join(self.config["parametros_risco_governanca"]["normas_auditoria"])
        
        laudo_texto = f"""===========================================================
LAUDO TÉCNICO DE VALUATION - NEXUS VALUATION AI
===========================================================
EMISSÃO: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
ATIVO: {ticker}
PREÇO JUSTO: R$ {preco}
-----------------------------------------------------------
GOVERNANÇA E RISCO:
- Limite Prudencial de Drawdown: {dd_max*100}%
- Normas de Referência: {normas}
-----------------------------------------------------------
ISENÇÃO DE RESPONSABILIDADE FINANCEIRA:
Este documento é um artefato de processamento de dados e 
análise semântica. Não representa oferta de valores 
mobiliários ou recomendação de investimento. Resultados 
passados não garantem retornos futuros.
==========================================================="""
        
        nome_arquivo = f"laudo_auditoria_{ticker}.txt"
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            f.write(laudo_texto)
        return nome_arquivo