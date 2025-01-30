import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
from excel_db import ExcelConnection
from folium.plugins import MarkerCluster

# Configuração da página
st.set_page_config(
    page_title="Mapa de Serviços",
    page_icon="🗺️",
    layout="wide"
)

# Título
st.title("🗺️ Mapa de Serviços")

# Container para status
status_container = st.empty()

with st.spinner('Conectando ao Excel...'):
    # Inicializar conexão com Excel
    db = ExcelConnection()

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

# Container para dados
data_container = st.empty()

with st.spinner('Carregando dados...'):
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

    # Container para mapa
    map_container = st.empty()

    with st.spinner('Gerando mapa...'):
        # Criar mapa base
        m = folium.Map(
            location=[-23.5505, -46.6333],  # São Paulo
            zoom_start=10,
            prefer_canvas=True  # Usar canvas para melhor performance
        )
        
        # Criar cluster de marcadores
        marker_cluster = MarkerCluster(
            name="Serviços",
            overlay=True,
            control=True,
            icon_create_function=None
        )

        # Filtrar apenas registros com coordenadas válidas
        df_map = df[pd.notna(df["LATIDUDE"]) & pd.notna(df["LONGITUDE"])].copy()
        
        # Limitar número de marcadores se necessário
        max_markers = 1000
        if len(df_map) > max_markers:
            st.warning(f"⚠️ Limitando visualização aos {max_markers} serviços mais recentes para melhor performance")
            df_map = df_map.nlargest(max_markers, "DATA_TOA")

        # Adicionar marcadores ao cluster
        for idx, row in df_map.iterrows():
            folium.Marker(
                [row["LATIDUDE"], row["LONGITUDE"]],
                popup=f"""
                <b>Cidade:</b> {row["CIDADES"] if pd.notna(row["CIDADES"]) else "N/A"}<br>
                <b>Técnico:</b> {row["TECNICO"] if pd.notna(row["TECNICO"]) else "N/A"}<br>
                <b>Data:</b> {row["DATA_TOA"].strftime("%d/%m/%Y %H:%M") if pd.notna(row["DATA_TOA"]) else "N/A"}<br>
                <b>Serviço:</b> {row["SERVIÇO"] if pd.notna(row["SERVIÇO"]) else "N/A"}<br>
                <b>Status:</b> {row["STATUS"] if pd.notna(row["STATUS"]) else "N/A"}<br>
                """
            ).add_to(marker_cluster)

        # Adicionar cluster ao mapa
        marker_cluster.add_to(m)

        # Ajustar zoom para mostrar todos os marcadores
        if not df_map.empty:
            sw = df_map[["LATIDUDE", "LONGITUDE"]].min().values.tolist()
            ne = df_map[["LATIDUDE", "LONGITUDE"]].max().values.tolist()
            m.fit_bounds([sw, ne])

        # Exibir mapa usando st_folium
        with map_container:
            map_data = st_folium(
                m,
                width=1200,
                height=600,
                returned_objects=[],
                use_container_width=True
            )

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
        st.metric("Serviços com Coordenadas", len(df_map))

else:
    st.warning("⚠️ Nenhum dado encontrado para o período selecionado")
