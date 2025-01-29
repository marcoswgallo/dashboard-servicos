import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
        options=sorted(df['TECNICO'].unique()),
        default=[]
    )
    
    # Aplicar filtros
    if tecnicos:
        df = df[df['TECNICO'].isin(tecnicos)]
    
    # Análises por técnico
    df_tecnico = df.groupby('TECNICO').agg({
        'VALOR_TÉCNICO': ['count', 'sum', 'mean'],
        'CIDADES': 'nunique',
        'STATUS': lambda x: (x == 'Concluído').sum() / len(x) * 100
    }).reset_index()
    
    # Renomear colunas
    df_tecnico.columns = [
        'Técnico', 'Total_Servicos', 'Valor_Total', 
        'Valor_Medio', 'Cidades_Atendidas', 'Taxa_Conclusao'
    ]
    
    # Métricas principais
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Técnicos Ativos",
            f"{len(df_tecnico):,}",
            help="Número de técnicos que realizaram serviços no período"
        )
    
    with col2:
        media_servicos = df_tecnico['Total_Servicos'].mean()
        st.metric(
            "Média de Serviços/Técnico",
            f"{media_servicos:,.1f}",
            help="Média de serviços por técnico no período"
        )
    
    with col3:
        media_valor = df_tecnico['Valor_Total'].mean()
        st.metric(
            "Média de Valor/Técnico",
            f"R$ {media_valor:,.2f}",
            help="Média de valor total por técnico"
        )
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        # Top 10 técnicos por número de serviços
        fig = px.bar(
            df_tecnico.nlargest(10, 'Total_Servicos'),
            x='Técnico',
            y='Total_Servicos',
            title='Top 10 Técnicos por Número de Serviços',
            labels={'Total_Servicos': 'Total de Serviços'},
            color='Total_Servicos',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Top 10 técnicos por valor total
        fig = px.bar(
            df_tecnico.nlargest(10, 'Valor_Total'),
            x='Técnico',
            y='Valor_Total',
            title='Top 10 Técnicos por Valor Total',
            labels={'Valor_Total': 'Valor Total (R$)'},
            color='Valor_Total',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Análise de desempenho
    st.subheader("📊 Análise de Desempenho")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Scatter plot: Serviços x Valor Médio
        fig = px.scatter(
            df_tecnico,
            x='Total_Servicos',
            y='Valor_Medio',
            title='Relação entre Número de Serviços e Valor Médio',
            labels={
                'Total_Servicos': 'Total de Serviços',
                'Valor_Medio': 'Valor Médio (R$)'
            },
            hover_data=['Técnico', 'Taxa_Conclusao'],
            color='Taxa_Conclusao',
            color_continuous_scale='RdYlGn',
            size='Cidades_Atendidas'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Taxa de conclusão por técnico
        fig = px.bar(
            df_tecnico.sort_values('Taxa_Conclusao', ascending=False),
            x='Técnico',
            y='Taxa_Conclusao',
            title='Taxa de Conclusão por Técnico',
            labels={'Taxa_Conclusao': 'Taxa de Conclusão (%)'},
            color='Taxa_Conclusao',
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabela detalhada
    with st.expander("📋 Dados Detalhados por Técnico"):
        st.dataframe(
            df_tecnico.sort_values('Total_Servicos', ascending=False),
            hide_index=True,
            use_container_width=True
        )

else:
    st.warning("Nenhum dado encontrado para o período selecionado.")
