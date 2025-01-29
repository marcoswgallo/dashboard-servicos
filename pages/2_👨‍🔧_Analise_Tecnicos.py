import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from DB import DatabaseConnection

# Configuração da página
st.set_page_config(
    page_title="Análise por Técnico",
    page_icon="👨‍🔧",
    layout="wide"
)

# Título
st.title("👨‍🔧 Análise por Técnico")

# Inicializar conexão com banco
db = DatabaseConnection()

# Filtros na sidebar
st.sidebar.title("🎯 Filtros")

# Datas
col1, col2 = st.sidebar.columns(2)

with col1:
    data_inicio = st.text_input(
        "📅 Data Inicial:",
        value="01/01/2025",
        help="Formato: DD/MM/YYYY"
    )

with col2:
    data_fim = st.text_input(
        "📅 Data Final:",
        value="28/01/2025",
        help="Formato: DD/MM/YYYY"
    )

# Carregar dados
df = db.execute_query(data_inicio, data_fim)

if df is not None and not df.empty:
    # Filtros adicionais
    tecnicos = st.sidebar.multiselect(
        "👨‍🔧 Técnicos:",
        options=sorted(df['TECNICO'].unique().tolist()),
        default=[]
    )

    # Aplicar filtros
    if tecnicos:
        df = df[df['TECNICO'].isin(tecnicos)]

    # Métricas Gerais
    st.subheader("📊 Métricas Gerais")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total de Técnicos", len(df['TECNICO'].unique()))
    
    with col2:
        st.metric("Total de Serviços", len(df))
    
    with col3:
        media_servicos = len(df) / len(df['TECNICO'].unique())
        st.metric("Média de Serviços/Técnico", f"{media_servicos:.1f}")
    
    with col4:
        concluidos = len(df[df['STATUS'].str.contains('Concluído', case=False, na=False)])
        st.metric("Serviços Concluídos", concluidos)

    # Gráficos
    col1, col2 = st.columns(2)

    with col1:
        # Serviços por técnico
        servicos_tecnico = df['TECNICO'].value_counts().reset_index()
        servicos_tecnico.columns = ['Técnico', 'Quantidade']
        
        fig = px.bar(
            servicos_tecnico,
            x='Técnico',
            y='Quantidade',
            title='Serviços por Técnico',
            labels={'Quantidade': 'Quantidade de Serviços'}
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Status por técnico
        status_tecnico = df.groupby(['TECNICO', 'STATUS']).size().reset_index()
        status_tecnico.columns = ['Técnico', 'Status', 'Quantidade']
        
        fig = px.bar(
            status_tecnico,
            x='Técnico',
            y='Quantidade',
            color='Status',
            title='Status dos Serviços por Técnico',
            barmode='group'
        )
        st.plotly_chart(fig, use_container_width=True)

    # Tabela detalhada
    st.subheader("📋 Dados Detalhados")
    st.dataframe(
        df[['DATA_TOA', 'TECNICO', 'CIDADES', 'SERVIÇO', 'STATUS']],
        hide_index=True,
        use_container_width=True
    )

else:
    st.warning("⚠️ Nenhum dado encontrado para o período selecionado. Tente ajustar as datas do filtro.")
