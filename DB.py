import pandas as pd
import streamlit as st
from supabase.client import create_client
from datetime import datetime, timedelta

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
            
            # Extrair o período da query
            if "INTERVAL" in query:
                dias = int(query.split("INTERVAL '")[1].split(" days")[0])
                data_limite = datetime.now() - timedelta(days=dias)
                data_limite_str = data_limite.strftime("%Y-%m-%d")
            else:
                data_limite_str = "1900-01-01"  # Data antiga para pegar todos os registros
            
            # Fazer a consulta usando a API do Supabase
            response = (self.supabase
                .table("Basic")
                .select("*")
                .gte("DATA", data_limite_str)
                .order("DATA", desc=True)
                .execute())
            
            if response.data:
                df = pd.DataFrame(response.data)
                return df
            return None
        except Exception as e:
            st.error(f"Erro ao executar query: {str(e)}")
            return None

    def get_table_names(self) -> list:
        try:
            tables = self.supabase.table("Basic").select("*").limit(1).execute()
            return ["Basic"] if tables else []
        except:
            return []