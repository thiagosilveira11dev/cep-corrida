# CEP Corrida

Um projeto de análise de dados de treinos usando **Controle Estatístico de Processos (CEP)** nível iniciante.

# O que é este projeto?

Este projeto coleta dados de treinos (corridas e caminhadas) e realiza análises estatísticas para entender padrões no desempenho físico, especificamente focando no **BPM (batidas por minuto)** do coração, coletados através de um smartwatch.

# Objetivo

Aplicar conceitos de **CEP (Controle Estatístico de Processos)** para:
- Importar e validar dados de treinos
- Calcular limites de controle estatístico
- Gerar gráficos profissionais
- Identificar padrões e anomalias

# Estrutura do Projeto

cep-corrida
    data/
        exports/
        processed/
        raw/
    docs/
    notebooks/
    src/
        analysis/
        data_processing/
        database/
        visualization/
    .gitignore
    main.py
    README.md # Este arquivo
    requirements.txt

# Como usar

## 1. Instalar dependências

Abra o terminal na raiz do projeto e execute:

    pip install -r requirements.txt

## 2. Preparar os dados

Exporte os dados do treino do smartwatch em formato CSV e coloque o arquivo em:

    data/raw/treinos_2026_raw.csv

**Formato esperado:**
- Separador: ponto-e-vírgula (`;`)
- Colunas: data, distancia, duracao, velocidade_media, ritmo_medio, passos, bpm_medio, cadencia, 
           comprimento_passo, bpm_maximo, ritmo_maximo, velocidade_maxima, tipo
- Data: formato ISO (YYYY-MM-DD)
- Tipo: "corrida" ou "caminhada"

## 3. Executar a importação e análise

    python src/data_processing/import_and_analyze.py

Este script vai:
- Criar o banco de dados SQLite
- Validar os dados do CSV
- Importar os dados
- Realizar análise CEP do BPM médio
- Gerar log de execução em `data/processed/import_log.txt`

## 4. Gerar gráficos

    python src/data_processing/generate_graphics.py

Este script vai gerar:
- `carta_controle_bpm.png` - Gráfico de indivíduos com limites de controle
- `distribuicao_bpm.png` - Histograma com distribuição normal
- `boxplot_por_tipo.png` - Comparação entre corrida e caminhada
- `relatorio_estatistico.txt` - Relatório com estatísticas

Todos os arquivos são salvos em `data/exports/`

## O que você vai ver

### Carta de Controle
Mostra cada valor de BPM ao longo dos treinos, com:
- Linha de média
- Limites de controle (3-sigma)
- Pontos fora de controle destacados em vermelho

### Distribuição
Histograma mostrando como o BPM se distribui e se segue uma distribuição normal.

### Comparação por Tipo
Boxplot comparando BPM entre treinos de corrida e caminhada.

### Relatório Estatístico
Arquivo de texto com:
- Média e desvio padrão
- Limites de controle
- Status do processo (sob controle ou não)

## Exemplo de Resultado

    Quantidade de treinos: 26 Média (BPM): 129.00 Desvio padrão: 14.15 Limite Superior de Controle: 171.44 Limite Inferior de Controle: 86.56 Status: ✓ SOB CONTROLE

## Tecnologias Utilizadas

- **Python 3.12** - Linguagem de programação
- **Pandas** - Manipulação de dados
- **SQLite** - Banco de dados
- **Matplotlib** - Geração de gráficos
- **NumPy** - Cálculos numéricos

## Logs

Cada execução gera um arquivo de log:
- `data/processed/import_log.txt` - Log da importação
- `data/processed/graficos_log.txt` - Log da geração de gráficos

Verifique estes arquivos para entender o que aconteceu em cada execução.

## Validação de Dados

O script de importação valida automaticamente:
- Formato de data (YYYY-MM-DD)
- Distância > 0
- Duração no formato HH:MM:SS
- BPM entre 40 e 220
- Tipo é "corrida" ou "caminhada"

Anomalias encontradas são registradas no log, mas não impedem a importação.

## Próximos Passos

- [ ] Análise exploratória profunda (correlações, tendências)
- [ ] Testes estatísticos (comparação corrida vs caminhada)
- [ ] Previsões de BPM futuro
- [ ] Dashboard interativo

## Autor

Thiago - Projeto de aprendizado em análise de dados

## Licença

Este projeto é de uso pessoal e educacional.

---

**Última atualização:** Abril de 2026