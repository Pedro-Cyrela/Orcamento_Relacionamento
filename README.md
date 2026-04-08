# Comparador de Previsões Orçamentárias

Aplicação em **Python + Streamlit** para comparar **2 ou mais previsões orçamentárias em Excel**, padronizando os gastos por uma biblioteca externa, consolidando valores e destacando diferenças entre cenários de **90 dias** e **cota plena**.

## O que a aplicação faz

- recebe múltiplos arquivos Excel de previsão
- extrai `administradora` e `empreendimento` pelo nome do arquivo
- lê uma biblioteca Excel com abas `Tipos_Padrao` e `Biblioteca_Map`
- padroniza as descrições originais de gastos
- consolida valores por tipo e subtipo padronizado
- compara previsões usando a **Previsão 1 como base**
- destaca diferenças negativas em verde e positivas em vermelho
- exibe detalhamento expansível por classificação
- exporta o comparativo para Excel
- mostra itens não classificados e avisos de validação

## Estrutura do projeto

```text
orcamento_comparador/
├── app.py
├── requirements.txt
├── README.md
├── .streamlit/
│   └── config.toml
├── assets/
│   └── styles.css
├── exports/
├── services/
│   ├── __init__.py
│   ├── comparison_service.py
│   ├── excel_reader.py
│   ├── export_service.py
│   ├── library_service.py
│   ├── models.py
│   └── standardizer.py
├── ui/
│   ├── __init__.py
│   └── components.py
└── utils/
    ├── __init__.py
    ├── constants.py
    ├── formatters.py
    └── helpers.py
```

## Como rodar localmente no VS Code

1. Crie e ative um ambiente virtual.
2. Instale as dependências.
3. Execute o Streamlit.

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Como usar

1. Defina o **Número de Comparações**.
2. Carregue a **biblioteca Excel**.
3. Faça upload das previsões.
4. Revise os cards de cada previsão.
5. Analise o painel **Diferença entre Previsões**.
6. Exporte o resultado pelo botão **Exportar para Excel**.

## Formato esperado do nome do arquivo

```text
Administradora - Empreendimento.xlsx
```

Exemplo:

```text
Protel - Living Wellness.xlsx
```

Se o nome estiver fora do padrão, o app continua funcionando, mas exibe um aviso amigável.

## Estrutura da biblioteca

### Aba obrigatória: `Tipos_Padrao`
Colunas mínimas:

- `id_tipo_gasto`
- `tipo_gasto_padrao`
- `subtipo_gasto`
- `descricao_tipo`
- `ativo`

### Aba obrigatória: `Biblioteca_Map`
Colunas mínimas:

- `administradora`
- `descricao_original`
- `id_tipo_gasto`
- `tipo_gasto_padrao`
- `subtipo_gasto`
- `regra_observacao`
- `ativo`

### Regras de mapeamento aplicadas

1. tenta `administradora + descricao_original`
2. se não encontrar, tenta regra geral com administradora vazia, `GERAL` ou equivalente
3. se ainda não encontrar, marca como **Não classificado**

## Observações importantes

- O parser foi preparado com base em layouts reais semelhantes aos arquivos enviados, incluindo formatos matriciais e layouts com apenas uma coluna principal de valores.
- Quando a planilha tiver apenas um campo principal de valor, a aplicação replica esse valor para `cota plena` e registra aviso.
- A aba `Template_Novos_Map` é ignorada no cálculo principal.
- As abas `Resumo` e `Instrucoes` são ignoradas no processamento.

## Arquivos para adaptar no futuro

### Ajustar visual/layout
Edite:

- `assets/styles.css`
- `ui/components.py`
- `app.py`

### Ajustar regras da biblioteca
Edite:

- `services/library_service.py`
- `utils/constants.py`

### Ajustar heurísticas de leitura dos Excels
Edite:

- `services/excel_reader.py`

## Deploy no Streamlit Community Cloud

O projeto já está preparado para deploy:

- `requirements.txt` incluído
- `.streamlit/config.toml` incluído
- app principal em `app.py`

No Streamlit Community Cloud, basta apontar o repositório e usar:

- **Main file path**: `app.py`

## Limitação conhecida desta primeira versão

Os arquivos enviados no workspace serviram como referência para os layouts de previsões. **Não foi encontrado um arquivo real de biblioteca junto aos uploads desta conversa**, então a lógica da biblioteca foi implementada a partir da especificação funcional fornecida. Para facilitar, o app inclui um botão para baixar um **modelo de biblioteca** pronto para preenchimento.
