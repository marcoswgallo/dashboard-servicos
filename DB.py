import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

class DatabaseConnection:
    def __init__(self):
        try:
            # Tentar conectar com Supabase
            url = st.secrets.supabase.url
            key = st.secrets.supabase.key
            
            self.supabase = create_client(url, key)
            st.success("✅ Conexão com Supabase estabelecida com sucesso!")
            
            # Verificar datas disponíveis
            self.check_date_range()
            
        except Exception as e:
            st.error(f"❌ Erro ao conectar ao banco de dados: {str(e)}")
            self.supabase = None
    
    def check_date_range(self):
        """Verifica a primeira e última data disponível no banco."""
        try:
            # Buscar primeira data (ordem ascendente)
            first_date = self.supabase.table('Basic').select('DATA').order('DATA', desc=False).limit(1).execute()
            # Buscar última data (ordem descendente)
            last_date = self.supabase.table('Basic').select('DATA').order('DATA', desc=True).limit(1).execute()
            
            if first_date.data and last_date.data:
                # Converter as datas para datetime
                self.first_date = pd.to_datetime(first_date.data[0]['DATA'], format='%d/%m/%Y %H:%M')
                self.last_date = pd.to_datetime(last_date.data[0]['DATA'], format='%d/%m/%Y %H:%M')
                
                st.info(f"📅 Dados disponíveis de {first_date.data[0]['DATA']} até {last_date.data[0]['DATA']}")
        except Exception as e:
            st.error(f"Erro ao verificar datas: {str(e)}")
            self.first_date = None
            self.last_date = None

    def convert_value(self, value):
        """Converte valor para float."""
        try:
            if isinstance(value, str):
                # Remove R$ e converte vírgula para ponto
                value = value.replace('R$', '').replace('.', '').replace(',', '.')
                return float(value)
            return value
        except:
            return 0

    def convert_date(self, date_str):
        """Converte string de data para datetime."""
        try:
            if pd.isna(date_str):
                return None
            # Tenta diferentes formatos de data
            for fmt in ['%d/%m/%Y %H:%M', '%d/%m/%Y']:
                try:
                    return pd.to_datetime(date_str, format=fmt)
                except:
                    continue
            return None
        except:
            return None

    def execute_query(self, data_inicio, data_fim):
        """
        Executa query no banco de dados.
        
        Args:
            data_inicio (str): Data inicial no formato YYYY-MM-DD ou DD/MM/YYYY
            data_fim (str): Data final no formato YYYY-MM-DD ou DD/MM/YYYY
            
        Returns:
            DataFrame: Resultado da query ou None se houver erro
        """
        @st.cache_data(ttl=300)  # Cache por 5 minutos
        def fetch_data(_supabase, _data_inicio, _data_fim, _first_date, _last_date):
            try:
                with st.spinner('🔄 Carregando dados do banco...'):
                    # Fazer a consulta usando a API do Supabase com paginação
                    all_data = []
                    page = 1
                    page_size = 10000  # Aumentado para 10k registros por página
                    
                    # Debug das datas recebidas
                    st.write(f"DEBUG - Data inicial recebida: {_data_inicio}")
                    st.write(f"DEBUG - Data final recebida: {_data_fim}")
                    
                    # Tentar converter as datas para o formato correto
                    try:
                        # Primeiro tenta formato ISO (YYYY-MM-DD)
                        data_inicio_dt = pd.to_datetime(_data_inicio)
                        data_fim_dt = pd.to_datetime(_data_fim)
                        st.write("DEBUG - Datas convertidas usando formato ISO")
                    except:
                        try:
                            # Depois tenta formato BR (DD/MM/YYYY)
                            data_inicio_dt = pd.to_datetime(_data_inicio, format='%d/%m/%Y')
                            data_fim_dt = pd.to_datetime(_data_fim, format='%d/%m/%Y')
                            st.write("DEBUG - Datas convertidas usando formato BR")
                        except Exception as e:
                            st.error(f"Erro ao converter datas. Use formato DD/MM/YYYY ou YYYY-MM-DD: {str(e)}")
                            return None
                    
                    # Validar se as datas estão dentro do período disponível
                    if data_inicio_dt < _first_date:
                        st.warning(f"⚠️ Data inicial ajustada para {_first_date.strftime('%d/%m/%Y %H:%M')} (primeiro registro disponível)")
                        data_inicio_dt = _first_date
                    
                    if data_fim_dt > _last_date:
                        st.warning(f"⚠️ Data final ajustada para {_last_date.strftime('%d/%m/%Y %H:%M')} (último registro disponível)")
                        data_fim_dt = _last_date
                    
                    # Converter para string no formato do banco (DD/MM/YYYY HH:MM)
                    data_inicio_str = data_inicio_dt.strftime('%d/%m/%Y %H:%M')
                    data_fim_str = data_fim_dt.strftime('%d/%m/%Y %H:%M')
                    
                    st.info(f"🔍 Buscando registros de {data_inicio_str} até {data_fim_str}")
                    
                    # Debug da query
                    st.write(f"DEBUG - Query com datas: DATA >= '{data_inicio_str}' AND DATA <= '{data_fim_str}'")
                    
                    while True:
                        # Calcular o offset
                        offset = (page - 1) * page_size
                        
                        # Debug da paginação
                        st.write(f"DEBUG - Carregando página {page} (offset: {offset}, limit: {page_size})")
                        
                        # Fazer a consulta para a página atual com filtro de data
                        response = (_supabase.table('Basic')
                                  .select('*')
                                  .gte('DATA', data_inicio_str)
                                  .lte('DATA', data_fim_str)
                                  .order('DATA')  # Ordenar por data para garantir consistência
                                  .range(offset, offset + page_size - 1)
                                  .execute())
                        
                        # Debug da resposta
                        if page == 1 and not response.data:
                            st.write("DEBUG - Primeira query não retornou dados")
                        elif page == 1:
                            st.write(f"DEBUG - Primeira data encontrada: {response.data[0]['DATA']}")
                            st.write(f"DEBUG - Última data encontrada: {response.data[-1]['DATA']}")
                            st.write(f"DEBUG - Total de registros na primeira página: {len(response.data)}")
                        
                        if not response.data:
                            if page == 1:
                                st.warning("Nenhum registro encontrado para o período")
                            break
                            
                        all_data.extend(response.data)
                        current_page_size = len(response.data)
                        
                        # Atualizar progresso
                        st.write(f"📥 Carregados {len(all_data):,} registros...")
                        
                        # Se retornou menos que page_size registros, chegamos ao fim
                        if current_page_size < page_size:
                            st.write(f"DEBUG - Última página carregada com {current_page_size} registros")
                            break
                            
                        page += 1
                
                return all_data
                    
            except Exception as e:
                st.error(f"Erro ao carregar dados: {str(e)}")
                return None
        
        try:
            if self.supabase is None:
                st.error("Cliente Supabase não inicializado")
                return None
            
            # Buscar dados com cache
            all_data = fetch_data(self.supabase, data_inicio, data_fim, self.first_date, self.last_date)
            
            if not all_data:
                st.warning("Nenhum dado encontrado para o período selecionado")
                return None
            
            with st.spinner('🔄 Processando dados...'):
                # Converter para DataFrame
                df = pd.DataFrame(all_data)
                
                # Converter valores monetários
                df['VALOR_TÉCNICO'] = df['VALOR TÉCNICO'].apply(self.convert_value)
                df['VALOR_EMPRESA'] = df['VALOR EMPRESA'].apply(self.convert_value)
                
                # Remover colunas originais
                df = df.drop(['VALOR TÉCNICO', 'VALOR EMPRESA'], axis=1)
                
                # Converter coordenadas para float
                df['LATIDUDE'] = pd.to_numeric(df['LATIDUDE'], errors='coerce')
                df['LONGITUDE'] = pd.to_numeric(df['LONGITUDE'], errors='coerce')
                
                # Converter data para datetime
                df['DATA'] = df['DATA'].apply(self.convert_date)
                
                # Remover registros com data inválida
                df = df.dropna(subset=['DATA'])
                
                # Ordenar por data
                df = df.sort_values('DATA', ascending=False)
                
                # Preencher valores nulos
                df = df.fillna({
                    'SERVIÇO': '',
                    'CIDADES': '',
                    'TECNICO': '',
                    'BASE': '',
                    'STATUS': ''
                })
                
                st.success(f"✅ {len(df):,} registros carregados com sucesso!")
                return df
                
        except Exception as e:
            st.error(f"Erro ao executar query: {str(e)}")
            return None

    def get_table_names(self) -> list:
        try:
            response = self.supabase.table('Basic').select('*').limit(1).execute()
            return ["Basic"] if response.data else []
        except Exception as e:
            st.error(f"Erro ao listar tabelas: {str(e)}")
            return []