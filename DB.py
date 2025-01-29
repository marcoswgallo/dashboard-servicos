import psycopg2
import pandas as pd
from typing import Optional
import streamlit as st
from urllib.parse import quote_plus

class DatabaseConnection:
    def __init__(self):
        try:
            # Tentar pegar as configurações do Streamlit primeiro
            self.config = {
                'host': st.secrets['postgres']['host'],
                'port': st.secrets['postgres']['port'],
                'database': st.secrets['postgres']['database'],
                'user': st.secrets['postgres']['user'],
                'password': st.secrets['postgres']['password']
            }
        except Exception as e:
            # Se não encontrar no Streamlit, usar configuração local
            password = quote_plus('RNupTzhk6d-3SZC')
            self.config = {
                'host': 'db.vdmzeeewpzfpgmnaabfw.supabase.co',
                'port': 5432,
                'database': 'postgres',
                'user': 'postgres',
                'password': password
            }
        
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(**self.config)
            self.cursor = self.conn.cursor()
            print("Conexão bem sucedida!")
        except Exception as e:
            print(f"Erro ao conectar ao banco de dados: {e}")

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
            print(f"Erro ao executar query: {e}")
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