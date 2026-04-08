from __future__ import annotations

import pandas as pd
import streamlit as st

from services.models import ComparisonResult, ForecastData
from utils.formatters import format_currency


class UIComponents:
    @staticmethod
    def inject_css(css_text: str) -> None:
        st.markdown(f"<style>{css_text}</style>", unsafe_allow_html=True)

    @staticmethod
    def render_top_bar(status_label: str, status_class: str) -> None:
        st.markdown(
            f"""
            <div class="topbar-card">
                <div>
                    <div class="app-title">Comparador de Previsões Orçamentárias</div>
                    <div class="app-subtitle">Padronize, consolide, compare e exporte previsões com visual corporativo.</div>
                </div>
                <div class="status-pill {status_class}">{status_label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def render_forecast_card(forecast: ForecastData) -> None:
        warning_html = ""
        if forecast.unclassified_data is not None and not forecast.unclassified_data.empty:
            warning_html = f'<span class="warning-badge">{len(forecast.unclassified_data)} não classificado(s)</span>'

        st.markdown(
            f"""
            <div class="section-card">
                <div class="card-header-row">
                    <div>
                        <div class="card-title">{forecast.label}</div>
                        <div class="card-meta">{forecast.filename}</div>
                    </div>
                    <div>{warning_html}</div>
                </div>
                <div class="meta-grid">
                    <div><span class="meta-label">Administradora</span><br>{forecast.administradora}</div>
                    <div><span class="meta-label">Empreendimento</span><br>{forecast.empreendimento}</div>
                    <div><span class="meta-label">Aba lida</span><br>{forecast.sheet_name}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        summary_df = forecast.consolidated_data.copy()
        summary_df["90 dias"] = summary_df["valor_90_dias"].apply(format_currency)
        summary_df["Cota plena"] = summary_df["valor_cota_plena"].apply(format_currency)
        summary_df = summary_df[["tipo_gasto_padrao", "subtipo_gasto", "90 dias", "Cota plena"]]
        summary_df.columns = ["Classificação", "Subtipo", "90 dias", "Cota plena"]
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        UIComponents._render_grouped_details(
            details_df=forecast.standardized_data,
            title="Detalhamento por classificação",
            difference_mode=False,
            expander_prefix=forecast.forecast_id,
        )

    @staticmethod
    def render_comparison_panel(comparison: ComparisonResult, compared_label: str) -> None:
        st.markdown(
            f"""
            <div class="section-card comparison-card">
                <div class="card-header-row">
                    <div>
                        <div class="card-title">Diferença entre Previsões</div>
                        <div class="card-meta">Base: Previsão 1 | Comparada: {compared_label}</div>
                    </div>
                    <div class="summary-kpi">{len(comparison.summary)} classificações</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        raw_df = comparison.summary[["tipo_gasto_padrao", "subtipo_gasto", "dif_90_dias", "dif_cota_plena"]].copy()
        raw_df.columns = ["Classificação", "Subtipo", "90 dias", "Cota plena"]
        styled = raw_df.style.format({"90 dias": format_currency, "Cota plena": format_currency}).applymap(
            lambda value: "color: #0f766e; font-weight: 600" if isinstance(value, (int, float)) and value < 0 else (
                "color: #b42318; font-weight: 600" if isinstance(value, (int, float)) and value > 0 else "color: #475569"
            ),
            subset=["90 dias", "Cota plena"],
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)

        UIComponents._render_grouped_details(
            details_df=comparison.detail,
            title="Detalhamento da diferença",
            difference_mode=True,
            expander_prefix="comparison",
        )

    @staticmethod
    def render_alerts(messages: list[str], title: str = "Avisos") -> None:
        if not messages:
            return
        with st.expander(title, expanded=False):
            for message in messages:
                st.warning(message)

    @staticmethod
    def render_unclassified_section(forecasts: list[ForecastData]) -> None:
        frames = []
        for forecast in forecasts:
            if not forecast.unclassified_data.empty:
                frames.append(
                    forecast.unclassified_data[[
                        "previsao_label",
                        "descricao_original",
                        "administradora",
                        "empreendimento",
                        "valor_90_dias",
                        "valor_cota_plena",
                    ]]
                )
        if not frames:
            return

        data = pd.concat(frames, ignore_index=True)
        data["valor_90_dias"] = data["valor_90_dias"].apply(format_currency)
        data["valor_cota_plena"] = data["valor_cota_plena"].apply(format_currency)
        data.columns = ["Previsão", "Descrição original", "Administradora", "Empreendimento", "90 dias", "Cota plena"]
        with st.expander("Itens não classificados", expanded=False):
            st.dataframe(data, use_container_width=True, hide_index=True)

    @staticmethod
    def _render_grouped_details(details_df: pd.DataFrame, title: str, difference_mode: bool, expander_prefix: str) -> None:
        if details_df.empty:
            return
        st.markdown(f"#### {title}")
        grouped = details_df.groupby(["tipo_gasto_padrao", "subtipo_gasto"], dropna=False)
        for (tipo, subtipo), group in grouped:
            with st.expander(f"{tipo} • {subtipo}", expanded=False):
                display = group.copy()
                if difference_mode:
                    cols = [
                        "descricao_original",
                        "base_90_dias",
                        "comparada_90_dias",
                        "dif_90_dias",
                        "base_cota_plena",
                        "comparada_cota_plena",
                        "dif_cota_plena",
                    ]
                    display = display[cols]
                    rename_map = {
                        "descricao_original": "Descrição original",
                        "base_90_dias": "Base 90 dias",
                        "comparada_90_dias": "Comparada 90 dias",
                        "dif_90_dias": "Dif. 90 dias",
                        "base_cota_plena": "Base cota plena",
                        "comparada_cota_plena": "Comparada cota plena",
                        "dif_cota_plena": "Dif. cota plena",
                    }
                else:
                    cols = ["descricao_original", "administradora", "empreendimento", "valor_90_dias", "valor_cota_plena"]
                    display = display[cols]
                    rename_map = {
                        "descricao_original": "Descrição original",
                        "administradora": "Administradora",
                        "empreendimento": "Empreendimento",
                        "valor_90_dias": "90 dias",
                        "valor_cota_plena": "Cota plena",
                    }
                display = display.rename(columns=rename_map)
                numeric_like_cols = [col for col in display.columns if any(token in col.lower() for token in ["90 dias", "cota", "dif.", "base", "comparada"])]
                if difference_mode:
                    styler = display.style.format({col: format_currency for col in numeric_like_cols}).applymap(
                        lambda value: "color: #0f766e; font-weight: 600" if isinstance(value, (int, float)) and value < 0 else (
                            "color: #b42318; font-weight: 600" if isinstance(value, (int, float)) and value > 0 else "color: #475569"
                        ),
                        subset=[col for col in numeric_like_cols if "Dif." in col],
                    )
                    st.dataframe(styler, use_container_width=True, hide_index=True)
                else:
                    for column in numeric_like_cols:
                        display[column] = display[column].apply(format_currency)
                    st.dataframe(display, use_container_width=True, hide_index=True)
