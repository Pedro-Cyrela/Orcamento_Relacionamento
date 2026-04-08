# Implantação recomendada da biblioteca no projeto

## Pasta definida para o projeto
A biblioteca deve ficar em:

`app/data/biblioteca/biblioteca_padronizacao_gastos_modelo_v2.xlsx`

Essa foi a pasta escolhida para padronizar o carregamento logo na abertura do app.

## Arquivos que precisam ler a biblioteca
Neste pacote, já deixei os arquivos ajustados para esse caminho:

- `app/core/settings.py`
- `app/services/biblioteca_loader.py`
- `.env.example`
- `app/data/biblioteca/biblioteca_padronizacao_gastos_modelo_v2.xlsx`

## Como funciona
### 1) Caminho padrão
O app passa a procurar automaticamente em:

`app/data/biblioteca/biblioteca_padronizacao_gastos_modelo_v2.xlsx`

### 2) Sobrescrita opcional
Se você quiser mudar o local no futuro, basta configurar a variável:

`BIBLIOTECA_GASTOS_PATH`

### 3) Compatibilidade com arquivos antigos
O loader trata compatibilidade para evitar o erro de schema:
- se faltar `subtipo_gasto`, usa `tipo_gasto_padrao`
- se faltar `descricao_tipo`, usa `descricao_padrao`

## O que muda no projeto
Você deve substituir ou adicionar estes arquivos:

- `app/core/settings.py`
- `app/services/biblioteca_loader.py`
- `app/data/biblioteca/biblioteca_padronizacao_gastos_modelo_v2.xlsx`
- `.env.example` (opcional, mas recomendado)

## Onde salvar no GitHub
Suba exatamente mantendo a estrutura de pastas:

- `app/data/biblioteca/biblioteca_padronizacao_gastos_modelo_v2.xlsx`
- `app/core/settings.py`
- `app/services/biblioteca_loader.py`
- `.env.example`

## Como chamar no app
No ponto em que o sistema inicializa ou carrega os dados, use:

```python
from app.services.biblioteca_loader import carregar_biblioteca_padrao

biblioteca = carregar_biblioteca_padrao()
tipos_padrao = biblioteca["Tipos_Padrao"]
```

## Observação importante
Como eu não recebi o repositório do app, preparei a estrutura mais segura e comum para projetos Python.
Se o seu projeto usar outro layout, você pode manter a mesma lógica e apenas mover os arquivos para os diretórios equivalentes.
