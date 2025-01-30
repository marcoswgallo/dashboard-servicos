# Configuração no PythonAnywhere

## 1. Banco de Dados MySQL

1. Vá para a aba "Databases" no PythonAnywhere
2. Anote as informações do seu banco MySQL:
   - Host: `seuusername.mysql.pythonanywhere-services.com`
   - Username: `seuusername`
   - Password: (a senha que você definiu)

3. Crie um novo banco de dados:
   ```sql
   CREATE DATABASE dashboard_servicos CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

## 2. Configuração do Projeto

1. Vá para a aba "Files" e faça upload do seu projeto
   - Você pode usar o git clone: `git clone https://github.com/marcoswgallo/dashboard-servicos.git`

2. Crie o arquivo de secrets:
   ```bash
   mkdir -p .streamlit
   nano .streamlit/secrets.toml
   ```

3. Adicione as configurações do MySQL:
   ```toml
   [mysql]
   host = "seuusername.mysql.pythonanywhere-services.com"
   user = "seuusername"
   password = "sua-senha"
   database = "dashboard_servicos"
   ```

## 3. Instalação de Dependências

1. Vá para a aba "Consoles" e inicie um novo console Python 3.10
2. Navegue até a pasta do projeto:
   ```bash
   cd dashboard-servicos
   ```

3. Instale as dependências:
   ```bash
   pip3 install -r requirements.txt
   ```

## 4. Importação dos Dados

1. Certifique-se que o arquivo Excel está na pasta `data/`
2. Execute o script de importação:
   ```bash
   python3 import_to_mysql.py
   ```

## 5. Configuração do Web App

1. Vá para a aba "Web"
2. Clique em "Add a new web app"
3. Escolha "Manual configuration"
4. Selecione Python 3.10

5. Configure o WSGI file (`/var/www/seuusername_pythonanywhere_com_wsgi.py`):
   ```python
   import sys
   import streamlit.web.bootstrap
   
   # Adicione o caminho do seu projeto
   path = '/home/seuusername/dashboard-servicos'
   if path not in sys.path:
       sys.path.append(path)
   
   # Configurar variáveis de ambiente
   import os
   os.environ['STREAMLIT_SERVER_PORT'] = '8000'
   os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
   
   # Iniciar Streamlit
   def application(environ, start_response):
       streamlit.web.bootstrap.run('Home.py', '', [], [])
       return ['']
   ```

6. Configure os arquivos estáticos:
   - URL: /static/
   - Directory: /home/seuusername/dashboard-servicos/static

7. Reinicie o web app

## 6. Testando

1. Seu app estará disponível em: `https://seuusername.pythonanywhere.com`
2. Verifique os logs em caso de erro:
   - Error log
   - Server log
   - Access log

## 7. Atualizações

Para atualizar o projeto:
1. Pull as alterações do git
2. Reinicie o web app

Para atualizar os dados:
1. Atualize o arquivo Excel
2. Execute `python3 import_to_mysql.py`
