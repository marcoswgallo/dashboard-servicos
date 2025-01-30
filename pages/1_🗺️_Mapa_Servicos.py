import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
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

# Só mostrar os filtros se tiver dados
if not df.empty:
    # Remover valores nulos antes de usar unique() e sort
    cidades_unicas = df["CIDADES"].dropna().unique().tolist()
    tecnicos_unicos = df["TECNICO"].dropna().unique().tolist()
    
    with col1:
        cidades = st.multiselect(
            "🏙️ Cidades:",
            options=sorted(cidades_unicas),
            default=[]
        )
    
    with col2:
        tecnicos = st.multiselect(
            "👨‍🔧 Técnicos:",
            options=sorted(tecnicos_unicos),
            default=[]
        )

    # Aplicar filtros
    if cidades:
        df = df[df["CIDADES"].isin(cidades)]
    if tecnicos:
        df = df[df["TECNICO"].isin(tecnicos)]

    # Criar mapa base
    m = folium.Map(
        location=[-23.5505, -46.6333],  # São Paulo
        zoom_start=10
    )

    # Adicionar marcadores apenas para coordenadas válidas
    for idx, row in df.iterrows():
        if pd.notna(row["LATIDUDE"]) and pd.notna(row["LONGITUDE"]):
            folium.Marker(
                [row["LATIDUDE"], row["LONGITUDE"]],
                popup=f"""
                <b>Cidade:</b> {row["CIDADES"] if pd.notna(row["CIDADES"]) else "N/A"}<br>
                <b>Técnico:</b> {row["TECNICO"] if pd.notna(row["TECNICO"]) else "N/A"}<br>
                <b>Data:</b> {row["DATA_TOA"].strftime("%d/%m/%Y %H:%M") if pd.notna(row["DATA_TOA"]) else "N/A"}<br>
                <b>Serviço:</b> {row["SERVIÇO"] if pd.notna(row["SERVIÇO"]) else "N/A"}<br>
                <b>Status:</b> {row["STATUS"] if pd.notna(row["STATUS"]) else "N/A"}<br>
                """
            ).add_to(m)

    # Exibir mapa usando st_folium
    map_data = st_folium(m, width=1200, height=600, returned_objects=[])

    # Métricas
    st.subheader("📊 Métricas")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total de Serviços", len(df))
    
    with col2:
        st.metric("Cidades Atendidas", len(df["CIDADES"].unique()))
    
    with col3:
        st.metric("Técnicos em Campo", len(df["TECNICO"].unique()))
    
    with col4:
        st.metric("Serviços com Coordenadas", 
                 df[pd.notna(df["LATIDUDE"]) & pd.notna(df["LONGITUDE"])].shape[0])

else:
    st.warning("⚠️ Nenhum dado encontrado para o período selecionado")
