import psycopg2
import pandas as pd
import streamlit as st

class DatabaseConnection:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.config = {
            "dbname": st.secrets["dbname"],
            "user": st.secrets["user"],
            "password": st.secrets["password"],
            "host": st.secrets["host"],
            "port": st.secrets["port"],
            "connect_timeout": st.secrets.get("connect_timeout", 10)
        }

    def connect(self):
        try:
            self.connection = psycopg2.connect(**self.config)
            self.cursor = self.connection.cursor()
            return True
        except Exception as e:
            st.error(f"Erro ao conectar ao banco: {str(e)}")
            return False

    def disconnect(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
        except Exception as e:
            st.error(f"Erro ao desconectar: {str(e)}")

    def execute_query(self, query):
        try:
            if not self.connect():
                return None

            self.cursor.execute(query)
            columns = [desc[0] for desc in self.cursor.description]
            data = self.cursor.fetchall()
            
            if data:
                df = pd.DataFrame(data, columns=columns)
                return df
            return None
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