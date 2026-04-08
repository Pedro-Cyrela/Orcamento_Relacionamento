# Comparador de Previsões Orçamentárias

Versão corrigida da primeira entrega.

## Correção aplicada
A biblioteca agora aceita `subtipo_gasto` e `regra_observacao` como colunas opcionais em `Biblioteca_Map`.
Se essas colunas não existirem, o app preenche automaticamente com valores padrão e segue o processamento.

## Como rodar
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Arquivos principais para ajuste
- `services/library_service.py`: validação e leitura da biblioteca
- `services/excel_reader.py`: heurísticas de leitura das previsões
- `assets/styles.css`: visual
