import streamlit as st
import plotly.express as px
import pandas as pd
from DB import DatabaseConnection

# Configuração da página
st.set_page_config(
    page_title="Detalhamento por Técnico",
    page_icon="📊",
    layout="wide"
)

# Título
st.title("📊 Detalhamento por Técnico")

# Mapeamento de bases para tipos
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

# Função para carregar dados
@st.cache_data
def load_data():
    try:
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
        else:
            st.error("DataFrame vazio retornado pela consulta")
            return None
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None

# Carregar dados
df = load_data()

if df is not None:
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

    # Outros filtros
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

    if not df_filtered.empty:
        # Filtrar apenas serviços executados
        df_executado = df_filtered[df_filtered['STATUS'].str.upper() == 'EXECUTADO']
        df_executado['DATA'] = df_executado['DATA'].dt.date

        # Calcular métricas por técnico (apenas executados)
        # Primeiro agrupamos por técnico, data e contrato para ter contratos únicos por dia
        df_contratos_por_dia = df_executado.groupby(['TECNICO', 'DATA', 'CONTRATO']).agg({
            'VALOR TÉCNICO': 'sum'  # Soma do valor por contrato
        }).reset_index()

        # Agora calculamos as métricas finais
        metricas_tecnico = df_contratos_por_dia.groupby('TECNICO').agg({
            'DATA': 'nunique',  # Dias trabalhados
            'CONTRATO': 'count',  # Total de contratos únicos
            'VALOR TÉCNICO': 'sum'  # Valor total
        }).reset_index()

        # Renomear colunas
        metricas_tecnico.columns = ['TECNICO', 'Dias Trabalhados', 'Contratos Executados', 'Valor Total']

        # Calcular distribuição de status por técnico e contrato único
        status_por_tecnico = df_filtered.groupby(['TECNICO', 'CONTRATO', 'STATUS']).size().reset_index()
        status_por_tecnico = status_por_tecnico.groupby(['TECNICO', 'STATUS']).size().unstack(fill_value=0)

        # Juntar com distribuição de status
        metricas_tecnico = metricas_tecnico.merge(status_por_tecnico, on='TECNICO', how='left')

        # Calcular médias (usando apenas contratos executados)
        metricas_tecnico['Média de Contratos/Dia'] = metricas_tecnico['Contratos Executados'] / metricas_tecnico['Dias Trabalhados']
        metricas_tecnico['Média por Dia'] = metricas_tecnico['Valor Total'] / metricas_tecnico['Dias Trabalhados']

        # Criar três colunas para os gráficos
        col1, col2, col3 = st.columns(3)

        with col1:
            # Gráfico de dias trabalhados
            fig_dias = px.bar(
                metricas_tecnico.nlargest(10, 'Dias Trabalhados'),
                x='TECNICO',
                y='Dias Trabalhados',
                title='Top 10 Técnicos por Dias Trabalhados'
            )
            fig_dias.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_dias, use_container_width=True)

        with col2:
            # Gráfico de média de contratos por dia
            fig_media_contratos = px.bar(
                metricas_tecnico.nlargest(10, 'Média de Contratos/Dia'),
                x='TECNICO',
                y='Média de Contratos/Dia',
                title='Top 10 Técnicos - Média de Contratos por Dia'
            )
            fig_media_contratos.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_media_contratos, use_container_width=True)

        with col3:
            # Gráfico de média de valor por dia
            fig_media_valor = px.bar(
                metricas_tecnico.nlargest(10, 'Média por Dia'),
                x='TECNICO',
                y='Média por Dia',
                title='Top 10 Técnicos - Faturamento Médio por Dia'
            )
            fig_media_valor.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_media_valor, use_container_width=True)

        # Formatar valores monetários e decimais
        metricas_tecnico['Valor Total'] = metricas_tecnico['Valor Total'].apply(lambda x: f'R$ {x:,.2f}')
        metricas_tecnico['Média por Dia'] = metricas_tecnico['Média por Dia'].apply(lambda x: f'R$ {x:,.2f}')
        metricas_tecnico['Média de Contratos/Dia'] = metricas_tecnico['Média de Contratos/Dia'].round(1)

        # Exibir tabela completa
        st.subheader('Detalhamento Completo por Técnico')
        st.dataframe(metricas_tecnico.sort_values('Dias Trabalhados', ascending=False), hide_index=True)
