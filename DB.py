import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

class DatabaseConnection:
    def __init__(self):
        try:
            # Debug: mostrar todas as chaves disponíveis em st.secrets
            st.write("Chaves disponíveis:", st.secrets.to_dict())
            
            # Tentar conectar com Supabase
            url = st.secrets.supabase.url
            key = st.secrets.supabase.key
            
            self.supabase = create_client(url, key)
            st.success("✅ Conexão com Supabase estabelecida com sucesso!")
            
        except Exception as e:
            st.error(f"❌ Erro ao conectar ao banco de dados: {str(e)}")
            self.supabase = None

    def convert_value(self, value):
        """Converte valor para float."""
        try:
            if isinstance(value, str):
                # Remove R$ e converte vírgula para ponto
                value = value.replace('R$', '').replace('.', '').replace(',', '.')
                return float(value)
            return value
        except:
            return 0

    def convert_date(self, date_str):
        """Converte string de data para datetime."""
        try:
            if pd.isna(date_str):
                return None
            # Tenta diferentes formatos de data
            for fmt in ['%d/%m/%Y %H:%M', '%d/%m/%Y']:
                try:
                    return pd.to_datetime(date_str, format=fmt)
                except:
                    continue
            return None
        except:
            return None

    def execute_query(self, data_inicio, data_fim):
        """
        Executa query no banco de dados.
        
        Args:
            data_inicio (str): Data inicial no formato YYYY-MM-DD
            data_fim (str): Data final no formato YYYY-MM-DD
            
        Returns:
            DataFrame: Resultado da query ou None se houver erro
        """
        try:
            if self.supabase is None:
                st.error("Cliente Supabase não inicializado")
                return None
            
            # Fazer a consulta usando a API do Supabase
            response = self.supabase.table('Basic').select('*').execute()
            
            if not response.data:
                st.warning("Nenhum dado encontrado na tabela Basic")
                return None
            
            # Converter para DataFrame
            df = pd.DataFrame(response.data)
            
            # Debug: mostrar colunas disponíveis
            st.write("Colunas disponíveis:", df.columns.tolist())
            
            # Converter valores monetários
            df['VALOR_TÉCNICO'] = df['VALOR TÉCNICO'].apply(self.convert_value)
            df['VALOR_EMPRESA'] = df['VALOR EMPRESA'].apply(self.convert_value)
            
            # Remover colunas originais
            df = df.drop(['VALOR TÉCNICO', 'VALOR EMPRESA'], axis=1)
            
            # Converter coordenadas para float
            df['LATIDUDE'] = pd.to_numeric(df['LATIDUDE'], errors='coerce')
            df['LONGITUDE'] = pd.to_numeric(df['LONGITUDE'], errors='coerce')
            
            # Converter data para datetime
            df['DATA'] = df['DATA'].apply(self.convert_date)
            
            # Remover registros com data inválida
            df = df.dropna(subset=['DATA'])
            
            # Filtrar por data
            data_inicio_dt = pd.to_datetime(data_inicio)
            data_fim_dt = pd.to_datetime(data_fim)
            df = df[(df['DATA'].dt.date >= data_inicio_dt.date()) & 
                   (df['DATA'].dt.date <= data_fim_dt.date())]
            
            # Ordenar por data
            df = df.sort_values('DATA', ascending=False)
            
            # Preencher valores nulos
            df = df.fillna({
                'SERVIÇO': '',
                'CIDADES': '',
                'TECNICO': '',
                'BASE': '',
                'STATUS': ''
            })
            
            if len(df) == 0:
                st.warning("Nenhum dado encontrado para o período selecionado")
                return None
                
            return df
                
        except Exception as e:
            st.error(f"Erro ao executar query: {str(e)}")
            return None

    def get_table_names(self) -> list:
        try:
            response = self.supabase.table('Basic').select('*').limit(1).execute()
            return ["Basic"] if response.data else []
        except Exception as e:
            st.error(f"Erro ao listar tabelas: {str(e)}")
            return []