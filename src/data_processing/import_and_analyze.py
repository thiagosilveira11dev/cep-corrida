import pandas as pd # type: ignore
import sqlite3
from datetime import datetime
import os
import logging

# Configurar logging para rastrear validações e erros
logging.basicConfig(
    filename='data/processed/import_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Também exibir logs no console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)


def criar_banco():
    """
    Cria o banco de dados SQLite e as tabelas se não existirem.
    Tabelas: treinos e analise_cep
    """
    try:
        conexao = sqlite3.connect('data/processed/treinos.db')
        cursor = conexao.cursor()

        # Tabela de treinos (dados brutos importados)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS treinos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data DATE NOT NULL,
                distancia REAL NOT NULL,
                duracao_minutos REAL NOT NULL,
                velocidade_media REAL NOT NULL,
                ritmo_medio TEXT NOT NULL,
                passos INTEGER NOT NULL,
                bpm_medio INTEGER NOT NULL,
                cadencia INTEGER NOT NULL,
                comprimento_passo REAL NOT NULL,
                bpm_maximo INTEGER NOT NULL,
                ritmo_maximo TEXT NOT NULL,
                velocidade_maxima REAL NOT NULL,
                tipo TEXT NOT NULL,
                data_insercao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(data, tipo)
            )
        ''')

        # Tabela de análise CEP (resultados das análises)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analise_cep (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_analise DATE NOT NULL,
                metrica TEXT NOT NULL,
                valor_medio REAL NOT NULL,
                desvio_padrao REAL NOT NULL,
                limite_superior_controle REAL NOT NULL,
                limite_inferior_controle REAL NOT NULL,
                limite_superior_especificacao REAL,
                limite_inferior_especificacao REAL,
                status TEXT NOT NULL,
                quantidade_pontos INTEGER NOT NULL,
                data_insercao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conexao.commit()
        conexao.close()
        logging.info('Banco de dados criado/verificado com sucesso')

    except Exception as e:
        logging.error(f'Erro ao criar banco de dados: {e}')
        raise


def validar_csv(caminho_csv):
    """
    Valida o arquivo CSV antes de importar.
    Detecta automaticamente o separador (vírgula, ponto-e-vírgula ou tabulação).
    """
    anomalias = []

    try:
        # Verificar se arquivo existe
        if not os.path.exists(caminho_csv):
            logging.error(f'Arquivo não encontrado: {caminho_csv}')
            raise FileNotFoundError(f'Arquivo não encontrado: {caminho_csv}')

        # Detectar separador automaticamente
        with open(caminho_csv, 'r', encoding='utf-8') as f:
            primeira_linha = f.readline()

        if '\t' in primeira_linha:
            separador = '\t'
            logging.info('Separador detectado: Tabulação')
        elif ';' in primeira_linha:
            separador = ';'
            logging.info('Separador detectado: Ponto-e-vírgula')
        else:
            separador = ','
            logging.info('Separador detectado: Vírgula')

        # Ler CSV com separador detectado e quotechar para aspas duplas
        df = pd.read_csv(caminho_csv, sep=separador, quotechar='"')

        # Remover espaços extras dos nomes das colunas
        df.columns = df.columns.str.strip()

        logging.info(f'Arquivo CSV lido com sucesso: {len(df)} linhas')
        logging.info(f'Colunas encontradas: {df.columns.tolist()}')

        # Colunas esperadas
        colunas_esperadas = [
            'data', 'distancia', 'duracao', 'velocidade_media', 'ritmo_medio',
            'passos', 'bpm_medio', 'cadencia', 'comprimento_passo', 'bpm_maximo',
            'ritmo_maximo', 'velocidade_maxima', 'tipo'
        ]

        # Verificar colunas
        colunas_faltantes = [col for col in colunas_esperadas if col not in df.columns]
        if colunas_faltantes:
            logging.error(f'Colunas faltantes no CSV: {colunas_faltantes}')
            raise ValueError(f'Colunas faltantes: {colunas_faltantes}')

        # Validar dados linha por linha
        for idx, row in df.iterrows():
            linha = idx + 2  # +2 porque começa em 0 e tem header

            # Validar data (formato YYYY-MM-DD)
            try:
                pd.to_datetime(row['data'])
            except:
                anomalias.append(f'Linha {linha}: Data inválida ({row["data"]})')

            # Validar distância (deve ser > 0)
            if pd.isna(row['distancia']) or row['distancia'] <= 0:
                anomalias.append(f'Linha {linha}: Distância inválida ({row["distancia"]})')

            # Validar duração (formato HH:MM:SS)
            try:
                partes = str(row['duracao']).split(':')
                if len(partes) != 3:
                    anomalias.append(f'Linha {linha}: Duração com formato inválido ({row["duracao"]})')
            except:
                anomalias.append(f'Linha {linha}: Duração inválida ({row["duracao"]})')

            # Validar BPM médio (deve estar entre 40 e 220)
            if pd.isna(row['bpm_medio']) or row['bpm_medio'] < 40 or row['bpm_medio'] > 220:
                anomalias.append(f'Linha {linha}: BPM médio suspeito ({row["bpm_medio"]})')

            # Validar tipo (deve ser 'corrida' ou 'caminhada')
            if row['tipo'] not in ['corrida', 'caminhada']:
                anomalias.append(f'Linha {linha}: Tipo inválido ({row["tipo"]})')

        if anomalias:
            logging.warning(f'Total de anomalias encontradas: {len(anomalias)}')
            for anomalia in anomalias:
                logging.warning(f'  - {anomalia}')
        else:
            logging.info('Nenhuma anomalia encontrada na validação')

        return df, anomalias

    except Exception as e:
        logging.error(f'Erro ao validar CSV: {e}')
        raise


def converter_duracao_para_minutos(duracao_str):
    """
    Converte duração no formato HH:MM:SS para minutos decimais.
    Exemplo: '00:27:22' vira 27.37 minutos
    """
    try:
        partes = str(duracao_str).split(':')
        horas = int(partes[0])
        minutos = int(partes[1])
        segundos = int(partes[2])

        total_minutos = horas * 60 + minutos + segundos / 60
        return round(total_minutos, 2)
    except:
        logging.warning(f'Erro ao converter duração: {duracao_str}')
        return None


def verificar_duplicatas(df, conexao):
    """
    Verifica quais linhas do DataFrame já existem no banco de dados.
    Retorna: DataFrame com apenas dados novos (sem duplicatas)
    """
    cursor = conexao.cursor()

    # Buscar todas as datas e tipos já no banco
    cursor.execute('SELECT data, tipo FROM treinos')
    registros_existentes = set(cursor.fetchall())

    # Filtrar apenas dados novos
    df_novo = df[~df.apply(lambda row: (row['data'], row['tipo']) in registros_existentes, axis=1)]

    if len(df_novo) < len(df):
        duplicatas = len(df) - len(df_novo)
        logging.info(f'{duplicatas} linha(s) já existem no banco e serão ignoradas')
    else:
        logging.info(f'Nenhuma duplicata encontrada. {len(df_novo)} linha(s) serão importadas')

    return df_novo


def importar_dados(caminho_csv):
    """
    Importa dados do CSV para o banco de dados SQLite.
    Processa:
    - Validação de dados
    - Conversão de duração para minutos decimais
    - Verificação de duplicatas
    - Inserção no banco
    """
    try:
        logging.info('=== INICIANDO IMPORTAÇÃO DE DADOS ===')

        # Validar CSV
        df, anomalias = validar_csv(caminho_csv)

        # Converter duração para minutos decimais
        df['duracao_minutos'] = df['duracao'].apply(converter_duracao_para_minutos)

        # Conectar ao banco
        conexao = sqlite3.connect('data/processed/treinos.db')

        # Verificar duplicatas
        df_novo = verificar_duplicatas(df, conexao)

        if len(df_novo) == 0:
            logging.info('Nenhum dado novo para importar')
            conexao.close()
            return

        # Preparar dados para inserção
        cursor = conexao.cursor()

        for idx, row in df_novo.iterrows():
            try:
                cursor.execute('''
                    INSERT INTO treinos (
                        data, distancia, duracao_minutos, velocidade_media, ritmo_medio,
                        passos, bpm_medio, cadencia, comprimento_passo, bpm_maximo,
                        ritmo_maximo, velocidade_maxima, tipo
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['data'],
                    row['distancia'],
                    row['duracao_minutos'],
                    row['velocidade_media'],
                    row['ritmo_medio'],
                    row['passos'],
                    row['bpm_medio'],
                    row['cadencia'],
                    row['comprimento_passo'],
                    row['bpm_maximo'],
                    row['ritmo_maximo'],
                    row['velocidade_maxima'],
                    row['tipo']
                ))
            except Exception as e:
                logging.error(f'Erro ao inserir linha {idx + 2}: {e}')

        conexao.commit()
        logging.info(f'{len(df_novo)} linha(s) importada(s) com sucesso')
        conexao.close()

    except Exception as e:
        logging.error(f'Erro durante importação: {e}')
        raise


def analisar_cep_bpm():
    """
    Realiza análise de Controle Estatístico de Processos (CEP) no BPM médio.

    Calcula:
    - Média e desvio padrão
    - Limites de controle (3-sigma)
    - Status (sob controle ou fora de controle)
    - Armazena resultados na tabela analise_cep
    """
    try:
        logging.info('=== INICIANDO ANÁLISE CEP (BPM MÉDIO) ===')

        conexao = sqlite3.connect('data/processed/treinos.db')

        # Buscar dados de BPM do banco
        df_treinos = pd.read_sql_query('SELECT * FROM treinos', conexao)

        if len(df_treinos) == 0:
            logging.warning('Nenhum dado disponível para análise CEP')
            conexao.close()
            return

        # Calcular estatísticas
        bpm_dados = df_treinos['bpm_medio']
        media = bpm_dados.mean()
        desvio_padrao = bpm_dados.std()

        # Limites de controle (3-sigma)
        lsc = media + (3 * desvio_padrao)  # Limite Superior de Controle
        lic = media - (3 * desvio_padrao)  # Limite Inferior de Controle

        # Verificar pontos fora de controle
        pontos_fora = len(bpm_dados[(bpm_dados > lsc) | (bpm_dados < lic)])
        status = 'fora_de_controle' if pontos_fora > 0 else 'sob_controle'

        # Log das análises
        logging.info(f'Métrica: BPM Médio')
        logging.info(f'Quantidade de treinos: {len(df_treinos)}')
        logging.info(f'Média: {media:.2f} bpm')
        logging.info(f'Desvio padrão: {desvio_padrao:.2f} bpm')
        logging.info(f'Limite Superior de Controle (LSC): {lsc:.2f} bpm')
        logging.info(f'Limite Inferior de Controle (LIC): {lic:.2f} bpm')
        logging.info(f'Pontos fora de controle: {pontos_fora}')
        logging.info(f'Status: {status}')

        # Inserir resultados na tabela analise_cep
        cursor = conexao.cursor()
        cursor.execute('''
            INSERT INTO analise_cep (
                data_analise, metrica, valor_medio, desvio_padrao,
                limite_superior_controle, limite_inferior_controle,
                status, quantidade_pontos
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().date(),
            'bpm_medio',
            round(media, 2),
            round(desvio_padrao, 2),
            round(lsc, 2),
            round(lic, 2),
            status,
            len(df_treinos)
        ))

        conexao.commit()
        conexao.close()

        logging.info('Análise CEP armazenada no banco com sucesso')

    except Exception as e:
        logging.error(f'Erro durante análise CEP: {e}')
        raise


def main():
    """
    Função principal que orquestra todo o processo:
    1. Cria o banco de dados
    2. Importa dados do CSV
    3. Realiza análise CEP
    """
    try:
        logging.info('╔════════════════════════════════════════════╗')
        logging.info('║  SISTEMA DE IMPORTAÇÃO E ANÁLISE CEP       ║')
        logging.info('║  Projeto: CEP Corrida                      ║')
        logging.info('╚════════════════════════════════════════════╝')

        # Passo 1: Criar banco de dados
        criar_banco()

        # Passo 2: Importar dados
        importar_dados('data/raw/treinos_2026_raw.csv')

        # Passo 3: Análise CEP
        analisar_cep_bpm()

        logging.info('╔════════════════════════════════════════════╗')
        logging.info('║  PROCESSO CONCLUÍDO COM SUCESSO!           ║')
        logging.info('╚════════════════════════════════════════════╝')

    except Exception as e:
        logging.error(f'Erro fatal no processo: {e}')
        raise


if __name__ == '__main__':
    main()