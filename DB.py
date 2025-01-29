import pandas as pd
import streamlit as st
from supabase import create_client

class DatabaseConnection:
    def __init__(self):
        self.supabase = None
        try:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
            self.supabase = create_client(url, key)
        except Exception as e:
            st.error(f"Erro ao inicializar cliente Supabase: {str(e)}")

    def execute_query(self, query):
        try:
            if self.supabase is None:
                return None
                
            # Executar a query usando o cliente Supabase
            response = self.supabase.rpc('execute_sql', {'query': query}).execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                return df
            return None
        except Exception as e:
            st.error(f"Erro ao executar query: {str(e)}")
            return None

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