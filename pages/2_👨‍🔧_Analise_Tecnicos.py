import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from DB import DatabaseConnection

# Configuração da página
st.set_page_config(
    page_title="Análise de Técnicos",
    page_icon="👨‍🔧",
    layout="wide"
)

# Título
st.title("��‍🔧 Análise de Técnicos")

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

# Só mostrar os filtros e gráficos se tiver dados
if not df.empty:
    # Remover valores nulos antes de usar unique() e sort
    tecnicos_unicos = df["TECNICO"].dropna().unique().tolist()
    
    # Filtros adicionais
    tecnicos = st.sidebar.multiselect(
        "👨‍🔧 Técnicos:",
        options=sorted(tecnicos_unicos),
        default=[]
    )

    # Aplicar filtros
    if tecnicos:
        df = df[df["TECNICO"].isin(tecnicos)]

    # Gráficos
    col1, col2 = st.columns(2)

    with col1:
        # Serviços por técnico
        servicos_tecnico = df["TECNICO"].value_counts().reset_index()
        servicos_tecnico.columns = ["Técnico", "Total de Serviços"]
        
        fig = px.bar(
            servicos_tecnico,
            x="Técnico",
            y="Total de Serviços",
            title="Serviços por Técnico"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Status dos serviços por técnico
        status_tecnico = df.groupby(["TECNICO", "STATUS"]).size().reset_index()
        status_tecnico.columns = ["Técnico", "Status", "Total"]
        
        fig = px.bar(
            status_tecnico,
            x="Técnico",
            y="Total",
            color="Status",
            title="Status dos Serviços por Técnico",
            barmode="group"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Métricas
    st.subheader("📊 Métricas")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total de Técnicos", len(df["TECNICO"].unique()))
    
    with col2:
        media_servicos = round(df["TECNICO"].value_counts().mean(), 2)
        st.metric("Média de Serviços por Técnico", media_servicos)
    
    with col3:
        concluidos = len(df[df["STATUS"].str.contains("Concluído", case=False, na=False)])
        st.metric("Total de Serviços Concluídos", concluidos)

else:
    st.warning("⚠️ Nenhum dado encontrado para o período selecionado. Tente ajustar as datas do filtro.")
