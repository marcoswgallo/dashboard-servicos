import pandas as pd
from sqlalchemy import create_engine, text, types
import streamlit as st
from datetime import datetime, timedelta

def parse_time(time_str):
    """Converte string de hora para timedelta."""
    try:
        if pd.isna(time_str):
            return None
        # Tenta converter diferentes formatos de hora
        formats = ['%H:%M:%S', '%H:%M', '%H']
        for fmt in formats:
            try:
                t = datetime.strptime(str(time_str), fmt)
                return timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
            except:
                continue
        return None
    except:
        return None

def clean_data(df):
    """Limpa e prepara os dados antes de importar para o banco."""
    try:
        # 1. Remover linhas completamente vazias
        df = df.dropna(how='all')
        
        # 2. Converter e padronizar tipos de dados
        
        # Datas
        df['DATA_TOA'] = pd.to_datetime(df['DATA_TOA'], format='%d/%m/%Y %H:%M', errors='coerce')
        df['DATA'] = pd.to_datetime(df['DATA'], format='%d/%m/%Y', errors='coerce')
        
        # Strings - Preencher nulos e padronizar
        string_columns = ['BASE', 'SERVIÇO', 'STATUS ATIVIDADE', 'STATUS', 'ENDEREÇO', 
                         'BAIRRO', 'CIDADES', 'TECNICO', 'LOGIN', 'LOCAL', 'PERIODO']
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].fillna('Não Especificado')
                df[col] = df[col].str.strip().str.title()
        
        # Coordenadas
        df['LATIDUDE'] = pd.to_numeric(df['LATIDUDE'], errors='coerce')
        df['LONGITUDE'] = pd.to_numeric(df['LONGITUDE'], errors='coerce')
        
        # Horários
        time_columns = ['INÍCIO', 'FIM', 'DESLOCAMENTO']
        for col in time_columns:
            if col in df.columns:
                df[col] = df[col].apply(parse_time)
        
        # Números inteiros
        int_columns = ['CONTRATO', 'OS', 'COD', 'COD STATUS', 'JOB COD']
        for col in int_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        # Valores monetários
        df['VALOR TÉCNICO'] = pd.to_numeric(df['VALOR TÉCNICO'], errors='coerce').fillna(0)
        df['VALOR EMPRESA'] = pd.to_numeric(df['VALOR EMPRESA'], errors='coerce').fillna(0)
        
        # 3. Remover linhas com datas inválidas (DATA_TOA é essencial)
        df = df.dropna(subset=['DATA_TOA'])
        
        # 4. Remover duplicatas
        df = df.drop_duplicates()
        
        # 5. Ordenar por data
        df = df.sort_values('DATA_TOA')
        
        # 6. Validar dados
        if len(df) == 0:
            st.error("❌ Nenhum dado válido após a limpeza")
            return None
            
        return df
        
    except Exception as e:
        st.error(f"❌ Erro ao limpar dados: {str(e)}")
        return None

def import_excel(file_path):
    """Importa dados do Excel para o banco PostgreSQL."""
    try:
        # Ler arquivo Excel
        df = pd.read_excel(file_path)
        st.success("✅ Arquivo Excel lido com sucesso!")
        
        # Mostrar preview dos dados originais
        st.subheader("📊 Preview dos Dados Originais")
        st.dataframe(df.head())
        
        # Limpar dados
        df_clean = clean_data(df)
        if df_clean is None:
            st.error("❌ Erro ao limpar os dados")
            return
            
        # Mostrar preview dos dados limpos
        st.subheader("🧹 Preview dos Dados Limpos")
        st.dataframe(df_clean.head())
        
        # Mostrar estatísticas
        st.subheader("📈 Estatísticas da Limpeza")
        stats = {
            "Total de Registros": len(df_clean),
            "Técnicos Únicos": len(df_clean['TECNICO'].unique()),
            "Cidades Atendidas": len(df_clean['CIDADES'].unique()),
            "Período dos Dados": f"{df_clean['DATA_TOA'].min().strftime('%d/%m/%Y')} até {df_clean['DATA_TOA'].max().strftime('%d/%m/%Y')}",
            "Total em Valor Técnico": f"R$ {df_clean['VALOR TÉCNICO'].sum():,.2f}",
            "Total em Valor Empresa": f"R$ {df_clean['VALOR EMPRESA'].sum():,.2f}"
        }
        for key, value in stats.items():
            st.write(f"**{key}:** {value}")
        
        # Conectar ao banco
        url = st.secrets["postgres"]["url"]
        engine = create_engine(url)
        
        # Criar tabela e importar dados
        with engine.connect() as conn:
            # Dropar tabela se existir
            conn.execute(text("DROP TABLE IF EXISTS basic"))
            
            # Criar nova tabela com os dados limpos
            df_clean.to_sql(
                'basic',
                conn,
                if_exists='replace',
                index=False,
                dtype={
                    'DATA_TOA': types.TIMESTAMP(timezone=False),
                    'DATA': types.TIMESTAMP(timezone=False),
                    'INÍCIO': types.Interval(),
                    'FIM': types.Interval(),
                    'DESLOCAMENTO': types.Interval(),
                    'VALOR TÉCNICO': types.Numeric(10, 2),
                    'VALOR EMPRESA': types.Numeric(10, 2),
                    'CONTRATO': types.Integer(),
                    'OS': types.Integer(),
                    'COD': types.Integer(),
                    'COD STATUS': types.Integer(),
                    'JOB COD': types.Integer(),
                }
            )
            
            # Criar índices para melhorar performance
            conn.execute(text("CREATE INDEX idx_data_toa ON basic (\"DATA_TOA\")"))
            conn.execute(text("CREATE INDEX idx_tecnico ON basic (\"TECNICO\")"))
            conn.execute(text("CREATE INDEX idx_cidades ON basic (\"CIDADES\")"))
            
            st.success("✅ Dados importados com sucesso para o banco!")
            
    except Exception as e:
        st.error(f"❌ Erro ao importar dados: {str(e)}")

if __name__ == "__main__":
    st.title("📥 Importador de Dados")
    
    uploaded_file = st.file_uploader("Escolha o arquivo Excel", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        if st.button("Importar Dados"):
            import_excel(uploaded_file)
