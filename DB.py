import psycopg2
import pandas as pd
from typing import Optional
import streamlit as st

class DatabaseConnection:
    def __init__(self):
        try:
            # Tentar carregar as configurações
            st.write("Verificando configurações...")
            if 'postgres' not in st.secrets:
                st.error("Configuração 'postgres' não encontrada nos secrets")
                return
            
            # Configurações do banco
            self.config = {
                'dbname': st.secrets.postgres.database,
                'user': st.secrets.postgres.user,
                'password': st.secrets.postgres.password,
                'host': st.secrets.postgres.host,
                'port': st.secrets.postgres.port
            }
            
            st.write(f"Tentando conectar em: {self.config['host']}:{self.config['port']}/{self.config['dbname']} com usuário {self.config['user']}")
            
        except Exception as e:
            st.error(f"Erro ao carregar configurações: {str(e)}")
            raise e
        
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            st.write("Iniciando conexão...")
            self.conn = psycopg2.connect(
                dbname=self.config['dbname'],
                user=self.config['user'],
                password=self.config['password'],
                host=self.config['host'],
                port=self.config['port']
            )
            self.cursor = self.conn.cursor()
            st.success("✅ Conexão bem sucedida!")
        except Exception as e:
            st.error(f"❌ Erro ao conectar ao banco de dados: {str(e)}")
            raise e

    def disconnect(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
                st.write("Conexão encerrada!")
        except Exception as e:
            st.error(f"Erro ao desconectar: {str(e)}")

    def execute_query(self, query: str) -> Optional[pd.DataFrame]:
        try:
            st.write("Executando query...")
            self.connect()
            self.cursor.execute(query)
            columns = [desc[0] for desc in self.cursor.description]
            data = self.cursor.fetchall()
            df = pd.DataFrame(data, columns=columns)
            st.success("✅ Query executada com sucesso!")
            return df
        except Exception as e:
            st.error(f"❌ Erro ao executar query: {str(e)}")
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