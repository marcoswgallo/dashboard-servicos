import pandas as pd
import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta

class DatabaseConnection:
    def __init__(self):
        self.supabase = None
        try:
            url: str = st.secrets["supabase"]["url"]
            key: str = st.secrets["supabase"]["key"]
            self.supabase: Client = create_client(url, key)
        except Exception as e:
            st.error(f"Erro ao inicializar cliente Supabase: {str(e)}")

    def execute_query(self, query_params):
        try:
            if self.supabase is None:
                st.error("Cliente Supabase não inicializado")
                return None
            
            # Extrair a data limite dos parâmetros
            data_limite = query_params.split("=")[1]
            
            # Fazer a consulta usando a API do Supabase
            response = self.supabase.table('Basic').select('*').execute()
            
            if not response.data:
                st.warning("Nenhum dado encontrado na tabela Basic")
                return None
                
            df = pd.DataFrame(response.data)
            
            # Debug: mostrar alguns exemplos de datas
            st.write("Exemplos de datas no banco:", df['DATA'].head().tolist())
            
            # Converter a coluna DATA para datetime usando parser flexível
            df['DATA'] = pd.to_datetime(df['DATA'], format='mixed', dayfirst=True)
            
            # Debug: mostrar datas convertidas
            st.write("Exemplos de datas convertidas:", df['DATA'].head().dt.strftime('%Y-%m-%d %H:%M').tolist())
            
            # Filtrar por data
            data_limite = pd.to_datetime(data_limite)
            df = df[df['DATA'] >= data_limite]
            
            # Ordenar por data
            df = df.sort_values('DATA', ascending=False)
            
            if len(df) == 0:
                st.warning("Nenhum dado encontrado após aplicar os filtros")
                return None
                
            return df
            
        except Exception as e:
            st.error(f"Erro ao executar query: {str(e)}")
            st.error("Detalhes do erro para debug:")
            st.error(str(e.__class__.__name__))
            st.error(str(e.__dict__))
            # Debug: mostrar o tipo de dados que estamos tentando converter
            if 'df' in locals():
                st.write("Tipo de dados na coluna DATA:", df['DATA'].dtype)
                st.write("Primeiros valores da coluna DATA:", df['DATA'].head().tolist())
            return None

    def get_table_names(self) -> list:
        try:
            response = self.supabase.table('Basic').select('*').limit(1).execute()
            return ["Basic"] if response.data else []
        except Exception as e:
            st.error(f"Erro ao listar tabelas: {str(e)}")
            return []