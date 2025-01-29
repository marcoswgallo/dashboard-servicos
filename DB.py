import psycopg2
import pandas as pd
from typing import Optional
import streamlit as st
from urllib.parse import quote_plus

class DatabaseConnection:
    def __init__(self):
        try:
            # Tentar carregar as configurações
            if 'postgres' not in st.secrets:
                st.error("❌ Configuração 'postgres' não encontrada nos secrets")
                return
            
            # Configurações do banco
            self.config = {
                'dbname': st.secrets.postgres.database,
                'user': st.secrets.postgres.user,
                'password': st.secrets.postgres.password,
                'host': st.secrets.postgres.host,
                'port': st.secrets.postgres.port,
                'connect_timeout': 10
            }
            
            # Debug - mostrar configurações (exceto senha)
            st.write("Configurações de conexão:")
            safe_config = self.config.copy()
            safe_config['password'] = '****'
            st.write(safe_config)
            
        except Exception as e:
            st.error(f"❌ Erro ao carregar configurações: {str(e)}")
            raise e
        
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            # Tentar conexão direta primeiro
            try:
                st.write("Tentando conexão principal...")
                self.conn = psycopg2.connect(**self.config)
                self.cursor = self.conn.cursor()
                st.success("✅ Conexão principal estabelecida!")
                return True
            except psycopg2.OperationalError as e:
                st.warning(f"⚠️ Erro na conexão principal: {str(e)}")
                # Se falhar, tentar conexão alternativa
                st.warning("⚠️ Tentando conexão alternativa...")
                password = quote_plus('RNupTzhk6d-3SZC')
                alt_config = {
                    'dbname': 'postgres',
                    'user': 'postgres',
                    'password': password,
                    'host': 'db.vdmzeeewpzfpgmnaabfw.supabase.co',
                    'port': 5432,
                    'connect_timeout': 10
                }
                self.conn = psycopg2.connect(**alt_config)
                self.cursor = self.conn.cursor()
                st.success("✅ Conexão alternativa estabelecida!")
                return True
                
        except Exception as e:
            st.error(f"❌ Erro ao conectar ao banco de dados: {str(e)}")
            return False

    def disconnect(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
                st.write("Conexão encerrada")
        except Exception as e:
            st.error(f"Erro ao desconectar: {str(e)}")

    def execute_query(self, query: str) -> Optional[pd.DataFrame]:
        try:
            st.write("Executando query:")
            st.code(query, language='sql')
            
            if not self.connect():
                st.error("❌ Não foi possível estabelecer conexão com o banco")
                return None
                
            self.cursor.execute(query)
            columns = [desc[0] for desc in self.cursor.description]
            data = self.cursor.fetchall()
            
            st.write(f"Registros retornados: {len(data)}")
            if len(data) == 0:
                st.warning("⚠️ A query não retornou nenhum resultado")
            
            df = pd.DataFrame(data, columns=columns)
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