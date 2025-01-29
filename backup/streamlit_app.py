import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from DB import DatabaseConnection
import pandas as pd
from datetime import datetime, date
import locale

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Análise",
    page_icon="📈",
    layout="wide"
)

# Criar mapeamento de bases para tipos
base_tipos = {
    'Instalação': [
        'BASE BAURU', 'BASE BOTUCATU', 'BASE CAMPINAS', 'BASE LIMEIRA',
        'BASE PAULINIA', 'BASE PIRACICABA', 'BASE RIBEIRAO PRETO',
        'BASE SAO JOSE DO RIO PRETO', 'BASE SOROCABA', 'BASE SUMARE',
        'GPON BAURU', 'GPON RIBEIRAO PRETO'
    ],
    'Manutenção': [
        'BASE ARARAS VT', 'BASE BOTUCATU VT', 'BASE MDU ARARAS',
        'BASE MDU BAURU', 'BASE MDU MOGI', 'BASE MDU PIRACICABA',
        'BASE MDU SJRP', 'BASE PIRACICABA VT', 'BASE RIBEIRÃO VT',
        'BASE SERTAOZINHO VT', 'BASE SUMARE VT', 'BASE VAR BAURU',
        'BASE VAR PIRACICABA', 'BASE VAR SUMARE'
    ],
    'Desconexão': [
        'DESCONEXAO', 'DESCONEXÃO BOTUCATU', 'DESCONEXÃO CAMPINAS',
        'DESCONEXAO RIBEIRAO PRETO'
    ]
}

# Função para carregar os dados
@st.cache_data
def load_data():
    db = DatabaseConnection()
    query = """
    SELECT * FROM "Basic"
    """
    df = db.execute_query(query)
    if df is not None:
        # Converter coluna de data para datetime usando o formato correto
        df['DATA'] = pd.to_datetime(df['DATA'], dayfirst=True)
        
        # Converter valores para numérico
        df['VALOR TÉCNICO'] = pd.to_numeric(df['VALOR TÉCNICO'].str.replace(',', '.'), errors='coerce')
        df['VALOR EMPRESA'] = pd.to_numeric(df['VALOR EMPRESA'].str.replace(',', '.'), errors='coerce')
        
        # Preencher valores nulos
        df['SERVIÇO'] = df['SERVIÇO'].fillna('')
        df['CIDADES'] = df['CIDADES'].fillna('')
        df['TECNICO'] = df['TECNICO'].fillna('')
        df['BASE'] = df['BASE'].fillna('')
        
        # Criar coluna de tipo de base
        df['TIPO_BASE'] = 'Outros'
        for tipo, bases in base_tipos.items():
            df.loc[df['BASE'].isin(bases), 'TIPO_BASE'] = tipo
        
    return df

# Carregar os dados
try:
    df = load_data()
    if df is None:
        st.error("Não foi possível conectar ao banco de dados. Verifique as configurações de conexão.")
        st.stop()
except Exception as e:
    st.error(f"Erro ao carregar dados: {str(e)}")
    st.stop()

# Verificar se há dados
if df.empty:
    st.warning("Não há dados disponíveis para exibição.")
    st.stop()

# Título
st.title("📈 Dashboard de Análise")

# Sidebar com filtros
st.sidebar.header("Filtros")

# Filtro de data
min_date = df['DATA'].min()
max_date = df['DATA'].max()

# Tratar datas NaT
if pd.isna(min_date):
    min_date = pd.Timestamp('2020-01-01')
if pd.isna(max_date):
    max_date = pd.Timestamp('2025-12-31')

# Converter para date
min_date = min_date.date()
max_date = max_date.date()

# Filtro de data com formato brasileiro
date_range = st.sidebar.date_input(
    "Período",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    format="DD/MM/YYYY"
)

# Filtro de tipo de base
tipo_base = st.sidebar.multiselect(
    "Tipo de Base",
    options=['Instalação', 'Manutenção', 'Desconexão', 'Outros'],
    default=[]
)

# Filtro de base específica
bases_disponiveis = []
if tipo_base:
    for tipo in tipo_base:
        if tipo == 'Outros':
            bases_outros = df[~df['BASE'].isin([b for bases in base_tipos.values() for b in bases])]['BASE'].unique()
            bases_disponiveis.extend(bases_outros)
        else:
            bases_disponiveis.extend(base_tipos[tipo])
else:
    bases_disponiveis = sorted(df['BASE'].unique())

base = st.sidebar.multiselect(
    "Base",
    options=sorted(bases_disponiveis),
    default=[]
)

# Filtros dropdown
servico = st.sidebar.multiselect(
    "Serviço",
    options=sorted([s for s in df['SERVIÇO'].unique() if s != '']),
    default=[]
)

cidade = st.sidebar.multiselect(
    "Cidade",
    options=sorted([c for c in df['CIDADES'].unique() if c != '']),
    default=[]
)

tecnico = st.sidebar.multiselect(
    "Técnico",
    options=sorted([t for t in df['TECNICO'].unique() if t != '']),
    default=[]
)

# Aplicar filtros
if df is not None:
    # Filtro de data
    if len(date_range) == 2:
        start_date, end_date = date_range
        df_filtered = df[
            (df['DATA'].dt.date >= start_date) &
            (df['DATA'].dt.date <= end_date)
        ]
    else:
        df_filtered = df.copy()
    
    # Filtro de tipo de base e base
    if tipo_base:
        df_filtered = df_filtered[df_filtered['TIPO_BASE'].isin(tipo_base)]
    if base:
        df_filtered = df_filtered[df_filtered['BASE'].isin(base)]
    
    # Outros filtros
    if servico:
        df_filtered = df_filtered[df_filtered['SERVIÇO'].isin(servico)]
    if cidade:
        df_filtered = df_filtered[df_filtered['CIDADES'].isin(cidade)]
    if tecnico:
        df_filtered = df_filtered[df_filtered['TECNICO'].isin(tecnico)]
    
    # Debug - mostrar valores únicos de STATUS
    st.sidebar.write("Status disponíveis:", df_filtered['STATUS'].unique())
    
    # Criar uma cópia filtrada apenas com status EXECUTADO para os gráficos
    df_executado = df_filtered[df_filtered['STATUS'].str.upper() == 'EXECUTADO'].copy()
    
    # Debug - mostrar quantidade de registros
    st.sidebar.write("Total de registros:", len(df_filtered))
    st.sidebar.write("Registros executados:", len(df_executado))
    
    # Métricas principais em destaque no topo
    st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: rgba(28, 131, 225, 0.1);
        border: 1px solid rgba(28, 131, 225, 0.1);
        padding: 5% 5% 5% 10%;
        border-radius: 5px;
        color: rgb(30, 103, 119);
        overflow-wrap: break-word;
    }

    /* breakline for metric text         */
    div[data-testid="metric-container"] > label[data-testid="stMetricLabel"] > div {
        overflow-wrap: break-word;
        white-space: break-spaces;
        color: rgb(49, 51, 63);
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Serviços", f"{len(df_filtered):,}")
    with col2:
        st.metric("Cidades Atendidas", df_filtered['CIDADES'].nunique())
    with col3:
        st.metric("Técnicos Ativos", df_filtered['TECNICO'].nunique())
    with col4:
        valor_medio = df_executado['VALOR EMPRESA'].mean()
        st.metric("Valor Médio", f"R$ {valor_medio:,.2f}" if pd.notna(valor_medio) else "N/A")
    
    # Espaço após as métricas
    st.markdown("---")
    
    # Status das Atividades centralizado
    st.subheader("Status das Atividades")
    status_counts = df_filtered['STATUS'].value_counts().reset_index()
    status_counts.columns = ['STATUS', 'Quantidade']
    if not status_counts.empty:
        status_fig = px.pie(
            status_counts,
            values='Quantidade',
            names='STATUS',
            title='Distribuição de Status'
        )
        st.plotly_chart(status_fig, use_container_width=True)
    else:
        st.info("Sem dados para mostrar")

    # Linha divisória
    st.markdown("---")
    
    # Layout em duas colunas para os gráficos dos técnicos
    col1, col2 = st.columns(2)
    
    # Gráficos
    with col1:
        # Top 10 Técnicos por Maior Valor Total (apenas EXECUTADO)
        st.subheader("Top 10 Técnicos - Maior Faturamento")
        st.caption("Status: EXECUTADO")
        tech_data = df_executado.groupby('TECNICO')['VALOR EMPRESA'].sum().reset_index()
        if not tech_data.empty:
            # Filtrar apenas técnicos com faturamento > 0
            tech_data = tech_data[tech_data['VALOR EMPRESA'] > 0]
            tech_data_top = tech_data.sort_values('VALOR EMPRESA', ascending=False).head(10)
            tech_fig = px.bar(
                tech_data_top,
                x='TECNICO',
                y='VALOR EMPRESA',
                title='Maiores Faturamentos',
                labels={'VALOR EMPRESA': 'Valor Total (R$)', 'TECNICO': 'Técnico'}
            )
            # Formatando os valores no eixo y para mostrar em reais
            tech_fig.update_layout(
                yaxis=dict(
                    tickprefix="R$ ",
                    tickformat=",.2f"
                )
            )
            st.plotly_chart(tech_fig, use_container_width=True)
        else:
            st.info("Sem dados para mostrar")

    with col2:
        # Top 10 Técnicos por Menor Valor Total (apenas EXECUTADO)
        st.subheader("Top 10 Técnicos - Menor Faturamento")
        st.caption("Status: EXECUTADO")
        if not tech_data.empty:
            # Filtrar apenas técnicos com faturamento > 0
            tech_data = tech_data[tech_data['VALOR EMPRESA'] > 0]
            tech_data_bottom = tech_data.sort_values('VALOR EMPRESA', ascending=True).head(10)
            tech_fig_bottom = px.bar(
                tech_data_bottom,
                x='TECNICO',
                y='VALOR EMPRESA',
                title='Menores Faturamentos',
                labels={'VALOR EMPRESA': 'Valor Total (R$)', 'TECNICO': 'Técnico'},
                color_discrete_sequence=['#EF553B']  # Cor diferente para diferenciar do gráfico anterior
            )
            # Formatando os valores no eixo y para mostrar em reais
            tech_fig_bottom.update_layout(
                yaxis=dict(
                    tickprefix="R$ ",
                    tickformat=",.2f"
                )
            )
            st.plotly_chart(tech_fig_bottom, use_container_width=True)
        else:
            st.info("Sem dados para mostrar")
    
    # Linha divisória
    st.markdown("---")

    # Top 10 Cidades centralizado
    st.subheader("Top 10 Cidades")
    st.caption("Status: EXECUTADO")
    city_data = df_executado['CIDADES'].value_counts().reset_index()
    city_data.columns = ['CIDADES', 'Quantidade']
    city_data = city_data.head(10)
    if not city_data.empty:
        city_fig = px.bar(
            city_data,
            x='CIDADES',
            y='Quantidade',
            title='Serviços Executados por Cidade'
        )
        st.plotly_chart(city_fig, use_container_width=True)
    else:
        st.info("Sem dados para mostrar")
else:
    st.error("Não foi possível carregar os dados. Verifique a conexão com o banco de dados.")
