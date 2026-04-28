import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

class DashboardFundamentos:
    def __init__(self, ticker):
        self.ticker = ticker
        self.empresa = yf.Ticker(ticker)
        self.info = self.empresa.info

    def renderizar_kpis(self):
        """Gera os cards de indicadores (Múltiplos, Rentabilidade e Risco)"""
        st.markdown("### 📊 Raio-X Fundamentalista (Fechamento Atual)")
        
        # Proteção caso a API não retorne algum dado
        def formatar(valor, formato="{:.2f}", percentual=False):
            if valor is None or valor == "N/A": return "N/D"
            if percentual: return f"{valor * 100:.2f}%"
            return formato.format(valor)

        # LINHA 1: VALUATION
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("P/L (Preço/Lucro)", formatar(self.info.get('trailingPE')))
        with col2:
            st.metric("P/VP (Preço/VPA)", formatar(self.info.get('priceToBook')))
        with col3:
            st.metric("EV / EBITDA", formatar(self.info.get('enterpriseToEbitda')))
        with col4:
            st.metric("Dividend Yield", formatar(self.info.get('dividendYield'), percentual=True))

        # LINHA 2: RENTABILIDADE E RISCO
        st.markdown("<br>", unsafe_allow_html=True) # Espaçamento
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("ROE (Retorno s/ PL)", formatar(self.info.get('returnOnEquity'), percentual=True))
        with col2:
            st.metric("Margem Líquida", formatar(self.info.get('profitMargins'), percentual=True))
        with col3:
            # Cálculo manual de Dívida Líquida / EBITDA se não vier pronto
            divida_total = self.info.get('totalDebt', 0)
            caixa = self.info.get('totalCash', 0)
            ebitda = self.info.get('ebitda', 1) # Evita divisão por zero
            div_liq_ebitda = (divida_total - caixa) / ebitda if ebitda else None
            
            # Alerta visual para risco de crédito alto
            if div_liq_ebitda and div_liq_ebitda > 3.0:
                st.metric("Dívida Líq / EBITDA", formatar(div_liq_ebitda), "⚠️ Alavancada", delta_color="inverse")
            else:
                st.metric("Dívida Líq / EBITDA", formatar(div_liq_ebitda))
        with col4:
            st.metric("Liquidez Corrente", formatar(self.info.get('currentRatio')))

    def renderizar_graficos(self):
        """Gera os gráficos históricos de Receita vs Lucro"""
        st.markdown("### 📈 Evolução Histórica (DRE)")
        
        try:
            dre = self.empresa.financials
            if dre is not None and not dre.empty:
                # Transpõe e limpa os dados
                dre = dre.T
                # Pegamos apenas Receita Total e Lucro Líquido
                if 'Total Revenue' in dre.columns and 'Net Income' in dre.columns:
                    df_grafico = dre[['Total Revenue', 'Net Income']].dropna()
                    df_grafico.index = pd.to_datetime(df_grafico.index).year
                    df_grafico = df_grafico.sort_index()

                    # Criando um gráfico de barras duplas institucional com Plotly
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=df_grafico.index,
                        y=df_grafico['Total Revenue'],
                        name='Receita Total',
                        marker_color='#1f77b4' # Azul corporativo
                    ))
                    fig.add_trace(go.Bar(
                        x=df_grafico.index,
                        y=df_grafico['Net Income'],
                        name='Lucro Líquido',
                        marker_color='#2ca02c' # Verde lucro
                    ))

                    fig.update_layout(
                        barmode='group',
                        title='Receita vs Lucro Líquido (Últimos Exercícios)',
                        xaxis_title='Ano Fiscal',
                        yaxis_title='Valor (R$)',
                        legend_title='Métrica',
                        height=400,
                        margin=dict(l=0, r=0, t=40, b=0)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Dados de DRE insuficientes para gerar o gráfico histórico.")
        except Exception as e:
            st.error(f"Erro ao carregar gráficos: {e}")