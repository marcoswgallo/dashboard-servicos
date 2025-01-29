from DB import DatabaseConnection

# Criar instância da conexão
db = DatabaseConnection()

# Listar todas as tabelas
print("Tabelas disponíveis:")
tables = db.get_table_names()
for table in tables:
    print(f"\nTabela: {table}")
    # Listar colunas de cada tabela
    columns = db.get_table_columns(table)
    print("Colunas:", columns)
