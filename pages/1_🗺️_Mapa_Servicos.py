import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from datetime import datetime, timedelta
from DB import DatabaseConnection

# Configuração da página
st.set_page_config(
    page_title="Mapa de Serviços",
    page_icon="🗺️",
    layout="wide"
)

# Título
st.title("🗺️ Mapa de Serviços")

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
        tecnicos = st.multiselect(
            "👨‍🔧 Técnicos:",
            options=sorted(df['TECNICO'].unique()),
            default=[]
        )
    
    # Aplicar filtros
    if cidades:
        df = df[df['CIDADES'].isin(cidades)]
    if tecnicos:
        df = df[df['TECNICO'].isin(tecnicos)]
    
    # Criar mapa
    st.subheader("📍 Localização dos Serviços")
    
    # Centro do mapa (média das coordenadas)
    center_lat = df['LATIDUDE'].mean()
    center_lon = df['LONGITUDE'].mean()
    
    # Criar mapa base
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles='cartodbpositron'
    )
    
    # Adicionar marcadores
    for idx, row in df.iterrows():
        # Criar popup com informações
        popup_html = f"""
            <div style='min-width: 200px'>
                <b>Data:</b> {row['DATA_TOA'].strftime('%d/%m/%Y %H:%M')}<br>
                <b>Técnico:</b> {row['TECNICO']}<br>
                <b>Cidade:</b> {row['CIDADES']}<br>
                <b>Serviço:</b> {row['SERVIÇO']}<br>
                <b>Status:</b> {row['STATUS']}<br>
                <b>Valor:</b> R$ {row['VALOR_TÉCNICO']:,.2f}
            </div>
        """
        
        # Adicionar marcador
        folium.CircleMarker(
            location=[row['LATIDUDE'], row['LONGITUDE']],
            radius=8,
            popup=folium.Popup(popup_html, max_width=300),
            color='red',
            fill=True,
            fill_color='red'
        ).add_to(m)
    
    # Exibir mapa
    folium_static(m, width=1200, height=600)
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total de Serviços",
            f"{len(df):,}",
            help="Número total de serviços no período e filtros selecionados"
        )
    
    with col2:
        valor_total = df['VALOR_TÉCNICO'].sum()
        st.metric(
            "Valor Total",
            f"R$ {valor_total:,.2f}",
            help="Soma dos valores dos serviços"
        )
    
    with col3:
        media_valor = df['VALOR_TÉCNICO'].mean()
        st.metric(
            "Valor Médio",
            f"R$ {media_valor:,.2f}",
            help="Valor médio por serviço"
        )
    
    with col4:
        n_tecnicos = df['TECNICO'].nunique()
        st.metric(
            "Técnicos Ativos",
            f"{n_tecnicos}",
            help="Número de técnicos que realizaram serviços"
        )
    
    # Tabela de dados
    with st.expander("📋 Dados Detalhados"):
        st.dataframe(
            df[[
                'DATA_TOA', 'TECNICO', 'CIDADES', 'SERVIÇO', 
                'STATUS', 'VALOR_TÉCNICO'
            ]].sort_values('DATA_TOA', ascending=False),
            hide_index=True,
            use_container_width=True
        )

else:
    st.warning("Nenhum dado encontrado para o período selecionado.")
