import streamlit as st
import pandas as pd
import plotly.express as px
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

# Filtros
with st.container():
    st.markdown("### 🎯 Filtros")
    
    col1, col2 = st.columns([2,2])
    
    with col1:
        data_inicial = st.text_input(
            "📅 Data Inicial:",
            value="01/01/2025",  # Primeiro dia com dados
            help="Digite a data inicial no formato DD/MM/YYYY"
        )
        data_final = st.text_input(
            "📅 Data Final:",
            value="27/01/2025",  # Último dia com dados
            help="Digite a data final no formato DD/MM/YYYY"
        )

    # Converter datas para o formato ISO antes de passar para o DB
    try:
        data_inicial_iso = datetime.strptime(data_inicial, "%d/%m/%Y").strftime("%Y-%m-%d")
        data_final_iso = datetime.strptime(data_final, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError as e:
        st.error("⚠️ Por favor, digite as datas no formato DD/MM/YYYY")
        st.stop()

    # Calcular datas limite
    #data_inicio_str = data_inicio.strftime("%Y-%m-%d")
    #data_fim_str = data_fim.strftime("%Y-%m-%d")
    
    # Carregar dados
    db = DatabaseConnection()
    df = db.execute_query(data_inicial_iso, data_final_iso)
    
    if df is not None:
        # Remover linhas com coordenadas nulas ou inválidas
        df = df.dropna(subset=['LATIDUDE', 'LONGITUDE'])
        
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

        # Função para carregar dados com query
        @st.cache_data(ttl=300)  # Cache por 5 minutos
        def load_data_with_query(query):
            try:
                db = DatabaseConnection()
                df = db.execute_query(query)
                if df is not None and not df.empty:
                    # Converter DATA para datetime usando um parser mais flexível
                    def parse_date(date_str):
                        try:
                            # Primeiro tenta o formato com hora
                            return pd.to_datetime(date_str, format='%d/%m/%Y %H:%M')
                        except:
                            try:
                                # Se falhar, tenta só a data
                                return pd.to_datetime(date_str, format='%d/%m/%Y')
                            except:
                                # Se ainda falhar, retorna None
                                return None

                    df['DATA'] = df['DATA'].apply(parse_date)
                    
                    # Converter valores para numérico
                    df['VALOR TÉCNICO'] = pd.to_numeric(df['VALOR TÉCNICO'].str.replace(',', '.'), errors='coerce')
                    df['VALOR EMPRESA'] = pd.to_numeric(df['VALOR EMPRESA'].str.replace(',', '.'), errors='coerce')
                    df['LATIDUDE'] = pd.to_numeric(df['LATIDUDE'], errors='coerce')
                    df['LONGITUDE'] = pd.to_numeric(df['LONGITUDE'], errors='coerce')
                    
                    # Preencher valores nulos
                    df['SERVIÇO'] = df['SERVIÇO'].fillna('')
                    df['CIDADES'] = df['CIDADES'].fillna('')
                    df['TECNICO'] = df['TECNICO'].fillna('')
                    df['BASE'] = df['BASE'].fillna('')
                    df['STATUS'] = df['STATUS'].fillna('')
                    
                    return df
                return None
            except Exception as e:
                st.error(f"Erro ao carregar dados: {str(e)}")
                return None

        # Criar mapa
        st.markdown("### 📍 Localização dos Serviços")
        
        # Criar gráfico de mapa com Plotly
        fig = px.scatter_mapbox(
            df,
            lat='LATIDUDE',
            lon='LONGITUDE',
            hover_name='OS',
            hover_data={
                'TECNICO': True,
                'DATA': True,
                'LATIDUDE': False,
                'LONGITUDE': False
            },
            zoom=5,  # Zoom mais distante para ver todos os pontos
            height=600
        )

        # Atualizar layout do mapa
        fig.update_layout(
            mapbox_style="carto-positron",
            mapbox=dict(
                center=dict(lat=-22.9, lon=-47.0),  # Centro em Campinas-SP
            ),
            margin={"r":0,"t":0,"l":0,"b":0}
        )

        # Exibir mapa
        st.plotly_chart(fig, use_container_width=True)
        
        # Análises adicionais
        st.markdown("### 📊 Análises")
        
        # Criar colunas para os gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de serviços por técnico
            df_tec = df.groupby('TECNICO').size().reset_index(name='Total')
            df_tec = df_tec.sort_values('Total', ascending=True)
            
            fig_tec = px.bar(
                df_tec,
                x='Total',
                y='TECNICO',
                orientation='h',
                title='Serviços por Técnico',
                labels={'Total': 'Quantidade de Serviços', 'TECNICO': 'Técnico'}
            )
            st.plotly_chart(fig_tec, use_container_width=True)
        
        with col2:
            # Gráfico de serviços por cidade
            df_cidade = df.groupby('CIDADES').size().reset_index(name='Total')
            df_cidade = df_cidade.sort_values('Total', ascending=True)
            
            fig_cidade = px.bar(
                df_cidade,
                x='Total',
                y='CIDADES',
                orientation='h',
                title='Serviços por Cidade',
                labels={'Total': 'Quantidade de Serviços', 'CIDADES': 'Cidade'}
            )
            st.plotly_chart(fig_cidade, use_container_width=True)
            
        # Tabela de dados
        st.markdown("### 📋 Dados Detalhados")
        st.dataframe(
            df[['OS', 'TECNICO', 'DATA', 'VALOR_TÉCNICO']].sort_values('DATA', ascending=False),
            use_container_width=True
        )
        
        # Métricas principais em cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
                <div class="metric-card">
                    <h3 style="margin:0">📊 Total de Serviços</h3>
                    <h2 style="margin:0;color:#ff4b4b">{}</h2>
                </div>
            """.format(len(df)), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
                <div class="metric-card">
                    <h3 style="margin:0">🏙️ Cidades Atendidas</h3>
                    <h2 style="margin:0;color:#ff4b4b">{}</h2>
                </div>
            """.format(df['CIDADES'].nunique()), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
                <div class="metric-card">
                    <h3 style="margin:0">👨‍🔧 Técnicos Ativos</h3>
                    <h2 style="margin:0;color:#ff4b4b">{}</h2>
                </div>
            """.format(df['TECNICO'].nunique()), unsafe_allow_html=True)
        
        with col4:
            executados = len(df[df['STATUS'] == 'EXECUTADO'])
            total = len(df)
            taxa_execucao = (executados/total*100) if total > 0 else 0
            st.markdown("""
                <div class="metric-card">
                    <h3 style="margin:0">✅ Taxa de Execução</h3>
                    <h2 style="margin:0;color:#ff4b4b">{:.1f}%</h2>
                </div>
            """.format(taxa_execucao), unsafe_allow_html=True)

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
        
        df['DIA_SEMANA'] = pd.to_datetime(df['DATA']).dt.day_name()
        df['DIA_SEMANA'] = df['DIA_SEMANA'].map(dias_semana)

        # Identificar picos de demanda por dia da semana
        demanda_dia = df.groupby('DIA_SEMANA').size()
        dias_pico = demanda_dia.nlargest(3)

        # Identificar períodos com maior demanda
        demanda_periodo = df.groupby('PERIODO').size()
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
        bairros_demanda = df.groupby('BAIRRO').agg({
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
            df['STATUS'] = df['STATUS'].fillna('')
            df['STATUS'] = df['STATUS'].astype(str).str.upper()
            
            # Cálculos básicos
            total_servicos = len(df)
            total_executados = len(df[df['STATUS'] == 'EXECUTADO'])
            total_tecnicos = df['TECNICO'].fillna('SEM TÉCNICO').nunique()
            total_bairros = df['BAIRRO'].fillna('SEM BAIRRO').nunique()
            
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
        st.error("Não foi possível carregar os dados. Por favor, verifique a conexão com o banco de dados.")
