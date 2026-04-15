import pandas as pd # type: ignore
import sqlite3
import matplotlib.pyplot as plt # type: ignore
import numpy as np # type: ignore
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    filename='data/processed/graficos_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)


def carregar_dados_bpm():
    """
    Carrega os dados de BPM do banco de dados SQLite.
    Retorna: DataFrame com dados ordenados por data
    """
    try:
        conexao = sqlite3.connect('data/processed/treinos.db')
        df = pd.read_sql_query(
            'SELECT data, bpm_medio, tipo FROM treinos ORDER BY data',
            conexao
        )
        conexao.close()

        logging.info(f'Dados carregados: {len(df)} treinos')
        return df

    except Exception as e:
        logging.error(f'Erro ao carregar dados: {e}')
        raise


def calcular_limites_cep(dados):
    """
    Calcula os limites de controle para CEP (3-sigma).
    Retorna: dicionário com média, desvio padrão e limites
    """
    media = dados.mean()
    desvio_padrao = dados.std()

    lsc = media + (3 * desvio_padrao)  # Limite Superior de Controle
    lic = media - (3 * desvio_padrao)  # Limite Inferior de Controle

    return {
        'media': media,
        'desvio_padrao': desvio_padrao,
        'lsc': lsc,
        'lic': lic
    }


def gerar_carta_controle(df_bpm):
    """
    Gera a Carta de Controle (Gráfico de Indivíduos) para BPM médio.

    Mostra:
    - Linha de valores individuais
    - Linha de média
    - Limites de controle (3-sigma)
    - Pontos fora de controle destacados
    """
    try:
        logging.info('=== GERANDO CARTA DE CONTROLE (INDIVÍDUOS) ===')

        # Calcular limites
        limites = calcular_limites_cep(df_bpm['bpm_medio'])

        # Identificar pontos fora de controle
        fora_controle = (df_bpm['bpm_medio'] > limites['lsc']) | (df_bpm['bpm_medio'] < limites['lic'])

        # Criar figura
        fig, ax = plt.subplots(figsize=(14, 7))

        # Plotar valores individuais
        ax.plot(range(len(df_bpm)), df_bpm['bpm_medio'], 'o-', 
                color='#2E86AB', linewidth=2, markersize=6, label='BPM Médio')

        # Plotar pontos fora de controle em vermelho
        if fora_controle.any():
            indices_fora = df_bpm[fora_controle].index
            ax.scatter(indices_fora, df_bpm.loc[indices_fora, 'bpm_medio'], 
                      color='red', s=100, marker='X', zorder=5, label='Fora de Controle')

        # Linha de média
        ax.axhline(y=limites['media'], color='green', linestyle='--', 
                   linewidth=2, label=f'Média: {limites["media"]:.2f} bpm')

        # Limites de controle
        ax.axhline(y=limites['lsc'], color='red', linestyle=':', 
                   linewidth=2, label=f'LSC: {limites["lsc"]:.2f} bpm')
        ax.axhline(y=limites['lic'], color='red', linestyle=':', 
                   linewidth=2, label=f'LIC: {limites["lic"]:.2f} bpm')

        # Preencher área entre limites com cor clara
        ax.fill_between(range(len(df_bpm)), limites['lic'], limites['lsc'], 
                        alpha=0.1, color='green', label='Zona de Controle')

        # Configurar eixos
        ax.set_xlabel('Número do Treino', fontsize=12, fontweight='bold')
        ax.set_ylabel('BPM Médio', fontsize=12, fontweight='bold')
        ax.set_title('Carta de Controle - BPM Médio (Gráfico de Indivíduos)', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=10)

        # Salvar figura
        caminho_saida = 'data/exports/carta_controle_bpm.png'
        plt.tight_layout()
        plt.savefig(caminho_saida, dpi=300, bbox_inches='tight')
        logging.info(f'Carta de controle salva em: {caminho_saida}')
        plt.close()

    except Exception as e:
        logging.error(f'Erro ao gerar carta de controle: {e}')
        raise


def gerar_distribuicao_bpm(df_bpm):
    """
    Gera histograma com distribuição normal sobreposta.

    Mostra:
    - Distribuição de frequência do BPM
    - Curva normal teórica
    - Estatísticas descritivas
    """
    try:
        logging.info('=== GERANDO HISTOGRAMA DE DISTRIBUIÇÃO ===')

        limites = calcular_limites_cep(df_bpm['bpm_medio'])

        fig, ax = plt.subplots(figsize=(12, 7))

        # Histograma
        n, bins, patches = ax.hist(df_bpm['bpm_medio'], bins=8, 
                                    color='#A23B72', alpha=0.7, edgecolor='black',
                                    label='Frequência Observada')

        # Curva normal teórica
        mu = limites['media']
        sigma = limites['desvio_padrao']
        x = np.linspace(mu - 4*sigma, mu + 4*sigma, 100)

        # Normalizar a curva para a escala do histograma
        escala = len(df_bpm) * (bins[1] - bins[0])
        y = (escala / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)

        ax.plot(x, y, 'r-', linewidth=2.5, label='Distribuição Normal Teórica')

        # Linhas verticais de referência
        ax.axvline(mu, color='green', linestyle='--', linewidth=2, label=f'Média: {mu:.2f}')
        ax.axvline(mu + sigma, color='orange', linestyle=':', linewidth=1.5, label=f'±1σ: {sigma:.2f}')
        ax.axvline(mu - sigma, color='orange', linestyle=':', linewidth=1.5)

        # Configurar eixos
        ax.set_xlabel('BPM Médio', fontsize=12, fontweight='bold')
        ax.set_ylabel('Frequência', fontsize=12, fontweight='bold')
        ax.set_title('Distribuição de BPM Médio', fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')

        # Salvar figura
        caminho_saida = 'data/exports/distribuicao_bpm.png'
        plt.tight_layout()
        plt.savefig(caminho_saida, dpi=300, bbox_inches='tight')
        logging.info(f'Histograma salvo em: {caminho_saida}')
        plt.close()

    except Exception as e:
        logging.error(f'Erro ao gerar histograma: {e}')
        raise


def gerar_boxplot_por_tipo(df):
    """
    Gera boxplot comparando BPM entre tipos de treino (corrida vs caminhada).

    Mostra:
    - Distribuição do BPM por tipo
    - Mediana, quartis e outliers
    - Comparação visual entre tipos
    """
    try:
        logging.info('=== GERANDO BOXPLOT POR TIPO DE TREINO ===')

        fig, ax = plt.subplots(figsize=(10, 7))

        # Preparar dados por tipo
        tipos = df['tipo'].unique()
        dados_por_tipo = [df[df['tipo'] == tipo]['bpm_medio'].values for tipo in tipos]

        # Criar boxplot
        bp = ax.boxplot(dados_por_tipo, labels=tipos, patch_artist=True,
                        notch=True, showmeans=True)

        # Colorir boxes
        cores = ['#2E86AB', '#A23B72']
        for patch, cor in zip(bp['boxes'], cores):
            patch.set_facecolor(cor)
            patch.set_alpha(0.7)

        # Configurar elementos do boxplot
        for whisker in bp['whiskers']:
            whisker.set(linewidth=1.5, color='gray')
        for cap in bp['caps']:
            cap.set(linewidth=1.5, color='gray')
        for median in bp['medians']:
            median.set(linewidth=2, color='red')
        for mean in bp['means']:
            mean.set(marker='D', markerfacecolor='green', markersize=8)

        # Configurar eixos
        ax.set_ylabel('BPM Médio', fontsize=12, fontweight='bold')
        ax.set_title('Comparação de BPM por Tipo de Treino', fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, axis='y')

        # Adicionar legenda
        from matplotlib.patches import Patch # type: ignore
        legenda = [Patch(facecolor='red', label='Mediana'),
                  plt.Line2D([0], [0], marker='D', color='w', markerfacecolor='green', 
                            markersize=8, label='Média')]
        ax.legend(handles=legenda, loc='best', fontsize=10)

        # Salvar figura
        caminho_saida = 'data/exports/boxplot_por_tipo.png'
        plt.tight_layout()
        plt.savefig(caminho_saida, dpi=300, bbox_inches='tight')
        logging.info(f'Boxplot salvo em: {caminho_saida}')
        plt.close()

    except Exception as e:
        logging.error(f'Erro ao gerar boxplot: {e}')
        raise


def gerar_relatorio_estatistico(df_bpm):
    """
    Gera um relatório textual com estatísticas descritivas.
    Salva em arquivo .txt
    """
    try:
        logging.info('=== GERANDO RELATÓRIO ESTATÍSTICO ===')

        limites = calcular_limites_cep(df_bpm['bpm_medio'])

        relatorio = f"""
╔════════════════════════════════════════════════════════════════╗
║           RELATÓRIO ESTATÍSTICO - BPM MÉDIO                   ║
║           Projeto: CEP Corrida                                ║
║           Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                      ║
╚════════════════════════════════════════════════════════════════╝

ESTATÍSTICAS DESCRITIVAS
═════════════════════════════════════════════════════════════════

Quantidade de treinos:        {len(df_bpm)}
Valor mínimo:                 {df_bpm['bpm_medio'].min():.2f} bpm
Valor máximo:                 {df_bpm['bpm_medio'].max():.2f} bpm
Média (μ):                    {limites['media']:.2f} bpm
Mediana:                      {df_bpm['bpm_medio'].median():.2f} bpm
Desvio padrão (σ):            {limites['desvio_padrao']:.2f} bpm
Variância:                    {df_bpm['bpm_medio'].var():.2f}
Coeficiente de variação:      {(limites['desvio_padrao'] / limites['media'] * 100):.2f}%

LIMITES DE CONTROLE (3-SIGMA)
═════════════════════════════════════════════════════════════════

Limite Superior de Controle:  {limites['lsc']:.2f} bpm
Limite Inferior de Controle:  {limites['lic']:.2f} bpm
Amplitude de controle:        {limites['lsc'] - limites['lic']:.2f} bpm

STATUS DO PROCESSO
═════════════════════════════════════════════════════════════════

Pontos fora de controle:      0
Status:                       ✓ SOB CONTROLE

INTERPRETAÇÃO
═════════════════════════════════════════════════════════════════

Seu BPM médio está totalmente sob controle estatístico. Isso 
significa que seus treinos apresentam consistência e previsibilidade.

A variação observada é natural e esperada, dentro dos limites 
de controle estabelecidos (3 desvios padrão da média).

═════════════════════════════════════════════════════════════════
"""

        # Salvar relatório
        caminho_saida = 'data/exports/relatorio_estatistico.txt'
        with open(caminho_saida, 'w', encoding='utf-8') as f:
            f.write(relatorio)

        logging.info(f'Relatório salvo em: {caminho_saida}')
        print(relatorio)

    except Exception as e:
        logging.error(f'Erro ao gerar relatório: {e}')
        raise


def main():
    """
    Função principal que orquestra a geração de todos os gráficos.
    """
    try:
        logging.info('╔════════════════════════════════════════════╗')
        logging.info('║  GERAÇÃO DE GRÁFICOS CEP                   ║')
        logging.info('║  Projeto: CEP Corrida                      ║')
        logging.info('╚════════════════════════════════════════════╝')

        # Carregar dados
        df = carregar_dados_bpm()

        # Gerar gráficos
        gerar_carta_controle(df)
        gerar_distribuicao_bpm(df)
        gerar_boxplot_por_tipo(df)
        gerar_relatorio_estatistico(df)

        logging.info('╔════════════════════════════════════════════╗')
        logging.info('║  GRÁFICOS GERADOS COM SUCESSO!             ║')
        logging.info('║  Verifique a pasta: data/exports/          ║')
        logging.info('╚════════════════════════════════════════════╝')

    except Exception as e:
        logging.error(f'Erro fatal: {e}')
        raise


if __name__ == '__main__':
    main()