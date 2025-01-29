import psycopg2
import pandas as pd
from typing import Optional
import streamlit as st
from urllib.parse import quote_plus

class DatabaseConnection:
    def __init__(self):
        try:
            # Tentar pegar as configurações do Streamlit
            password = st.secrets["postgres"]["password"]
            host = st.secrets["postgres"]["host"]
            port = st.secrets["postgres"]["port"]
            database = st.secrets["postgres"]["database"]
            user = st.secrets["postgres"]["user"]
            
            # Criar string de conexão
            self.connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            
            # Debug - Mostrar configurações (exceto senha)
            st.write(f"Debug - Tentando conectar em: {host}:{port}/{database} com usuário {user}")
            
        except Exception as e:
            st.error(f"Erro ao carregar configurações: {str(e)}")
            # Usar configuração local como fallback
            password = quote_plus('Basic@2024')
            self.connection_string = f"postgresql://postgres:{password}@db.vdmzeeewpzfpgmnaabfw.supabase.co:5432/postgres"
        
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(self.connection_string)
            self.cursor = self.conn.cursor()
            st.success("Conexão bem sucedida!")
        except Exception as e:
            st.error(f"Erro ao conectar ao banco de dados: {str(e)}")
            raise e

    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("Conexão encerrada!")

    def execute_query(self, query: str) -> Optional[pd.DataFrame]:
        try:
            self.connect()
            self.cursor.execute(query)
            columns = [desc[0] for desc in self.cursor.description]
            data = self.cursor.fetchall()
            return pd.DataFrame(data, columns=columns)
        except Exception as e:
            st.error(f"Erro ao executar query: {str(e)}")
            return None
        finally:
            self.disconnect()

    def get_table_names(self) -> list:
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        """
        df = self.execute_query(query)
        if df is not None:
            return df['table_name'].tolist()
        return []

    def get_table_columns(self, table_name: str) -> list:
        query = f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = '{table_name}'
        """
        df = self.execute_query(query)
        if df is not None:
            return df['column_name'].tolist()
        return []