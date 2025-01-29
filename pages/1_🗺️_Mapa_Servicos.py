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

# Filtros adicionais na sidebar
col1, col2 = st.sidebar.columns(2)

# Inicializar listas vazias para os filtros
cidades = []
tecnicos = []

# Só mostrar os filtros se tiver dados
if df is not None and not df.empty:
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

    # Criar mapa base
    m = folium.Map(
        location=[-23.5505, -46.6333],  # São Paulo
        zoom_start=10
    )

    # Adicionar marcadores
    for idx, row in df.iterrows():
        if pd.notna(row['LATIDUDE']) and pd.notna(row['LONGITUDE']):
            folium.Marker(
                [row['LATIDUDE'], row['LONGITUDE']],
                popup=f"""
                <b>Cidade:</b> {row['CIDADES']}<br>
                <b>Técnico:</b> {row['TECNICO']}<br>
                <b>Data:</b> {row['DATA_TOA'].strftime('%d/%m/%Y %H:%M')}<br>
                <b>Serviço:</b> {row['SERVIÇO']}<br>
                <b>Status:</b> {row['STATUS']}<br>
                """
            ).add_to(m)

    # Exibir mapa
    folium_static(m, width=1200)

    # Métricas
    st.subheader("📊 Métricas")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total de Serviços", len(df))
    
    with col2:
        st.metric("Cidades Atendidas", len(df['CIDADES'].unique()))
    
    with col3:
        st.metric("Técnicos Ativos", len(df['TECNICO'].unique()))
    
    with col4:
        concluidos = len(df[df['STATUS'].str.contains('Concluído', case=False, na=False)])
        st.metric("Serviços Concluídos", concluidos)

else:
    # Mostrar mensagem quando não há dados
    st.warning("⚠️ Nenhum dado encontrado para o período selecionado. Tente ajustar as datas do filtro.")
