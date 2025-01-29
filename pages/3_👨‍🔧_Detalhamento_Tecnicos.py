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
    .metric-row {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

def convert_time_to_minutes(time_str):
    """Converte string de tempo (HH:MM) para minutos."""
    try:
        if pd.isna(time_str):
            return 0
        hours, minutes = map(int, str(time_str).split(':'))
        return hours * 60 + minutes
    except:
        return 0

def format_minutes(minutes):
    """Formata minutos para HH:MM."""
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours:02d}:{mins:02d}"

# Título principal
st.title("👨‍🔧 Detalhamento por Técnico")

# Filtros
with st.container():
    st.markdown("### 🎯 Filtros")
    
    col1, col2 = st.columns([2,2])
    
    with col1:
        dias = st.slider(
            "📅 Período de análise (dias):",
            min_value=1,
            max_value=90,
            value=30,
            help="Filtrar dados dos últimos X dias"
        )
    
    with col2:
        min_servicos = st.slider(
            "🔄 Mínimo de serviços:",
            min_value=1,
            max_value=50,
            value=5,
            help="Filtrar técnicos com pelo menos X serviços"
        )

    # Calcular data limite
    data_limite = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
    
    # Carregar dados
    db = DatabaseConnection()
    df = db.execute_query(data_limite)
    
    if df is not None:
        # Converter DESLOCAMENTO para minutos
        df['DESLOCAMENTO_MIN'] = df['DESLOCAMENTO'].apply(convert_time_to_minutes)
        
        # Métricas gerais
        total_tecnicos = df['TECNICO'].nunique()
        media_servicos = df.groupby('TECNICO').size().mean()
        total_servicos = len(df)
        valor_total = df['VALOR_TÉCNICO'].sum()
        
        # Cards com métricas
        st.markdown('<div class="metric-row">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("👥 Total de Técnicos", f"{total_tecnicos:,.0f}")
        with col2:
            st.metric("📊 Média de Serviços", f"{media_servicos:,.1f}")
        with col3:
            st.metric("🔄 Total de Serviços", f"{total_servicos:,.0f}")
        with col4:
            st.metric("💰 Valor Total", f"R$ {valor_total:,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
            
        # Análise por técnico
        st.markdown("### 📊 Análise por Técnico")
        
        # Tabela de detalhamento
        df_tecnico = df.groupby('TECNICO').agg({
            'OS': 'count',
            'VALOR_TÉCNICO': ['sum', 'mean'],
            'DESLOCAMENTO_MIN': ['mean', 'sum'],
            'BASE': 'first'
        }).reset_index()
        
        # Renomear colunas
        df_tecnico.columns = ['Técnico', 'Total Serviços', 'Valor Total', 'Valor Médio', 
                            'Média Deslocamento', 'Total Deslocamento', 'Base']
        
        # Filtrar por mínimo de serviços
        df_tecnico = df_tecnico[df_tecnico['Total Serviços'] >= min_servicos]
        df_tecnico = df_tecnico.sort_values('Total Serviços', ascending=False)
        
        # Formatar tempos
        df_tecnico['Média Deslocamento'] = df_tecnico['Média Deslocamento'].apply(format_minutes)
        df_tecnico['Total Deslocamento'] = df_tecnico['Total Deslocamento'].apply(format_minutes)
        
        # Gráficos lado a lado
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de barras - Top 10 por volume
            fig1 = px.bar(
                df_tecnico.head(10),
                x='Técnico',
                y='Total Serviços',
                title='Top 10 Técnicos por Volume de Serviços',
                color='Total Serviços',
                color_continuous_scale='Reds'
            )
            fig1.update_layout(showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)
            
        with col2:
            # Gráfico de barras - Top 10 por valor
            fig2 = px.bar(
                df_tecnico.sort_values('Valor Total', ascending=False).head(10),
                x='Técnico',
                y='Valor Total',
                title='Top 10 Técnicos por Valor Total',
                color='Valor Total',
                color_continuous_scale='Greens'
            )
            fig2.update_layout(showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
        
        # Tabela detalhada
        st.markdown("### 📋 Detalhamento Completo")
        st.dataframe(
            df_tecnico.style.format({
                'Total Serviços': '{:,.0f}',
                'Valor Total': 'R$ {:,.2f}',
                'Valor Médio': 'R$ {:,.2f}'
            }),
            use_container_width=True
        )
        
        # Análise por base
        st.markdown("### 📍 Análise por Base")
        df_base = df_tecnico.groupby('Base').agg({
            'Técnico': 'count',
            'Total Serviços': 'sum',
            'Valor Total': 'sum'
        }).reset_index()
        
        df_base.columns = ['Base', 'Total Técnicos', 'Total Serviços', 'Valor Total']
        
        # Gráfico de pizza
        fig3 = px.pie(
            df_base,
            values='Total Serviços',
            names='Base',
            title='Distribuição de Serviços por Base',
            hole=0.4
        )
        st.plotly_chart(fig3, use_container_width=True)
        
        # Tabela de bases
        st.dataframe(
            df_base.style.format({
                'Total Técnicos': '{:,.0f}',
                'Total Serviços': '{:,.0f}',
                'Valor Total': 'R$ {:,.2f}'
            }),
            use_container_width=True
        )
        
    else:
        st.error("Não foi possível carregar os dados. Por favor, verifique a conexão com o banco de dados.")
