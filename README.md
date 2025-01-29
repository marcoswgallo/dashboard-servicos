# Dashboard de Análise de Serviços

Este é um dashboard interativo desenvolvido com Streamlit para análise de serviços técnicos, oferecendo visualizações e insights operacionais.

## Funcionalidades

- 📊 Detalhamento de Técnicos
  - Análise de performance individual
  - Métricas de produtividade

- 🗺️ Mapa de Serviços
  - Visualização geográfica dos serviços
  - Análise de densidade por região
  - Insights operacionais
  - Métricas de performance

## Requisitos

- Python 3.8+
- Dependências listadas em `requirements.txt`

## Instalação

1. Clone o repositório:
```bash
git clone [URL_DO_SEU_REPOSITORIO]
cd ProjetoBasic
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente no arquivo `.streamlit/secrets.toml`:
```toml
[postgres]
host = "seu_host"
port = 5432
database = "seu_banco"
user = "seu_usuario"
password = "sua_senha"
```

## Executando o Dashboard

```bash
streamlit run streamlit_app.py
```

## Estrutura do Projeto

```
ProjetoBasic/
├── streamlit_app.py        # Aplicação principal
├── pages/                  # Páginas do dashboard
│   ├── 1_📊_Detalhamento_Tecnicos.py
│   └── 2_🗺️_Mapa_Servicos.py
├── DB.py                   # Conexão com banco de dados
├── requirements.txt        # Dependências do projeto
└── README.md              # Documentação
```

## Contribuindo

1. Faça um Fork do projeto
2. Crie sua Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a Branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request
