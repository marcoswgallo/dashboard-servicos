import pandas as pd
import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
import re

class DatabaseConnection:
    def __init__(self):
        self.supabase = None
        try:
            url: str = st.secrets["supabase"]["url"]
            key: str = st.secrets["supabase"]["key"]
            self.supabase: Client = create_client(url, key)
        except Exception as e:
            st.error(f"Erro ao inicializar cliente Supabase: {str(e)}")

    def clean_date(self, date_str):
        """Remove a hora da string de data se existir."""
        if pd.isna(date_str):
            return None
        # Remove qualquer coisa após um espaço (assumindo que é a hora)
        date_part = str(date_str).split(' ')[0]
        # Remove caracteres não numéricos exceto /
        date_part = re.sub(r'[^\d/]', '', date_part)
        return date_part

    def execute_query(self, data_limite):
        try:
            if self.supabase is None:
                st.error("Cliente Supabase não inicializado")
                return None
            
            # Fazer a consulta usando a API do Supabase
            response = self.supabase.table('Basic').select('*').execute()
            
            if not response.data:
                st.warning("Nenhum dado encontrado na tabela Basic")
                return None
                
            df = pd.DataFrame(response.data)
            
            # Debug: mostrar dados originais
            st.write("Primeiros registros originais:", df.head(2).to_dict('records'))
            
            # Limpar e converter datas
            df['DATA'] = df['DATA'].apply(self.clean_date)
            df['DATA'] = pd.to_datetime(df['DATA'], format='%d/%m/%Y', errors='coerce')
            
            # Remover registros com datas inválidas
            df = df.dropna(subset=['DATA'])
            
            # Debug: mostrar dados após conversão
            st.write("Primeiros registros após conversão:", df.head(2).to_dict('records'))
            
            # Converter data limite para datetime
            data_limite = pd.to_datetime(data_limite)
            
            # Filtrar por data
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
            if 'df' in locals():
                st.write("Exemplo de dados problemáticos:")
                problematic = df[pd.to_datetime(df['DATA'], format='%d/%m/%Y', errors='coerce').isna()]
                st.write(problematic['DATA'].head().tolist())
            return None

    def get_table_names(self) -> list:
        try:
            response = self.supabase.table('Basic').select('*').limit(1).execute()
            return ["Basic"] if response.data else []
        except Exception as e:
            st.error(f"Erro ao listar tabelas: {str(e)}")
            return []