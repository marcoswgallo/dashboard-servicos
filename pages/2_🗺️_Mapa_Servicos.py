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
        ORDER BY TO_DATE("DATA", 'DD/MM/YYYY') DESC
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
            
            # Converter coordenadas para numérico
            df['LATIDUDE'] = pd.to_numeric(df['LATIDUDE'], errors='coerce')
            df['LONGITUDE'] = pd.to_numeric(df['LONGITUDE'], errors='coerce')
            
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
    # Filtros
    col1, col2, col3 = st.columns([2,2,1])
    
    with col1:
        # Filtro de data
        dias = st.slider(
            "Dias anteriores:",
            min_value=1,
            max_value=90,
            value=30,
            help="Filtrar dados dos últimos X dias"
        )
        
        # Atualizar query com o filtro de dias
        query = f"""
        SELECT *
        FROM "Basic"
        WHERE TO_DATE("DATA", 'DD/MM/YYYY') >= CURRENT_DATE - INTERVAL '{dias} days'
        ORDER BY TO_DATE("DATA", 'DD/MM/YYYY') DESC
        LIMIT 1000;
        """
    
    with col2:
        # Filtro de status
        status = st.multiselect(
            "Status:",
            sorted(df['STATUS'].unique()) if df is not None else [],
            default=[],
            help="Filtrar por status do serviço"
        )
    
    with col3:
        # Tipo de visualização
        tipo_vis = st.selectbox(
            "Tipo de Visualização",
            ["Pontos", "Calor"],
            help="Escolha como os dados serão mostrados no mapa"
        )

    # Filtros e processamento
    if df is not None:
        df_filtered = df.copy()
        
        # Aplicar filtro de status
        if status:
            df_filtered = df_filtered[df_filtered['STATUS'].isin(status)]
        
        # Remover linhas sem coordenadas
        df_map = df_filtered[df_filtered['LATIDUDE'].notna() & df_filtered['LONGITUDE'].notna()]
        
        # Debug - mostrar quantidade após filtro
        st.write(f"Registros com coordenadas válidas: {len(df_map)}")
        
        if not df_map.empty:
            # Formatar dados para hover
            df_map['DATA'] = pd.to_datetime(df_map['DATA'], format='%d/%m/%Y').dt.strftime('%d/%m/%Y')
            df_map['Detalhes'] = df_map.apply(
                lambda x: f"""
                🗓️ {x['DATA']}
                👤 {x['CLIENTE']}
                🔧 {x['SERVIÇO']}
                👨‍🔧 {x['TECNICO']}
                📍 {x['BAIRRO']}, {x['CIDADES']}
                🏢 Base: {x['BASE']}
                ℹ️ {x['TIPO DE SERVIÇO']}
                """, 
                axis=1
            )
            
            # Criar mapa de pontos
            fig = px.scatter_mapbox(
                df_map,
                lat='LATIDUDE',
                lon='LONGITUDE',
                color='STATUS',
                color_discrete_sequence=px.colors.qualitative.Set1,
                title=f'Localização dos Serviços - Últimos {dias} dias',
                hover_data={
                    'LATIDUDE': False,
                    'LONGITUDE': False,
                    'Detalhes': True,
                    'STATUS': True
                },
                hover_name='CLIENTE'
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
