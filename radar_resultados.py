import yfinance as yf
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timezone
import pandas as pd

class RadarDeBalanço:
    def __init__(self, ticker):
        self.ticker = ticker

    def obter_proxima_divulgacao(self):
        """Busca a próxima data de balanço usando o yfinance (Versão Blindada)"""
        try:
            empresa = yf.Ticker(self.ticker)
            datas = empresa.calendar
            
            if datas is not None:
                # Tratamento para Dicionário (Novo padrão do yfinance)
                if isinstance(datas, dict) and 'Earnings Date' in datas and len(datas['Earnings Date']) > 0:
                    proxima_data = datas['Earnings Date'][0]
                # Tratamento para DataFrame (Padrão antigo)
                elif hasattr(datas, 'empty') and not datas.empty and 'Earnings Date' in datas.index:
                    proxima_data = datas.loc['Earnings Date'].iloc[0]
                else:
                    return None
                
                # Conversão segura para Datetime
                if isinstance(proxima_data, datetime):
                    return proxima_data
                elif hasattr(proxima_data, 'to_pydatetime'):
                    return proxima_data.to_pydatetime()
                    
        except Exception as e:
            st.sidebar.warning(f"Aviso do Radar: Não foi possível obter data de evento para {self.ticker}.")
        return None

    def renderizar_cronometro(self):
        data_evento = self.obter_proxima_divulgacao()
        
        if not data_evento:
            st.info("📅 Dados do próximo balanço ainda não agendados oficialmente.")
            return

        hoje = datetime.now(timezone.utc)
        dias_restantes = (data_evento.replace(tzinfo=timezone.utc) - hoje).days

        st.markdown("### 🚨 Radar de Balanço de Resultados")

        if dias_restantes > 0:
            st.warning(f"⏳ Faltam **{dias_restantes} dias** para a divulgação de resultados (Previsto: {data_evento.strftime('%d/%m/%Y')}).")
            
        elif dias_restantes == 0:
            st.error(f"🔥 **É HOJE!** A empresa reporta resultados hoje ({data_evento.strftime('%d/%m/%Y')}).")
            
            ano, mes, dia = data_evento.year, data_evento.month, data_evento.day
            
            codigo_html_js = f"""
            <div style="font-family: Arial, sans-serif; text-align: center; background-color: #ff4b4b; color: white; padding: 20px; border-radius: 10px; margin-top: 10px;">
                <h3 style="margin:0;">TEMPO PARA O EVENTO DE RESULTADOS</h3>
                <div id="countdown" style="font-size: 2em; font-weight: bold; margin-top: 10px;">Carregando cronômetro...</div>
            </div>

            <script>
            var countDownDate = new Date("{ano}-{mes:02d}-{dia:02d}T18:00:00").getTime();

            var x = setInterval(function() {{
                var now = new Date().getTime();
                var distance = countDownDate - now;

                var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                var seconds = Math.floor((distance % (1000 * 60)) / 1000);

                if (distance < 0) {{
                    clearInterval(x);
                    document.getElementById("countdown").innerHTML = "MERCADO FECHADO - BALANÇO EM DIVULGAÇÃO!";
                }} else {{
                    document.getElementById("countdown").innerHTML = hours + "h " + minutes + "m " + seconds + "s ";
                }}
            }}, 1000);
            </script>
            """
            components.html(codigo_html_js, height=150)
        else:
            st.success(f"✅ O balanço do trimestre já foi divulgado em {data_evento.strftime('%d/%m/%Y')}. Os dados base já estão atualizados.")