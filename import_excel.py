import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text, types
from datetime import datetime

def convert_date(date_str):
    """Converte string de data para datetime."""
    if pd.isna(date_str):
        return None
        
    # Lista de formatos possíveis
    formats = [
        '%d/%m/%Y %H:%M',
        '%d/%m/%Y',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d'
    ]
    
    for fmt in formats:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except:
            continue
    
    return None

def main():
    try:
        # Ler o arquivo Excel
        print("Lendo arquivo Excel...")
        df = pd.read_excel('Relatorio_Financeiro (29).xlsx')
        
        # Renomear colunas para match com o banco
        print("Processando dados...")
        df.columns = [col.upper() for col in df.columns]
        
        # Converter DATA_TOA para datetime
        print("Convertendo datas...")
        df['DATA_TOA'] = df['DATA_TOA'].apply(convert_date)
        
        # Remover linhas com datas inválidas
        df = df.dropna(subset=['DATA_TOA'])
        
        # Criar engine SQLAlchemy
        print("Conectando ao banco...")
        engine = create_engine("postgresql://neondb_owner:npg_6Vqm1EGWtnZd@ep-weathered-river-a8md0kfd-pooler.eastus2.azure.neon.tech/neondb")
        
        # Primeiro, dropar a tabela se existir e criar nova com tipos corretos
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS basic"))
            conn.commit()
        
        # Criar tabela e importar dados
        print("Importando dados para o banco...")
        df.to_sql('basic', engine, if_exists='replace', index=False,
                  dtype={
                      'DATA_TOA': types.TIMESTAMP(timezone=False)
                  })
        
        print(f"✅ Importação concluída! {len(df)} registros importados.")
        
        # Criar índice para melhorar performance
        with engine.connect() as conn:
            conn.execute(text('CREATE INDEX idx_data_toa ON basic ("DATA_TOA")'))
            conn.commit()
            print("✅ Índice criado na coluna DATA_TOA")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")

if __name__ == "__main__":
    main()
