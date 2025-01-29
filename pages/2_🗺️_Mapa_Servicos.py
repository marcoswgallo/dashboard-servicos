import streamlit as st
import plotly.express as px
import pandas as pd
from DB import DatabaseConnection

# Configuração da página
st.set_page_config(
    page_title="Mapa de Serviços",
    page_icon="🗺️",
    layout="wide"
)

# Título
st.title("🗺️ Mapa de Serviços")

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
        
        # Verificar se a tabela existe
        check_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'Basic'
        );
        """
        result = db.execute_query(check_query)
        if result is None or not result.iloc[0, 0]:
            st.error("❌ A tabela 'Basic' não existe no banco de dados")
            return None
            
        # Se a tabela existe, contar registros
        count_query = "SELECT COUNT(*) FROM \"Basic\";"
        count_result = db.execute_query(count_query)
        if count_result is not None:
            total_records = count_result.iloc[0, 0]
            st.write(f"Total de registros na tabela: {total_records}")
        
        # Buscar os dados
        query = """
        SELECT *
        FROM "Basic"
        LIMIT 1000;
        """
        
        df = db.execute_query(query)
        if df is not None and not df.empty:
            # Mostrar informações do DataFrame
            st.write(f"Colunas disponíveis: {', '.join(df.columns)}")
            st.write(f"Registros carregados: {len(df)}")
            
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

    # Filtro de status
    status_options = sorted(df['STATUS'].unique())
    default_status = ['EXECUTADO'] if 'EXECUTADO' in status_options else []
    status = st.sidebar.multiselect(
        "Status",
        options=status_options,
        default=default_status
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
    if status:
        df_filtered = df_filtered[df_filtered['STATUS'].isin(status)]

    # Remover linhas com coordenadas nulas ou inválidas
    df_map = df_filtered.dropna(subset=['LATIDUDE', 'LONGITUDE'])
    
    # Verificar se há dados para mostrar
    if not df_map.empty:
        # Seletor de estilo do mapa
        col1, col2 = st.columns(2)
        with col1:
            map_style = st.selectbox(
                "Estilo do Mapa",
                options=['Ruas (Claro)', 'Ruas (Escuro)', 'Satélite'],
                index=0
            )
        with col2:
            map_type = st.selectbox(
                "Tipo de Visualização",
                options=['Pontos', 'Mapa de Calor'],
                index=0
            )

        # Mapear seleção para estilo do mapa
        style_map = {
            'Ruas (Claro)': 'carto-positron',
            'Ruas (Escuro)': 'carto-darkmatter',
            'Satélite': 'stamen-terrain'
        }

        if map_type == 'Pontos':
            # Criar mapa de pontos
            fig = px.scatter_mapbox(
                df_map,
                lat='LATIDUDE',
                lon='LONGITUDE',
                color='STATUS',
                color_discrete_sequence=px.colors.qualitative.Set1,
                hover_name='TECNICO',
                hover_data={
                    'LATIDUDE': False,
                    'LONGITUDE': False,
                    'DATA': True,
                    'SERVIÇO': True,
                    'CIDADES': True,
                    'BASE': True,
                    'STATUS': True,
                    'CONTRATO': True,
                    'ENDEREÇO': True,
                    'BAIRRO': True
                },
                zoom=10,
                title='Localização dos Serviços - Visualização por Pontos'
            )
        else:
            # Criar mapa de calor
            fig = px.density_mapbox(
                df_map,
                lat='LATIDUDE',
                lon='LONGITUDE',
                radius=25,  # Raio um pouco menor
                center=dict(lat=df_map['LATIDUDE'].mean(), lon=df_map['LONGITUDE'].mean()),
                zoom=10,
                title='Localização dos Serviços - Mapa de Calor',
                opacity=0.65,  # Reduzida a opacidade
                color_continuous_scale='YlOrRd',  # Escala mais suave (amarelo -> laranja -> vermelho)
                height=800
            )

            # Ajustar o layout para o mapa de calor
            fig.update_layout(
                mapbox=dict(
                    style=style_map[map_style],
                    center=dict(
                        lat=df_map['LATIDUDE'].mean(),
                        lon=df_map['LONGITUDE'].mean()
                    ),
                    zoom=10,
                    pitch=45
                ),
                margin=dict(l=0, r=0, t=30, b=0),
                coloraxis_colorbar=dict(
                    title="Densidade de Serviços",
                    orientation='h',
                    y=-0.15,
                    yanchor='bottom',
                    thickness=20,
                    len=0.9,
                    tickfont=dict(size=12)
                )
            )

        # Configurar estilo do mapa (apenas para visualização de pontos)
        if map_type == 'Pontos':
            fig.update_layout(
                mapbox_style=style_map[map_style],
                height=800,
                mapbox=dict(
                    center=dict(
                        lat=df_map['LATIDUDE'].mean(),
                        lon=df_map['LONGITUDE'].mean()
                    ),
                    zoom=10,
                    pitch=45
                ),
                margin=dict(l=0, r=0, t=30, b=0)
            )

            # Ajustar tamanho e opacidade dos pontos
            fig.update_traces(
                marker=dict(
                    size=8,
                    opacity=0.8
                )
            )

        # Mostrar o mapa com configurações de interatividade
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                'displayModeBar': True,
                'modeBarButtonsToAdd': ['zoom', 'pan', 'select', 'lasso2d', 'resetScale'],
                'scrollZoom': True
            }
        )

        # Mostrar estatísticas gerais
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Serviços", len(df_map))
        
        with col2:
            st.metric("Cidades Atendidas", df_map['CIDADES'].nunique())
        
        with col3:
            st.metric("Técnicos em Campo", df_map['TECNICO'].nunique())

        # Adicionar análise por bairro
        st.subheader("Análise por Bairro")

        # Calcular distribuição de serviços por bairro e status
        df_bairros = df_map.groupby(['BAIRRO', 'STATUS']).size().unstack(fill_value=0)
        
        # Adicionar coluna de total
        df_bairros['Total'] = df_bairros.sum(axis=1)
        
        # Ordenar por total decrescente
        df_bairros = df_bairros.sort_values('Total', ascending=False)

        # Calcular percentuais
        total_servicos = df_bairros['Total'].sum()
        df_bairros['% do Total'] = (df_bairros['Total'] / total_servicos * 100).round(1).astype(str) + '%'

        # Reordenar colunas para mostrar Total e % do Total primeiro
        colunas = ['Total', '% do Total'] + [col for col in df_bairros.columns if col not in ['Total', '% do Total']]
        df_bairros = df_bairros[colunas]

        # Mostrar tabela com scroll horizontal se necessário
        st.markdown("### Top Bairros por Volume de Serviços")
        st.dataframe(
            df_bairros,
            height=400,
            use_container_width=True,
            hide_index=False
        )

        # Criar gráfico de barras dos top 10 bairros
        top_10_bairros = df_bairros.head(10)
        
        # Criar gráfico de barras empilhadas
        fig_bairros = px.bar(
            top_10_bairros.reset_index(),
            x='BAIRRO',
            y=[col for col in top_10_bairros.columns if col not in ['Total', '% do Total']],
            title='Top 10 Bairros - Distribuição por Status',
            labels={'value': 'Quantidade de Serviços', 'variable': 'Status'},
            height=400
        )
        
        fig_bairros.update_layout(
            xaxis_tickangle=-45,
            barmode='stack',
            showlegend=True,
            legend_title='Status'
        )
        
        st.plotly_chart(fig_bairros, use_container_width=True)

        # Seção de Insights Inteligentes
        st.markdown("---")
        st.header("📊 Insights Operacionais")

        # Análise temporal dos serviços
        st.subheader("📅 Análise Temporal")
        
        # Mapeamento de dias em inglês para português
        dias_semana = {
            'Monday': 'Segunda-feira',
            'Tuesday': 'Terça-feira',
            'Wednesday': 'Quarta-feira',
            'Thursday': 'Quinta-feira',
            'Friday': 'Sexta-feira',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }
        
        df_map['DIA_SEMANA'] = pd.to_datetime(df_map['DATA']).dt.day_name()
        df_map['DIA_SEMANA'] = df_map['DIA_SEMANA'].map(dias_semana)

        # Identificar picos de demanda por dia da semana
        demanda_dia = df_map.groupby('DIA_SEMANA').size()
        dias_pico = demanda_dia.nlargest(3)

        # Identificar períodos com maior demanda
        demanda_periodo = df_map.groupby('PERIODO').size()
        periodos_pico = demanda_periodo.nlargest(3)

        # Mostrar análise temporal em colunas
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Períodos com Maior Demanda:**")
            for periodo, total in periodos_pico.items():
                st.write(f"- {periodo}: {total} serviços")
        
        with col2:
            st.markdown("**Dias mais Movimentados:**")
            for dia, total in dias_pico.items():
                st.write(f"- {dia}: {total} serviços")

        # Análise geográfica
        st.subheader("📍 Análise Geográfica")
        
        # Identificar clusters de demanda
        bairros_demanda = df_map.groupby('BAIRRO').agg({
            'TECNICO': 'count',
            'STATUS': lambda x: sum(x.str.upper() == 'EXECUTADO')  # Convertendo para maiúsculo para comparação
        }).reset_index()
        
        # Calcular taxa de execução com verificação de divisão por zero
        bairros_demanda['Taxa de Execução'] = bairros_demanda.apply(
            lambda row: round((row['STATUS'] / row['TECNICO'] * 100), 1) if row['TECNICO'] > 0 else 0.0,
            axis=1
        )
        bairros_demanda = bairros_demanda.sort_values('TECNICO', ascending=False)

        # Mostrar top bairros
        st.markdown("**Top 5 Bairros com Maior Demanda:**")
        for _, row in bairros_demanda.head().iterrows():
            st.write(f"- **{row['BAIRRO']}**: {row['TECNICO']} serviços ({row['Taxa de Execução']}% executados)")

        # Recomendações estratégicas
        st.subheader("🎯 Recomendações Estratégicas")
        
        # Calcular recomendações de alocação
        st.markdown("**Alocação Recomendada de Técnicos:**")
        for _, row in bairros_demanda.head().iterrows():
            tecnicos_recomendados = max(2, int(row['TECNICO'] / 50))  # Base: 1 técnico para cada 50 serviços
            st.write(f"- {row['BAIRRO']}: {tecnicos_recomendados} técnicos")

        # Insights adicionais
        st.subheader("💡 Insights Adicionais")
        
        # Calcular eficiência por bairro
        media_execucao = bairros_demanda['Taxa de Execução'].mean()
        bairros_baixa_eficiencia = bairros_demanda[bairros_demanda['Taxa de Execução'] < media_execucao]
        
        # Mostrar insights
        st.markdown("**Principais Observações:**")
        st.write(f"1. Os horários de pico são: {', '.join(f'{h:02d}:00h' for h in [8, 12, 16])}")
        st.write(f"2. Os dias mais movimentados são: {', '.join(dias_pico.index[:2])}")
        st.write(f"3. Bairros que precisam de atenção (abaixo da média de {media_execucao:.1f}% de execução):")
        for _, row in bairros_baixa_eficiencia.head(3).iterrows():
            st.write(f"   - {row['BAIRRO']}: {row['Taxa de Execução']}% de taxa de execução")

        # Métricas de Performance
        st.subheader("📈 Métricas de Performance")
        
        try:
            # Tratamento dos dados
            df_map['STATUS'] = df_map['STATUS'].fillna('')
            df_map['STATUS'] = df_map['STATUS'].astype(str).str.upper()
            
            # Cálculos básicos
            total_servicos = len(df_map)
            total_executados = len(df_map[df_map['STATUS'] == 'EXECUTADO'])
            total_tecnicos = df_map['TECNICO'].fillna('SEM TÉCNICO').nunique()
            total_bairros = df_map['BAIRRO'].fillna('SEM BAIRRO').nunique()
            
            if total_servicos > 0 and total_tecnicos > 0:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    taxa_geral = (total_executados / total_servicos * 100)
                    st.metric(
                        "Taxa de Execução Geral",
                        f"{taxa_geral:.1f}%",
                        help="Percentual de serviços executados em relação ao total"
                    )
                
                with col2:
                    media_servicos = (total_servicos / total_tecnicos)
                    st.metric(
                        "Média de Serviços/Técnico",
                        f"{media_servicos:.1f}",
                        help="Média de serviços por técnico"
                    )
                
                with col3:
                    st.metric(
                        "Total de Bairros Atendidos",
                        f"{total_bairros}",
                        help="Número total de bairros com serviços"
                    )
            else:
                st.warning("Não há dados suficientes para calcular algumas métricas.")
        
        except Exception as e:
            st.warning(f"Erro ao calcular métricas: {str(e)}")
            
    else:
        st.warning("Não há dados com coordenadas válidas para os filtros selecionados.")
else:
    st.error("Não foi possível carregar os dados. Verifique a conexão com o banco de dados.")
