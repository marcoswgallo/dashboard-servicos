# Dashboard de Serviços Técnicos

Dashboard interativo para análise e visualização de serviços técnicos, construído com Streamlit.

## 🌟 Funcionalidades

- 📊 **Dashboard Principal**: Visão geral com métricas principais
- 🗺️ **Mapa de Serviços**: Visualização geográfica dos serviços
- 👨‍🔧 **Análise por Técnico**: Métricas detalhadas por técnico
- 💰 **Análise Financeira**: Análise detalhada dos valores

## 🚀 Como Executar Localmente

1. Clone o repositório:
```bash
git clone [URL_DO_SEU_REPOSITORIO]
cd ProjetoBasic
```

2. Crie um ambiente virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
- Crie um arquivo `.streamlit/secrets.toml` com:
```toml
[postgres]
url = "sua_url_do_banco_neon"
```

5. Execute a aplicação:
```bash
streamlit run streamlit_app.py
```

## 🔒 Variáveis de Ambiente

Para executar este projeto, você precisará das seguintes variáveis de ambiente no Streamlit Cloud:

- `postgres.url`: URL de conexão com o banco Neon PostgreSQL

## 📦 Estrutura do Projeto

```
ProjetoBasic/
├── .streamlit/
│   └── secrets.toml
├── pages/
│   ├── 1_🗺️_Mapa_Servicos.py
│   ├── 2_👨‍🔧_Analise_Tecnicos.py
│   └── 3_💰_Analise_Financeira.py
├── DB.py
├── import_excel.py
├── streamlit_app.py
├── requirements.txt
└── README.md
```

## 🛠️ Tecnologias Utilizadas

- [Streamlit](https://streamlit.io/)
- [Pandas](https://pandas.pydata.org/)
- [Plotly](https://plotly.com/)
- [Folium](https://python-visualization.github.io/folium/)
- [PostgreSQL](https://www.postgresql.org/)
- [SQLAlchemy](https://www.sqlalchemy.org/)

## 📈 Deploy

Este projeto está configurado para deploy automático no Streamlit Cloud.
Para fazer o deploy:

1. Faça o push do código para o GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Configure as variáveis de ambiente necessárias
4. Deploy!
