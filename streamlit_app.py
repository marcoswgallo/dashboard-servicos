import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Serviços",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        .element-container {
            margin-bottom: 0.5rem;
        }
        .stAlert {
            padding: 0.5rem;
            margin-bottom: 0.5rem;
        }
        .stDateInput {
            margin-bottom: 0.5rem;
        }
        /* Cores personalizadas */
        :root {
            --primary-color: #1f77b4;
            --secondary-color: #ff7f0e;
            --background-color: #f0f2f6;
        }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.title("🔧 Dashboard de Serviços")

# Descrição
st.markdown("""
Este dashboard apresenta uma análise detalhada dos serviços técnicos realizados.
Utilize a navegação lateral para acessar diferentes visualizações e análises.
""")

# Métricas principais
col1, col2, col3 = st.columns(3)

# Placeholder para métricas - serão atualizadas quando tivermos os dados
with col1:
    st.metric(
        label="Total de Serviços",
        value="Carregando...",
        delta=None,
        help="Número total de serviços no período selecionado"
    )

with col2:
    st.metric(
        label="Média Diária",
        value="Carregando...",
        delta=None,
        help="Média de serviços por dia no período"
    )

with col3:
    st.metric(
        label="Valor Total",
        value="Carregando...",
        delta=None,
        help="Valor total dos serviços no período"
    )

# Informações adicionais
st.markdown("""
### 📌 Navegação
- **Mapa de Serviços**: Visualize a distribuição geográfica dos serviços
- **Detalhamento Técnico**: Análise detalhada por técnico
- **Análise Financeira**: Visão financeira dos serviços

### 🔄 Atualizações
Os dados são atualizados automaticamente a cada carregamento.
""")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Desenvolvido com ❤️ pela equipe de Analytics</p>
</div>
""", unsafe_allow_html=True)
