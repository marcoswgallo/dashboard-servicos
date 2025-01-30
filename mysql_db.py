import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from datetime import datetime
import time

class MySQLConnection:
    def __init__(self):
        try:
            # Configurações do MySQL (você vai precisar adicionar isso no secrets.toml)
            db_config = st.secrets["mysql"]
            
            # Criar string de conexão MySQL
            connection_string = (
                f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
                f"@{db_config['host']}/{db_config['database']}"
            )
            
            # Criar engine SQLAlchemy
            self.engine = create_engine(
                connection_string,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800  # Reconecta após 30 minutos
            )
            
            # Testar conexão
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                st.success("✅ Conexão com MySQL estabelecida com sucesso!")
                
            # Verificar range de datas disponível
            self.check_date_range()
            
        except Exception as e:
            st.error(f"❌ Erro ao conectar ao MySQL: {str(e)}")
            st.stop()
    
    @st.cache_data(ttl=3600)  # Cache por 1 hora
    def check_date_range(_self):
        """Verifica o range de datas disponível no banco."""
        try:
            first_date, last_date = _self.get_date_range()
            st.info(f"📅 Dados disponíveis de {first_date.strftime('%d/%m/%Y %H:%M')} até {last_date.strftime('%d/%m/%Y %H:%M')}")
        except Exception as e:
            st.error(f"❌ Erro ao verificar datas: {str(e)}")
    
    @st.cache_data(ttl=3600)  # Cache por 1 hora
    def get_date_range(_self):
        """Retorna a primeira e última data disponível."""
        try:
            with _self.engine.connect() as conn:
                query = text("""
                    SELECT 
                        MIN(DATA_TOA) as first_date,
                        MAX(DATA_TOA) as last_date 
                    FROM servicos
                """)
                result = conn.execute(query).fetchone()
                
                if result and result[0] and result[1]:
                    return result[0], result[1]
                else:
                    st.warning("⚠️ Não foi possível determinar o range de datas disponível")
                    return None, None
        except Exception as e:
            st.error(f"❌ Erro ao verificar datas: {str(e)}")
            return None, None
    
    def parse_date(self, date_str):
        """Converte string de data para datetime."""
        try:
            formats = ["%d/%m/%Y", "%d/%m/%Y %H:%M", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue
            raise ValueError(f"Formato de data inválido: {date_str}")
        except Exception as e:
            st.error(f"❌ Erro ao converter data: {str(e)}")
            return None
    
    @st.cache_data(ttl=300)  # Cache por 5 minutos
    def execute_query(_self, start_date, end_date):
        """Executa query no banco de dados com otimizações."""
        empty_df = pd.DataFrame(columns=["DATA_TOA", "TECNICO", "CIDADES", "SERVICO", "STATUS", "LATITUDE", "LONGITUDE"])
        
        try:
            # Converter datas
            start = _self.parse_date(start_date)
            end = _self.parse_date(end_date)
            
            if not start or not end:
                st.warning("⚠️ Datas inválidas fornecidas.")
                return empty_df
            
            # Ajustar end_date para incluir todo o dia
            if len(end_date) <= 10:
                end = end.replace(hour=23, minute=59, second=59)
            
            # Query otimizada
            query = text("""
                WITH filtered_data AS (
                    SELECT 
                        DATA_TOA,
                        TECNICO,
                        CIDADES,
                        SERVICO,
                        STATUS,
                        LATITUDE,
                        LONGITUDE
                    FROM servicos 
                    WHERE DATA_TOA BETWEEN :start_date AND :end_date
                    AND LATITUDE IS NOT NULL 
                    AND LONGITUDE IS NOT NULL
                )
                SELECT * FROM filtered_data
                ORDER BY DATA_TOA DESC
                LIMIT 1000
            """)
            
            # Mostrar indicador de progresso
            with st.spinner('Carregando dados...'):
                start_time = time.time()
                
                # Executar query
                with _self.engine.connect() as conn:
                    # Configurar a conexão para fetch mais rápido
                    conn.execution_options(stream_results=True)
                    
                    # Usar método mais eficiente de leitura
                    df = pd.read_sql_query(
                        query,
                        conn,
                        params={
                            "start_date": start.strftime("%Y-%m-%d %H:%M:%S"),
                            "end_date": end.strftime("%Y-%m-%d %H:%M:%S")
                        },
                        parse_dates=["DATA_TOA"]
                    )
                
                end_time = time.time()
                if not df.empty:
                    st.success(f"✅ Dados carregados em {end_time - start_time:.2f} segundos")
                else:
                    st.warning("⚠️ Nenhum dado encontrado para o período selecionado.")
                    return empty_df
            
            return df
            
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados: {str(e)}")
            return empty_df
