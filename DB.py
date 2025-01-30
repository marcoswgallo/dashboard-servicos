import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from datetime import datetime
import time

class DatabaseConnection:
    def __init__(self):
        try:
            # Obter URL do banco do Streamlit Secrets
            self.url = st.secrets["postgres"]["url"]
            
            # Criar engine SQLAlchemy
            self.engine = create_engine(self.url, pool_size=5, max_overflow=10)
            
            # Testar conexão
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                st.success("✅ Conexão com Neon estabelecida com sucesso!")
                
            # Verificar range de datas disponível
            self.check_date_range()
            
        except Exception as e:
            st.error(f"❌ Erro ao conectar ao banco: {str(e)}")
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
        try:
            with _self.engine.connect() as conn:
                query = text("""
                    SELECT 
                        MIN("DATA_TOA")::timestamp as first_date,
                        MAX("DATA_TOA")::timestamp as last_date 
                    FROM basic
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
        empty_df = pd.DataFrame(columns=["DATA_TOA", "TECNICO", "CIDADES", "SERVIÇO", "STATUS", "LATIDUDE", "LONGITUDE"])
        
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
            
            # Query otimizada selecionando apenas as colunas necessárias
            query = text("""
                SELECT 
                    "DATA_TOA",
                    "TECNICO",
                    "CIDADES",
                    "SERVIÇO",
                    "STATUS",
                    "LATIDUDE",
                    "LONGITUDE",
                    "VALOR TÉCNICO",
                    "VALOR EMPRESA"
                FROM basic
                WHERE "DATA_TOA"::timestamp 
                    BETWEEN :start_date AND :end_date
                ORDER BY "DATA_TOA"
            """)
            
            # Mostrar indicador de progresso
            with st.spinner('Carregando dados...'):
                start_time = time.time()
                
                # Executar query
                with _self.engine.connect() as conn:
                    result = pd.read_sql_query(
                        query,
                        conn,
                        params={
                            "start_date": start.strftime("%Y-%m-%d %H:%M:%S"),
                            "end_date": end.strftime("%Y-%m-%d %H:%M:%S")
                        },
                        parse_dates=["DATA_TOA"]
                    )
                
                end_time = time.time()
                if not result.empty:
                    st.success(f"✅ Dados carregados em {end_time - start_time:.2f} segundos")
                else:
                    st.warning("⚠️ Nenhum dado encontrado para o período selecionado.")
                    return empty_df
            
            return result
            
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados: {str(e)}")
            return empty_df
    
    def get_table_names(self):
        """Retorna lista de tabelas no banco."""
        try:
            with self.engine.connect() as conn:
                query = text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                result = conn.execute(query)
                return [row[0] for row in result]
        except Exception as e:
            st.error(f"Erro ao listar tabelas: {str(e)}")
            return []
