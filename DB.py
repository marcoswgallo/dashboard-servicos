import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from datetime import datetime

class DatabaseConnection:
    def __init__(self):
        try:
            # Obter URL do banco do Streamlit Secrets
            self.url = st.secrets["postgres"]["url"]
            
            # Criar engine SQLAlchemy
            self.engine = create_engine(self.url)
            
            # Testar conexão
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                st.success("✅ Conexão com Neon estabelecida com sucesso!")
                
            # Verificar range de datas disponível
            self.check_date_range()
            
        except Exception as e:
            st.error(f"❌ Erro ao conectar ao banco: {str(e)}")
            st.stop()
    
    def check_date_range(self):
        """Verifica o range de datas disponível no banco."""
        try:
            with self.engine.connect() as conn:
                # Consulta para pegar primeira e última data
                query = text("""
                    SELECT 
                        MIN("DATA_TOA")::timestamp as first_date,
                        MAX("DATA_TOA")::timestamp as last_date 
                    FROM basic
                """)
                result = conn.execute(query).fetchone()
                
                if result and result[0] and result[1]:
                    first_date = result[0]
                    last_date = result[1]
                    
                    st.info(f"📅 Dados disponíveis de {first_date.strftime(%d/%m/%Y %H:%M)} "
                           f"até {last_date.strftime(%d/%m/%Y %H:%M)}")
                else:
                    st.warning("⚠️ Não foi possível determinar o range de datas disponível")
                
        except Exception as e:
            st.error(f"❌ Erro ao verificar datas: {str(e)}")
    
    def parse_date(self, date_str):
        """Converte string de data para datetime."""
        try:
            # Tenta diferentes formatos de data
            formats = [
                "%d/%m/%Y",
                "%d/%m/%Y %H:%M",
                "%Y-%m-%d",
                "%Y-%m-%d %H:%M:%S"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue
            
            raise ValueError(f"Formato de data inválido: {date_str}")
            
        except Exception as e:
            st.error(f"❌ Erro ao converter data: {str(e)}")
            return None
    
    def execute_query(self, start_date, end_date):
        """Executa query no banco de dados."""
        # Define as colunas padrão para DataFrame vazio
        empty_df = pd.DataFrame(columns=["DATA_TOA", "TECNICO", "CIDADES", "SERVIÇO", "STATUS", "LATIDUDE", "LONGITUDE"])
        
        try:
            # Converter datas
            start = self.parse_date(start_date)
            end = self.parse_date(end_date)
            
            if not start or not end:
                st.warning("⚠️ Datas inválidas fornecidas.")
                return empty_df
            
            # Ajustar end_date para incluir todo o dia
            if len(end_date) <= 10:  # Se não tem hora
                end = end.replace(hour=23, minute=59, second=59)
            
            # Query principal
            query = text("""
                SELECT *
                FROM basic
                WHERE "DATA_TOA"::timestamp 
                    BETWEEN :start_date AND :end_date
                ORDER BY "DATA_TOA"
            """)
            
            # Executar query
            with self.engine.connect() as conn:
                result = pd.read_sql_query(
                    query,
                    conn,
                    params={
                        "start_date": start.strftime("%Y-%m-%d %H:%M:%S"),
                        "end_date": end.strftime("%Y-%m-%d %H:%M:%S")
                    },
                    parse_dates=["DATA_TOA"]
                )
            
            if result.empty:
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
                    WHERE table_schema = "public"
                """)
                result = conn.execute(query)
                return [row[0] for row in result]
        except Exception as e:
            st.error(f"Erro ao listar tabelas: {str(e)}")
            return []
