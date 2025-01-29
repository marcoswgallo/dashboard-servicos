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

def format_currency(value):
    """Formata valor em reais."""
    return f"R$ {value:,.2f}"

def create_bar_chart(df, x, y, title, color_scale):
    """Cria gráfico de barras padronizado."""
    fig = px.bar(
        df,
        x=x,
        y=y,
        title=title,
        color=y,
        color_continuous_scale=color_scale,
        text=y
    )
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title_x=0.5,
        title_font_size=16,
        xaxis_title="",
        yaxis_title="",
        xaxis_tickangle=-45,
        height=500
    )
    fig.update_traces(
        texttemplate='%{text:,.0f}',
        textposition='outside'
    )
    return fig

# Título principal
st.title("👨‍🔧 Detalhamento por Técnico")

# Filtros
with st.container():
    st.markdown("### 🎯 Filtros")
    
    col1, col2 = st.columns([2,2])
    
    with col1:
        data_fim = st.date_input(
            "📅 Data Final:",
            value=datetime.now(),
            max_value=datetime.now(),
            help="Data final do período de análise"
        )
        data_inicio = st.date_input(
            "📅 Data Inicial:",
            value=data_fim - timedelta(days=30),
            max_value=data_fim,
            help="Data inicial do período de análise"
        )
    
    with col2:
        min_servicos = st.slider(
            "🔄 Mínimo de serviços:",
            min_value=1,
            max_value=50,
            value=5,
            help="Filtrar técnicos com pelo menos X serviços"
        )

    # Calcular datas limite
    data_inicio_str = data_inicio.strftime("%Y-%m-%d")
    data_fim_str = data_fim.strftime("%Y-%m-%d")
    
    # Carregar dados
    db = DatabaseConnection()
    df = db.execute_query(data_inicio_str, data_fim_str)
    
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
            st.metric("💰 Valor Total", format_currency(valor_total))
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
            # Top 10 por volume
            fig1 = create_bar_chart(
                df_tecnico.head(10),
                'Técnico',
                'Total Serviços',
                'Top 10 Técnicos por Volume de Serviços',
                'Reds'
            )
            st.plotly_chart(fig1, use_container_width=True)
            
        with col2:
            # Top 10 por valor
            df_valor = df_tecnico.sort_values('Valor Total', ascending=False).head(10).copy()
            df_valor['Valor Total'] = df_valor['Valor Total'].round(2)
            fig2 = create_bar_chart(
                df_valor,
                'Técnico',
                'Valor Total',
                'Top 10 Técnicos por Valor Total',
                'Greens'
            )
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
        df_base = df_base.sort_values('Total Serviços', ascending=False)
        
        # Gráfico de pizza
        fig3 = px.pie(
            df_base,
            values='Total Serviços',
            names='Base',
            title='Distribuição de Serviços por Base',
            hole=0.4
        )
        fig3.update_layout(
            title_x=0.5,
            title_font_size=16,
            height=500
        )
        fig3.update_traces(
            textinfo='percent+label',
            textposition='outside'
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
