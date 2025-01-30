import pandas as pd
import pymysql
from sqlalchemy import create_engine
import streamlit as st
import time

def import_excel_to_mysql():
    try:
        print("🔄 Iniciando importação...")
        start_time = time.time()
        
        # Ler configurações do MySQL
        db_config = st.secrets["mysql"]
        
        # Criar string de conexão
        connection_string = (
            f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}/{db_config['database']}"
        )
        
        # Criar engine
        engine = create_engine(connection_string)
        
        print("📊 Lendo arquivo Excel...")
        # Ler o Excel
        df = pd.read_excel(
            "data/servicos.xlsx",
            parse_dates=["DATA_TOA"]
        )
        
        print(f"📝 Encontrados {len(df)} registros")
        
        # Renomear colunas para o padrão MySQL
        df = df.rename(columns={
            "LATIDUDE": "LATITUDE",
            "LONGITUDE": "LONGITUDE",
            "SERVIÇO": "SERVICO"
        })
        
        # Limpar dados
        print("🧹 Limpando dados...")
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip()
        
        # Criar tabela e importar dados
        print("⬆️ Importando dados para o MySQL...")
        df.to_sql(
            'servicos',
            engine,
            if_exists='replace',
            index=False,
            chunksize=1000
        )
        
        # Criar índice
        with engine.connect() as conn:
            conn.execute("CREATE INDEX idx_data_toa ON servicos(DATA_TOA);")
            conn.execute("ALTER TABLE servicos ADD PRIMARY KEY (id);")
            
        end_time = time.time()
        print(f"✅ Importação concluída em {end_time - start_time:.2f} segundos!")
        print(f"📊 Total de registros importados: {len(df)}")
        
    except Exception as e:
        print(f"❌ Erro durante importação: {str(e)}")

if __name__ == "__main__":
    import_excel_to_mysql()
