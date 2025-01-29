import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse

class DatabaseConnection:
    def __init__(self):
        try:
            # Conectar ao Neon usando a URL completa
            self.conn = psycopg2.connect(st.secrets.neon.database_url)
            self.conn.cursor_factory = RealDictCursor
            st.success("✅ Conexão com Neon estabelecida com sucesso!")
            
            # Verificar datas disponíveis
            self.check_date_range()
            
        except Exception as e:
            st.error(f"❌ Erro ao conectar ao banco de dados: {str(e)}")
            self.conn = None
    
    def check_date_range(self):
        """Verifica a primeira e última data disponível no banco."""
        try:
            with self.conn.cursor() as cur:
                # Buscar primeira data
                cur.execute('SELECT MIN("DATA") as first_date, MAX("DATA") as last_date FROM basic')
                result = cur.fetchone()
                
                if result and result['first_date'] and result['last_date']:
                    self.first_date = result['first_date']
                    self.last_date = result['last_date']
                    
                    st.info(f"📅 Dados disponíveis de {self.first_date.strftime('%d/%m/%Y %H:%M')} "
                           f"até {self.last_date.strftime('%d/%m/%Y %H:%M')}")
        except Exception as e:
            st.error(f"Erro ao verificar datas: {str(e)}")
            self.first_date = None
            self.last_date = None

    def convert_value(self, value):
        """Converte valor para float."""
        try:
            if isinstance(value, str):
                # Remove R$ e converte vírgula para ponto
                value = value.replace('R$', '').replace('.', '').replace(',', '.')
                return float(value)
            return value
        except:
            return 0

    def execute_query(self, data_inicio, data_fim):
        """
        Executa query no banco de dados.
        
        Args:
            data_inicio (str): Data inicial no formato YYYY-MM-DD ou DD/MM/YYYY
            data_fim (str): Data final no formato YYYY-MM-DD ou DD/MM/YYYY
            
        Returns:
            DataFrame: Resultado da query ou None se houver erro
        """
        @st.cache_data(ttl=300)  # Cache por 5 minutos
        def fetch_data(_conn, _data_inicio, _data_fim, _first_date, _last_date):
            try:
                with st.spinner('🔄 Carregando dados do banco...'):
                    # Tentar converter as datas para o formato correto
                    try:
                        # Primeiro tenta formato ISO (YYYY-MM-DD)
                        data_inicio_dt = pd.to_datetime(_data_inicio)
                        data_fim_dt = pd.to_datetime(_data_fim)
                        st.write("DEBUG - Datas convertidas usando formato ISO")
                    except:
                        try:
                            # Depois tenta formato BR (DD/MM/YYYY)
                            data_inicio_dt = pd.to_datetime(_data_inicio, format='%d/%m/%Y')
                            data_fim_dt = pd.to_datetime(_data_fim, format='%d/%m/%Y')
                            st.write("DEBUG - Datas convertidas usando formato BR")
                        except Exception as e:
                            st.error(f"Erro ao converter datas. Use formato DD/MM/YYYY ou YYYY-MM-DD: {str(e)}")
                            return None
                    
                    # Validar se as datas estão dentro do período disponível
                    if data_inicio_dt < _first_date:
                        st.warning(f"⚠️ Data inicial ajustada para {_first_date.strftime('%d/%m/%Y %H:%M')} (primeiro registro disponível)")
                        data_inicio_dt = _first_date
                    
                    if data_fim_dt > _last_date:
                        st.warning(f"⚠️ Data final ajustada para {_last_date.strftime('%d/%m/%Y %H:%M')} (último registro disponível)")
                        data_fim_dt = _last_date
                    
                    # Query SQL
                    query = """
                    SELECT *
                    FROM basic
                    WHERE "DATA" BETWEEN %s AND %s
                    ORDER BY "DATA"
                    """
                    
                    # Usar pandas para ler direto para DataFrame
                    df = pd.read_sql_query(
                        query, 
                        _conn, 
                        params=(data_inicio_dt, data_fim_dt)
                    )
                    
                    if df.empty:
                        st.warning("Nenhum dado encontrado para o período selecionado")
                        return None
                    
                    st.success(f"✅ {len(df):,} registros carregados com sucesso!")
                    return df
                    
            except Exception as e:
                st.error(f"Erro ao carregar dados: {str(e)}")
                return None
        
        try:
            if self.conn is None:
                st.error("Conexão com banco não inicializada")
                return None
            
            # Buscar dados com cache
            df = fetch_data(self.conn, data_inicio, data_fim, self.first_date, self.last_date)
            
            if df is not None:
                # Converter valores monetários
                df['VALOR_TÉCNICO'] = df['VALOR TÉCNICO'].apply(self.convert_value)
                df['VALOR_EMPRESA'] = df['VALOR EMPRESA'].apply(self.convert_value)
                
                # Remover colunas originais
                df = df.drop(['VALOR TÉCNICO', 'VALOR EMPRESA'], axis=1)
                
                # Converter coordenadas para float
                df['LATIDUDE'] = pd.to_numeric(df['LATIDUDE'], errors='coerce')
                df['LONGITUDE'] = pd.to_numeric(df['LONGITUDE'], errors='coerce')
                
                # Ordenar por data
                df = df.sort_values('DATA', ascending=False)
                
                # Preencher valores nulos
                df = df.fillna({
                    'SERVIÇO': '',
                    'CIDADES': '',
                    'TECNICO': '',
                    'BASE': '',
                    'STATUS': ''
                })
                
            return df
                
        except Exception as e:
            st.error(f"Erro ao executar query: {str(e)}")
            return None

    def get_table_names(self) -> list:
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
                tables = [row['table_name'] for row in cur.fetchall()]
                return tables
        except Exception as e:
            st.error(f"Erro ao listar tabelas: {str(e)}")
            return []