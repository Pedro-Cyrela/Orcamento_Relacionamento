from __future__ import annotations

from pathlib import Path

import streamlit as st

from services.comparison_service import ComparisonService
from services.excel_reader import ForecastReader
from services.export_service import ExportService
from services.library_service import LibraryService
from services.standardizer import StandardizerService
from utils.helpers import AppError, ensure_excel_file
from ui.components import UIComponents

st.set_page_config(
    page_title="Comparador de Previsões Orçamentárias",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def load_css() -> None:
    css_path = Path(__file__).parent / "assets" / "styles.css"
    UIComponents.inject_css(css_path.read_text(encoding="utf-8"))


def init_state() -> None:
    defaults = {
        "library_data": None,
        "library_status_label": "Biblioteca não carregada",
        "library_status_class": "status-warning",
        "library_messages": [],
        "processed_forecasts": [],
        "comparison_result": None,
        "comparison_target_index": 1,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def process_inputs(library_file, forecast_files) -> None:
    st.session_state.processed_forecasts = []
    st.session_state.comparison_result = None
    st.session_state.library_messages = []

    if library_file is None:
        st.session_state.library_status_label = "Biblioteca não carregada"
        st.session_state.library_status_class = "status-warning"
        return

    library_data = LibraryService.load_library(library_file)
    st.session_state.library_data = library_data
    st.session_state.library_messages = library_data.warnings
    st.session_state.library_status_label = "Biblioteca carregada com sucesso"
    st.session_state.library_status_class = "status-success"

    processed = []
    for index, file in enumerate(forecast_files, start=1):
        ensure_excel_file(file.name)
        raw_forecast = ForecastReader.read_forecast(file)
        forecast = StandardizerService.standardize(
            raw_forecast=raw_forecast,
            library=library_data,
            forecast_id=f"forecast_{index}",
            label=f"Previsão {index}",
        )
        processed.append(forecast)

    st.session_state.processed_forecasts = processed
    if len(processed) >= 2:
        target_idx = min(st.session_state.comparison_target_index, len(processed) - 1)
        st.session_state.comparison_target_index = target_idx
        st.session_state.comparison_result = ComparisonService.compare(processed[0], processed[target_idx])


def main() -> None:
    load_css()
    init_state()

    UIComponents.render_top_bar(
        st.session_state.library_status_label,
        st.session_state.library_status_class,
    )

    top_left, top_mid, top_right = st.columns([1.2, 1, 1.2])
    with top_left:
        num_comparisons = st.number_input(
            "Número de Comparações",
            min_value=2,
            max_value=6,
            value=2,
            step=1,
            help="Quantidade de previsões Excel que serão carregadas e comparadas.",
        )
    with top_mid:
        library_file = st.file_uploader(
            "Carregar Biblioteca",
            type=["xlsx"],
            accept_multiple_files=False,
            help="Envie a biblioteca com as abas Tipos_Padrao e Biblioteca_Map.",
        )
    with top_right:
        template_bytes = LibraryService.build_default_template()
        st.download_button(
            "Baixar modelo de biblioteca",
            data=template_bytes,
            file_name="modelo_biblioteca_orcamento.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    forecast_files = st.file_uploader(
        "Selecione as previsões orçamentárias",
        type=["xlsx"],
        accept_multiple_files=True,
        help="Envie pelo menos duas previsões. O nome ideal do arquivo é 'Administradora - Empreendimento.xlsx'.",
    )

    process_triggered = False
    if library_file and forecast_files:
        if len(forecast_files) < num_comparisons:
            st.info(f"Envie pelo menos {num_comparisons} arquivos para iniciar a análise.")
        else:
            try:
                process_inputs(library_file, forecast_files[:num_comparisons])
                process_triggered = True
            except AppError as exc:
                st.session_state.library_status_label = "Erro de validação"
                st.session_state.library_status_class = "status-error"
                st.error(str(exc))
            except Exception as exc:  # pragma: no cover
                st.session_state.library_status_label = "Erro inesperado"
                st.session_state.library_status_class = "status-error"
                st.error(f"Ocorreu um erro inesperado ao processar os arquivos: {exc}")
    else:
        st.caption("Carregue a biblioteca e as previsões para habilitar todas as análises.")

    forecasts = st.session_state.processed_forecasts
    comparison = st.session_state.comparison_result

    if forecasts:
        left_col, right_col = st.columns([1.9, 1.1], gap="large")
        with left_col:
            forecast_cols = st.columns(2, gap="large") if len(forecasts) > 1 else [st.container()]
            for idx, forecast in enumerate(forecasts):
                target = forecast_cols[idx % len(forecast_cols)]
                with target:
                    UIComponents.render_forecast_card(forecast)
                    UIComponents.render_alerts(forecast.warnings, title=f"Avisos — {forecast.label}")

        with right_col:
            if len(forecasts) > 2:
                options = {forecast.label: index for index, forecast in enumerate(forecasts) if index > 0}
                selected_label = st.selectbox(
                    "Comparar contra a base (Previsão 1)",
                    options=list(options.keys()),
                    index=min(st.session_state.comparison_target_index - 1, len(options) - 1),
                )
                st.session_state.comparison_target_index = options[selected_label]
                comparison = ComparisonService.compare(forecasts[0], forecasts[st.session_state.comparison_target_index])
                st.session_state.comparison_result = comparison
            if comparison is not None:
                compared_label = forecasts[st.session_state.comparison_target_index].label
                export_bytes = ExportService.build_excel_export(forecasts, comparison)
                button_col, spacer_col = st.columns([1, 1])
                with button_col:
                    st.download_button(
                        "Exportar para Excel",
                        data=export_bytes,
                        file_name="comparativo_previsoes.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
                UIComponents.render_comparison_panel(comparison, compared_label=compared_label)
                UIComponents.render_alerts(st.session_state.library_messages, title="Observações da biblioteca")

        UIComponents.render_unclassified_section(forecasts)

    elif process_triggered:
        st.warning("Os arquivos foram lidos, mas nenhuma linha comparável foi encontrada.")


if __name__ == "__main__":
    main()
