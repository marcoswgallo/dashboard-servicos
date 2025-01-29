import psycopg2
import pandas as pd
from typing import Optional
import streamlit as st
from supabase import create_client, Client

class DatabaseConnection:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.supabase: Optional[Client] = None
        
        try:
            # Tentar carregar as configurações
            if 'supabase' not in st.secrets:
                st.error("❌ Configuração 'supabase' não encontrada nos secrets")
                return
            
            # Inicializar cliente Supabase
            supabase_url = st.secrets.supabase.url
            supabase_key = st.secrets.supabase.key
            self.supabase = create_client(supabase_url, supabase_key)
            
            # Configurações do banco
            self.config = {
                'dbname': 'postgres',
                'user': 'postgres.vdmzeeewpzfpgmnaabfw',
                'password': 'RNupTzhk6d-3SZC',
                'host': 'aws-0-sa-east-1.pooler.supabase.com',
                'port': 6543,
                'connect_timeout': 10
            }
            
            # Debug - mostrar configurações (exceto senha)
            st.write("Configurações de conexão:")
            safe_config = self.config.copy()
            safe_config['password'] = '****'
            st.write(safe_config)
            
        except Exception as e:
            st.error(f"❌ Erro ao carregar configurações: {str(e)}")
            self.config = None

    def connect(self):
        try:
            if self.config is None:
                st.error("❌ Configurações não inicializadas")
                return False
                
            st.write("Tentando conexão com o banco...")
            self.conn = psycopg2.connect(**self.config)
            self.cursor = self.conn.cursor()
            st.success("✅ Conexão estabelecida!")
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
            
            # Usar Supabase se disponível
            if self.supabase:
                try:
                    response = self.supabase.rpc('execute_sql', {'sql_query': query}).execute()
                    if response.data:
                        df = pd.DataFrame(response.data)
                        st.write(f"Registros retornados: {len(df)}")
                        return df
                except Exception as e:
                    st.warning(f"⚠️ Erro ao usar Supabase, tentando conexão direta: {str(e)}")
            
            # Fallback para conexão direta
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