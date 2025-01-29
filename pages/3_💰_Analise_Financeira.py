import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from DB import DatabaseConnection

# Configuração da página
st.set_page_config(
    page_title="Análise Financeira",
    page_icon="💰",
    layout="wide"
)

# Título
st.title("💰 Análise Financeira")

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
    col1, col2 = st.sidebar.columns(2)

    with col1:
        cidades = st.multiselect(
            "🏙️ Cidades:",
            options=sorted(df['CIDADES'].unique().tolist()),
            default=[]
        )

    with col2:
        tecnicos = st.multiselect(
            "👨‍🔧 Técnicos:",
            options=sorted(df['TECNICO'].unique().tolist()),
            default=[]
        )

    # Aplicar filtros
    if cidades:
        df = df[df['CIDADES'].isin(cidades)]
    if tecnicos:
        df = df[df['TECNICO'].isin(tecnicos)]

    # Métricas Gerais
    st.subheader("📊 Métricas Gerais")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_servicos = len(df)
        st.metric("Total de Serviços", total_servicos)

    with col2:
        total_tecnicos = len(df['TECNICO'].unique())
        st.metric("Total de Técnicos", total_tecnicos)

    with col3:
        media_servicos = total_servicos / total_tecnicos if total_tecnicos > 0 else 0
        st.metric("Média Serviços/Técnico", f"{media_servicos:.1f}")

    with col4:
        concluidos = len(df[df['STATUS'].str.contains('Concluído', case=False, na=False)])
        st.metric("Serviços Concluídos", concluidos)

    # Gráficos
    col1, col2 = st.columns(2)

    with col1:
        # Serviços por cidade
        servicos_cidade = df['CIDADES'].value_counts().reset_index()
        servicos_cidade.columns = ['Cidade', 'Quantidade']
        
        fig = px.bar(
            servicos_cidade,
            x='Cidade',
            y='Quantidade',
            title='Serviços por Cidade',
            labels={'Quantidade': 'Quantidade de Serviços'}
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Serviços por status
        status_servicos = df['STATUS'].value_counts().reset_index()
        status_servicos.columns = ['Status', 'Quantidade']
        
        fig = px.pie(
            status_servicos,
            values='Quantidade',
            names='Status',
            title='Distribuição por Status'
        )
        st.plotly_chart(fig, use_container_width=True)

    # Análise temporal
    st.subheader("📈 Análise Temporal")
    
    # Serviços por data
    df['Data'] = df['DATA_TOA'].dt.date
    servicos_data = df.groupby('Data').size().reset_index()
    servicos_data.columns = ['Data', 'Quantidade']
    
    fig = px.line(
        servicos_data,
        x='Data',
        y='Quantidade',
        title='Serviços por Data',
        labels={'Quantidade': 'Quantidade de Serviços'}
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tabela detalhada
    st.subheader("📋 Dados Detalhados")
    st.dataframe(
        df[['DATA_TOA', 'TECNICO', 'CIDADES', 'SERVIÇO', 'STATUS']].sort_values('DATA_TOA', ascending=False),
        hide_index=True,
        use_container_width=True
    )

else:
    st.warning("⚠️ Nenhum dado encontrado para o período selecionado. Tente ajustar as datas do filtro.")
