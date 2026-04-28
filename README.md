# 📈 Nexus Valuation AI (AutoValuation-LLM)

[cite_start]Uma pipeline *end-to-end* orientada a contratos de dados para a precificação institucional de ativos, combinando modelagem financeira quantitativa e auditoria semântica via Inteligência Artificial[cite: 3, 62].

## 🧠 O Problema
[cite_start]No ambiente de *Debt Capital Markets* e M&A, o processo de avaliação de ativos é frequentemente atrasado pela leitura manual de demonstrações financeiras (DFP/ITR) e vulnerável ao viés humano e erros de planilha (*Fat Finger*). [cite_start]Informações vitais sobre ganhos não-recorrentes ou provisões fiscais muitas vezes passam despercebidas, gerando distorções de *Valuation*[cite: 334, 1160].

## ⚙️ A Solução: Arquitetura Desacoplada
[cite_start]O **Nexus Valuation AI** adota o framework CRISP-DM e opera numa arquitetura assíncrona baseada em Microsserviços e *Data Contracts* (JSON), mitigando riscos operacionais[cite: 7, 30, 62].

### Funcionalidades Core
* [cite_start]**Pipeline ETL Híbrida:** Ingestão de dados estruturados (yfinance / brapi.dev) e armazenamento num Data Warehouse local em SQLite[cite: 785, 928, 929].
* [cite_start]**Roteamento Matemático Inteligente:** O motor determina automaticamente o modelo de precificação com base no setor[cite: 688, 1196, 1201]:
    * [cite_start]*Setor Financeiro:* Modelo de Desconto de Dividendos (DDM de Gordon)[cite: 688].
    * [cite_start]*Indústrias/Serviços:* Fluxo de Caixa Descontado (DCF) com *Fade-In*[cite: 1202].
    * [cite_start]*Commodities:* DCF Cíclico com decaimento severo (*Fade-Out*)[cite: 1198].
* [cite_start]**Auditoria de PDF via LLM:** A IA extrai e analisa o risco semântico das Notas Explicativas reais (usando `pdfplumber`), expurgando eventos não-recorrentes e ajustando o WACC dinamicamente[cite: 1379, 1380, 1383].
* [cite_start]**Trava de Qualidade (Quality Premium):** Ativos que apresentam ROE superior a 20% recebem ajustes automáticos na taxa de crescimento perpétuo ($g$) devido ao seu *Moat* competitivo[cite: 1283, 1292].
* [cite_start]**Governança e Compliance:** Geração automatizada de Laudos de Auditoria (TXT) rastreáveis, respeitando um limite estrito e predefinido de **45.0% de Drawdown Máximo Aceitável**[cite: 84, 156, 381].

## 🛠️ Stack Tecnológico
* **Linguagem:** Python 3
* [cite_start]**Interface:** Streamlit (Terminal Web) & CLI Terminal (Estilo DOS) [cite: 24, 948]
* [cite_start]**Processamento de Dados:** Pandas, SQLite3 [cite: 928]
* [cite_start]**Ingestão e Documentos:** yfinance, requests, pdfplumber [cite: 1379, 1389]
* [cite_start]**Conformidade:** Lógica alinhada com as normas IFRS 13 e CPC 46 (Mensuração do Valor Justo)[cite: 69, 70].