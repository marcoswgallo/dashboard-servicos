import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
            options=sorted(df['CIDADES'].unique()),
            default=[]
        )
    
    with col2:
        status = st.multiselect(
            "📊 Status:",
            options=sorted(df['STATUS'].unique()),
            default=[]
        )
    
    # Aplicar filtros
    if cidades:
        df = df[df['CIDADES'].isin(cidades)]
    if status:
        df = df[df['STATUS'].isin(status)]
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        valor_total = df['VALOR_TÉCNICO'].sum()
        st.metric(
            "Valor Total",
            f"R$ {valor_total:,.2f}",
            help="Soma total dos valores dos serviços"
        )
    
    with col2:
        valor_medio = df['VALOR_TÉCNICO'].mean()
        st.metric(
            "Valor Médio",
            f"R$ {valor_medio:,.2f}",
            help="Valor médio por serviço"
        )
    
    with col3:
        valor_mediano = df['VALOR_TÉCNICO'].median()
        st.metric(
            "Valor Mediano",
            f"R$ {valor_mediano:,.2f}",
            help="Valor mediano dos serviços"
        )
    
    with col4:
        desvio_padrao = df['VALOR_TÉCNICO'].std()
        st.metric(
            "Desvio Padrão",
            f"R$ {desvio_padrao:,.2f}",
            help="Desvio padrão dos valores"
        )
    
    # Análise temporal
    st.subheader("📈 Análise Temporal")
    
    # Dados diários
    df['Data'] = df['DATA_TOA'].dt.date
    df_diario = df.groupby('Data').agg({
        'VALOR_TÉCNICO': ['sum', 'mean', 'count']
    }).reset_index()
    df_diario.columns = ['Data', 'Valor_Total', 'Valor_Medio', 'Quantidade']
    
    # Gráfico de linha temporal
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_diario['Data'],
        y=df_diario['Valor_Total'],
        name='Valor Total',
        mode='lines+markers'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_diario['Data'],
        y=df_diario['Quantidade'] * df_diario['Valor_Medio'],
        name='Quantidade x Valor Médio',
        mode='lines+markers'
    ))
    
    fig.update_layout(
        title='Evolução Temporal dos Valores',
        xaxis_title='Data',
        yaxis_title='Valor (R$)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Análises por cidade e status
    col1, col2 = st.columns(2)
    
    with col1:
        # Top 10 cidades por valor
        df_cidade = df.groupby('CIDADES').agg({
            'VALOR_TÉCNICO': ['sum', 'count']
        }).reset_index()
        df_cidade.columns = ['Cidade', 'Valor_Total', 'Quantidade']
        
        fig = px.bar(
            df_cidade.nlargest(10, 'Valor_Total'),
            x='Cidade',
            y='Valor_Total',
            title='Top 10 Cidades por Valor Total',
            color='Quantidade',
            labels={'Valor_Total': 'Valor Total (R$)'},
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Distribuição por status
        df_status = df.groupby('STATUS').agg({
            'VALOR_TÉCNICO': ['sum', 'count']
        }).reset_index()
        df_status.columns = ['Status', 'Valor_Total', 'Quantidade']
        
        fig = px.pie(
            df_status,
            values='Valor_Total',
            names='Status',
            title='Distribuição de Valores por Status',
            hover_data=['Quantidade']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Histograma de valores
    st.subheader("📊 Distribuição de Valores")
    
    fig = px.histogram(
        df,
        x='VALOR_TÉCNICO',
        nbins=50,
        title='Distribuição dos Valores dos Serviços',
        labels={'VALOR_TÉCNICO': 'Valor (R$)', 'count': 'Quantidade'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabela detalhada
    with st.expander("📋 Análise Detalhada por Cidade"):
        st.dataframe(
            df_cidade.sort_values('Valor_Total', ascending=False),
            hide_index=True,
            use_container_width=True
        )

else:
    st.warning("Nenhum dado encontrado para o período selecionado.")
