import streamlit as st
import pandas as pd
from DB import DatabaseConnection
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(
    page_title="Detalhamento por Técnico",
    page_icon="👨‍🔧",
    layout="wide"
)

# Estilo CSS personalizado
st.markdown("""
    <style>
    .stMetric {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .dataframe {
        font-size: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.title("👨‍🔧 Detalhamento por Técnico")

# Filtros
with st.container():
    st.markdown("### 🎯 Filtros")
    
    col1, col2, col3 = st.columns([2,2,1])
    
    with col1:
        dias = st.slider(
            "📅 Período de análise (dias):",
            min_value=1,
            max_value=90,
            value=30,
            help="Filtrar dados dos últimos X dias"
        )

    # Calcular data limite
    data_limite = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
    
    # Carregar dados
    db = DatabaseConnection()
    df = db.execute_query(data_limite)
    
    if df is not None:
        # Métricas gerais
        total_tecnicos = df['TECNICO'].nunique()
        media_servicos = df.groupby('TECNICO').size().mean()
        total_servicos = len(df)
        
        # Cards com métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Técnicos", f"{total_tecnicos:,.0f}")
        with col2:
            st.metric("Média de Serviços por Técnico", f"{media_servicos:,.1f}")
        with col3:
            st.metric("Total de Serviços", f"{total_servicos:,.0f}")
            
        # Análise por técnico
        st.markdown("### 📊 Análise por Técnico")
        
        # Tabela de detalhamento
        df_tecnico = df.groupby('TECNICO').agg({
            'OS': 'count',
            'VALOR_TÉCNICO': 'sum',
            'DESLOCAMENTO': lambda x: pd.to_timedelta(x).mean()
        }).reset_index()
        
        df_tecnico.columns = ['Técnico', 'Total Serviços', 'Valor Total', 'Média Deslocamento']
        df_tecnico = df_tecnico.sort_values('Total Serviços', ascending=False)
        
        # Gráfico de barras
        fig = px.bar(
            df_tecnico,
            x='Técnico',
            y='Total Serviços',
            title='Serviços por Técnico',
            color='Total Serviços',
            color_continuous_scale='Reds'
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela detalhada
        st.markdown("### 📋 Detalhamento")
        st.dataframe(
            df_tecnico.style.format({
                'Total Serviços': '{:,.0f}',
                'Valor Total': 'R$ {:,.2f}',
                'Média Deslocamento': lambda x: str(x).split()[-1]
            }),
            use_container_width=True
        )
        
        # Análise de eficiência
        st.markdown("### 🎯 Análise de Eficiência")
        
        # Calcular métricas de eficiência
        df_eficiencia = df.groupby('TECNICO').agg({
            'OS': 'count',
            'VALOR_TÉCNICO': 'mean',
            'DESLOCAMENTO': lambda x: pd.to_timedelta(x).mean()
        }).reset_index()
        
        df_eficiencia.columns = ['Técnico', 'Quantidade Serviços', 'Valor Médio', 'Tempo Médio Deslocamento']
        
        # Scatter plot
        fig = px.scatter(
            df_eficiencia,
            x='Tempo Médio Deslocamento',
            y='Valor Médio',
            size='Quantidade Serviços',
            hover_name='Técnico',
            title='Eficiência dos Técnicos (Valor vs. Tempo de Deslocamento)',
            labels={
                'Tempo Médio Deslocamento': 'Tempo Médio de Deslocamento',
                'Valor Médio': 'Valor Médio por Serviço (R$)'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.error("Não foi possível carregar os dados. Por favor, verifique a conexão com o banco de dados.")
