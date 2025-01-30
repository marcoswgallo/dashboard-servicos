import pandas as pd
import streamlit as st
from datetime import datetime
import time
import os

class ExcelConnection:
    def __init__(self):
        try:
            # Caminho para o arquivo Excel
            self.file_path = "data/servicos.xlsx"
            
            # Verificar se o diretório existe
            os.makedirs("data", exist_ok=True)
            
            # Verificar se o arquivo existe
            if not os.path.exists(self.file_path):
                st.error("❌ Arquivo Excel não encontrado!")
                st.info("📁 Coloque o arquivo 'servicos.xlsx' na pasta 'data'")
                st.stop()
            
            st.success("✅ Arquivo Excel encontrado com sucesso!")
            
            # Verificar range de datas disponível
            self.check_date_range()
            
        except Exception as e:
            st.error(f"❌ Erro ao acessar arquivo Excel: {str(e)}")
            st.stop()
    
    @st.cache_data(ttl=3600)  # Cache por 1 hora
    def check_date_range(_self):
        """Verifica o range de datas disponível no Excel."""
        try:
            first_date, last_date = _self.get_date_range()
            st.info(f"📅 Dados disponíveis de {first_date.strftime('%d/%m/%Y %H:%M')} até {last_date.strftime('%d/%m/%Y %H:%M')}")
        except Exception as e:
            st.error(f"❌ Erro ao verificar datas: {str(e)}")
    
    @st.cache_data(ttl=3600)  # Cache por 1 hora
    def get_date_range(_self):
        """Retorna a primeira e última data disponível."""
        try:
            # Ler apenas a coluna de data para ser mais rápido
            dates = pd.read_excel(
                _self.file_path,
                usecols=["DATA_TOA"],
                parse_dates=["DATA_TOA"]
            )
            
            if dates.empty:
                return None, None
                
            return dates["DATA_TOA"].min(), dates["DATA_TOA"].max()
            
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
        """Busca dados do Excel."""
        try:
            # Converter datas
            start = _self.parse_date(start_date)
            end = _self.parse_date(end_date)
            
            if not start or not end:
                st.warning("⚠️ Datas inválidas fornecidas.")
                return pd.DataFrame()
            
            # Ajustar end_date para incluir todo o dia
            if len(end_date) <= 10:
                end = end.replace(hour=23, minute=59, second=59)
            
            # Mostrar indicador de progresso
            with st.spinner('Carregando dados...'):
                start_time = time.time()
                
                # Ler Excel
                df = pd.read_excel(
                    _self.file_path,
                    parse_dates=["DATA_TOA"]
                )
                
                # Filtrar por data
                df = df[
                    (df["DATA_TOA"] >= start) & 
                    (df["DATA_TOA"] <= end)
                ]
                
                # Ordenar por data
                df = df.sort_values("DATA_TOA")
                
                end_time = time.time()
                if not df.empty:
                    st.success(f"✅ Dados carregados em {end_time - start_time:.2f} segundos")
                else:
                    st.warning("⚠️ Nenhum dado encontrado para o período selecionado.")
                
                return df
                
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados: {str(e)}")
            return pd.DataFrame()
