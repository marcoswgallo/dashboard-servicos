import pandas as pd
import time

def excel_to_csv():
    """Converte Excel para CSV para importação no PythonAnywhere"""
    try:
        print(" Iniciando conversão Excel para CSV...")
        start_time = time.time()
        
        print(" Lendo arquivo Excel...")
        # Ler o Excel
        df = pd.read_excel(
            "data/servicos.xlsx",
            parse_dates=["DATA_TOA"]
        )
        
        print(f" Encontrados {len(df)} registros")
        
        # Renomear colunas para o padrão MySQL
        df = df.rename(columns={
            "LATIDUDE": "LATITUDE",
            "LONGITUDE": "LONGITUDE",
            "SERVIÇO": "SERVICO"
        })
        
        # Limpar dados
        print(" Limpando dados...")
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip()
        
        # Converter datas para formato MySQL
        df['DATA_TOA'] = df['DATA_TOA'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Salvar como CSV
        print(" Salvando arquivo CSV...")
        csv_path = "data/servicos_mysql.csv"
        df.to_csv(csv_path, index=False)
        
        end_time = time.time()
        print(f" Conversão concluída em {end_time - start_time:.2f} segundos!")
        print(f" Total de registros convertidos: {len(df)}")
        print("\nAgora você pode:")
        print("1. Fazer upload do arquivo 'data/servicos_mysql.csv' para o PythonAnywhere")
        print("2. No MySQL do PythonAnywhere, criar a tabela com:")
        print("""
CREATE TABLE servicos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    DATA_TOA DATETIME,
    TECNICO VARCHAR(100),
    CIDADES VARCHAR(100),
    SERVICO VARCHAR(200),
    STATUS VARCHAR(50),
    LATITUDE DECIMAL(10, 8),
    LONGITUDE DECIMAL(11, 8),
    INDEX idx_data_toa (DATA_TOA)
);
        """)
        print("3. Importar o CSV com:")
        print("""
LOAD DATA LOCAL INFILE 'servicos_mysql.csv'
INTO TABLE servicos
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\\n'
IGNORE 1 ROWS
(DATA_TOA, TECNICO, CIDADES, SERVICO, STATUS, LATITUDE, LONGITUDE);
        """)
        
    except Exception as e:
        print(f" Erro durante conversão: {str(e)}")

if __name__ == "__main__":
    excel_to_csv()
