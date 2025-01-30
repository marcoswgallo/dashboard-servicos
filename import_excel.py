import pandas as pd
from sqlalchemy import create_engine, text
import numpy as np
from datetime import datetime

def clean_data(df):
    """Limpa e prepara os dados antes de importar para o banco."""
    try:
        print("\nIniciando limpeza dos dados...")
        print(f"Colunas encontradas: {df.columns.tolist()}")
        
        # 1. Remover linhas completamente vazias
        print("\n1. Removendo linhas vazias...")
        df = df.dropna(how='all')
        print(f"Registros após remover linhas vazias: {len(df)}")
        
        # 2. Converter e padronizar tipos de dados
        print("\n2. Convertendo tipos de dados...")
        
        # Datas
        print("Convertendo datas...")
        df['DATA_TOA'] = pd.to_datetime(df['DATA_TOA'], format='%d/%m/%Y', errors='coerce')
        df['DATA'] = pd.to_datetime(df['DATA'], format='%d/%m/%Y %H:%M', errors='coerce')
        print(f"Datas válidas em DATA_TOA: {df['DATA_TOA'].notna().sum()}")
        print(f"Datas válidas em DATA: {df['DATA'].notna().sum()}")
        
        # Strings
        string_columns = ['BASE', 'SERVIÇO', 'STATUS ATIVIDADE', 'STATUS', 'ENDEREÇO', 
                         'BAIRRO', 'CIDADES', 'TECNICO', 'LOGIN', 'LOCAL', 'PERIODO']
        print("\nPadronizando strings...")
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].fillna('Não Especificado')
                df[col] = df[col].astype(str).str.strip().str.title()
                print(f"Coluna {col}: {df[col].nunique()} valores únicos")
        
        # Coordenadas
        print("\nConvertendo coordenadas...")
        df['LATIDUDE'] = pd.to_numeric(df['LATIDUDE'], errors='coerce')
        df['LONGITUDE'] = pd.to_numeric(df['LONGITUDE'], errors='coerce')
        print(f"Coordenadas válidas: {df['LATIDUDE'].notna().sum()}")
        
        # Horários
        print("\nConvertendo horários...")
        time_columns = ['INÍCIO', 'FIM', 'DESLOCAMENTO']
        for col in time_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format='%H:%M:%S', errors='coerce').dt.time
                df[col] = df[col].fillna(pd.Timestamp('00:00:00').time())
                print(f"Coluna {col}: {df[col].notna().sum()} valores válidos")
        
        # Números inteiros
        print("\nConvertendo números inteiros...")
        int_columns = ['CONTRATO', 'OS', 'COD', 'COD STATUS', 'JOB COD']
        for col in int_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                print(f"Coluna {col}: {df[col].nunique()} valores únicos")
        
        # Valores monetários
        print("\nConvertendo valores monetários...")
        df['VALOR TÉCNICO'] = pd.to_numeric(df['VALOR TÉCNICO'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df['VALOR EMPRESA'] = pd.to_numeric(df['VALOR EMPRESA'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        print(f"Soma VALOR TÉCNICO: R$ {df['VALOR TÉCNICO'].sum():,.2f}")
        print(f"Soma VALOR EMPRESA: R$ {df['VALOR EMPRESA'].sum():,.2f}")
        
        # 3. Remover linhas com datas inválidas
        print("\n3. Removendo linhas com datas inválidas...")
        df = df.dropna(subset=['DATA_TOA'])
        print(f"Registros após remover datas inválidas: {len(df)}")
        
        # 4. Remover duplicatas
        print("\n4. Removendo duplicatas...")
        df = df.drop_duplicates()
        print(f"Registros após remover duplicatas: {len(df)}")
        
        # 5. Ordenar por data
        print("\n5. Ordenando por data...")
        df = df.sort_values('DATA_TOA')
        
        if len(df) == 0:
            print("\n❌ Nenhum dado válido após a limpeza")
            return None
            
        print("\n✅ Limpeza concluída com sucesso!")
        return df
        
    except Exception as e:
        import traceback
        print(f"\n❌ Erro ao limpar dados: {str(e)}")
        print("Traceback completo:")
        print(traceback.format_exc())
        return None

def import_excel(file_path):
    """Importa dados do Excel para o banco PostgreSQL."""
    try:
        # Ler arquivo Excel
        df = pd.read_excel(file_path)
        print("✅ Arquivo Excel lido com sucesso!")
        print(f"Total de registros: {len(df)}")
        
        # Limpar dados
        df_clean = clean_data(df)
        if df_clean is None:
            print("❌ Erro ao limpar os dados")
            return
            
        # Mostrar estatísticas
        print("\n📈 Estatísticas da Limpeza:")
        stats = {
            "Total de Registros": len(df_clean),
            "Técnicos Únicos": len(df_clean['TECNICO'].unique()),
            "Cidades Atendidas": len(df_clean['CIDADES'].unique()),
            "Período dos Dados": f"{df_clean['DATA_TOA'].min().strftime('%d/%m/%Y')} até {df_clean['DATA_TOA'].max().strftime('%d/%m/%Y')}",
            "Total em Valor Técnico": f"R$ {df_clean['VALOR TÉCNICO'].sum():,.2f}",
            "Total em Valor Empresa": f"R$ {df_clean['VALOR EMPRESA'].sum():,.2f}"
        }
        for key, value in stats.items():
            print(f"{key}: {value}")
        
        # Conectar ao banco
        print("\nConectando ao banco Neon...")
        engine = create_engine("postgresql://neondb_owner:npg_6Vqm1EGWtnZd@ep-weathered-river-a8md0kfd-pooler.eastus2.azure.neon.tech/neondb")
        
        # Criar tabela e importar dados
        with engine.connect() as conn:
            print("Limpando tabela antiga...")
            conn.execute(text("DROP TABLE IF EXISTS basic"))
            
            print("Criando tabela...")
            conn.execute(text("""
                CREATE TABLE basic (
                    "DATA_TOA" timestamp without time zone,
                    "DATA" timestamp without time zone,
                    "BASE" text,
                    "SERVIÇO" text,
                    "AUDITADO" text,
                    "PDF" text,
                    "FOTO" text,
                    "COP REVERTEU" text,
                    "TIPO DE SERVIÇO" text,
                    "HABILIDADE DE TRABALHO" text,
                    "STATUS ATIVIDADE" text,
                    "STATUS" text,
                    "PACOTE" text,
                    "CLIENTE" text,
                    "ENDEREÇO" text,
                    "BAIRRO" text,
                    "CIDADES" text,
                    "LATIDUDE" double precision,
                    "LONGITUDE" double precision,
                    "NODE" text,
                    "TECNICO" text,
                    "LOGIN" text,
                    "SUPERVISOR" text,
                    "LOCAL" text,
                    "COP" text,
                    "PERIODO" text,
                    "INÍCIO" time without time zone,
                    "FIM" time without time zone,
                    "DESLOCAMENTO" time without time zone,
                    "CONTRATO" bigint,
                    "WO" text,
                    "OS" bigint,
                    "COD" integer,
                    "COD STATUS" integer,
                    "TIPO OS" text,
                    "JOB COD" integer,
                    "TIPO DE VALOR" text,
                    "VALOR TÉCNICO" numeric(10,2),
                    "VALOR EMPRESA" numeric(10,2),
                    "PONTO" text,
                    "TIPO RESIDÊNCIA" text
                )
            """))
            
            print("Importando dados...")
            # Usar to_sql do pandas para importar
            df_clean.to_sql('basic', conn, if_exists='append', index=False, method='multi', chunksize=1000)
            
            print("Criando índices...")
            conn.execute(text('CREATE INDEX idx_data_toa ON basic ("DATA_TOA")'))
            conn.execute(text('CREATE INDEX idx_tecnico ON basic ("TECNICO")'))
            conn.execute(text('CREATE INDEX idx_cidades ON basic ("CIDADES")'))
            
            print("✅ Dados importados com sucesso para o banco!")
            
    except Exception as e:
        import traceback
        print(f"\n❌ Erro ao importar dados: {str(e)}")
        print("Traceback completo:")
        print(traceback.format_exc())

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Uso: python import_excel.py <caminho_do_arquivo>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    import_excel(file_path)
