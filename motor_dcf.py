import json

class CalculadoraDCF:
    def __init__(self, config_path="config_parametros.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def calcular(self, path_mercado, path_ia):
        """
        Motor Híbrido: Escolhe entre DCF (Empresas Comuns) e DDM (Bancos)
        Com sistema de resiliência e cascata de dados (Fallbacks)
        """
        try:
            # 1. Carregar Contratos de Dados
            with open(path_mercado, 'r', encoding='utf-8') as f:
                dados_mercado = json.load(f)
            
            with open(path_ia, 'r', encoding='utf-8') as f:
                dados_ia = json.load(f)

            # 2. Extrair Variáveis Principais
            info = dados_mercado.get("dados_fundamentais", {})
            setor = info.get("setor", "Outros")
            preco_atual = info.get("preco_atual", 0)
            
            # Ajuste de Risco vindo da IA (Alpha)
            ajuste_ia = dados_ia.get("ajuste_risco_sugerido", 0)
            
            # Parâmetros Base do JSON
            wacc = self.config["parametros_valuation"]["wacc_padrao"]
            g_perpetuidade = self.config["parametros_valuation"]["taxa_crescimento_perpetuidade"]
            g_ajustado = max(0.01, g_perpetuidade - ajuste_ia) # Nunca menor que 1%

            # ---------------------------------------------------------
            # ROTEAMENTO: MODELO DE GORDON PARA BANCOS E SEGURADORAS
            # ---------------------------------------------------------
            if setor in ["Financeiro", "Financial Services", "Bancos"]:
                
                dy = info.get("dividendYield")
                if not dy or dy == 0:
                    dy = 0.06 # Fallback seguro de 6% se a API falhar
                
                dividendo_anual_atual = preco_atual * dy
                dividendo_esperado = dividendo_anual_atual * (1 + g_ajustado)
                
                ke = wacc 
                if ke <= g_ajustado:
                    ke = g_ajustado + 0.02 
                    
                preco_justo = dividendo_esperado / (ke - g_ajustado)
                return round(preco_justo, 2)

            # ---------------------------------------------------------
            # ROTEAMENTO: DCF PARA EMPRESAS COMUNS (Ex: WEGE3)
            # ---------------------------------------------------------
            else:
                # Tenta o Free Cash Flow primário
                fcf = info.get("freeCashflow")
                
                # CASCATA DE FALLBACKS (A Mágica da Resiliência)
                if not fcf or fcf <= 0:
                    # 1ª Tentativa de Salvação: Fluxo Operacional
                    fcf = info.get("operatingCashflow") 
                    
                if not fcf or fcf <= 0:
                    # 2ª Tentativa de Salvação: Lucro Líquido
                    fcf = info.get("netIncomeToCommon", info.get("netIncome"))
                    
                # Se após todas as tentativas continuar vazio ou negativo, aborta com zero
                if not fcf or fcf <= 0:
                    return 0.0

                # Tratamento seguro para Ações, Dívida e Caixa
                acoes_em_circulacao = info.get("sharesOutstanding")
                if not acoes_em_circulacao or acoes_em_circulacao <= 0:
                    acoes_em_circulacao = 1 # Evita erro de divisão por zero

                divida_total = info.get("totalDebt") or 0
                caixa_total = info.get("totalCash") or 0

                # Projeção de 5 anos
                taxa_crescimento = self.config["parametros_valuation"]["taxa_crescimento_base_setorial"]
                valor_presente_fluxos = 0
                fluxo_projetado = fcf

                for ano in range(1, 6):
                    fluxo_projetado *= (1 + taxa_crescimento)
                    valor_presente_fluxos += fluxo_projetado / ((1 + wacc) ** ano)

                # Valor Terminal (Perpetuidade)
                valor_terminal = (fluxo_projetado * (1 + g_ajustado)) / (wacc - g_ajustado)
                vp_valor_terminal = valor_terminal / ((1 + wacc) ** 5)

                # Enterprise Value e Equity Value
                enterprise_value = valor_presente_fluxos + vp_valor_terminal
                equity_value = enterprise_value + caixa_total - divida_total

                preco_justo = equity_value / acoes_em_circulacao
                return round(preco_justo, 2)

        except Exception as e:
            print(f"Erro crítico no motor matemático: {e}")
            return 0.0