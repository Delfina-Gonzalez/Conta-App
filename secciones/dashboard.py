"""Dashboard — financial indicators page."""

import streamlit as st
from utils.contabilidad import get_indicadores
from utils.styles import apply_style, page_header, fmt_money, divider


def _ratio_card(title: str, value, fmt: str = ".2f", ideal: str = "",
                interpretation: str = "", color: str = None) -> str:
    if value is None:
        val_str = "—"
        c = "#8892B0"
    else:
        val_str = f"{value:{fmt}}"
        c = color or "#E8EAF6"

    return (
        f'<div class="card" style="padding:1.25rem 1.5rem">'
        f'<div style="font-size:0.7rem;font-weight:600;letter-spacing:0.08em;'
        f'text-transform:uppercase;color:#8892B0;margin-bottom:0.35rem">{title}</div>'
        f'<div style="font-size:2rem;font-weight:700;color:{c};line-height:1;'
        f'margin-bottom:0.4rem">{val_str}</div>'
        f'<div style="font-size:0.75rem;color:#6C7BFF;margin-bottom:0.3rem">{ideal}</div>'
        f'<div style="font-size:0.8rem;color:#8892B0;line-height:1.5">{interpretation}</div>'
        f'</div>'
    )


def _signal_color(value, thresholds: tuple, reverse: bool = False) -> str:
    """Return color based on value vs thresholds (low, high)."""
    if value is None:
        return "#8892B0"
    lo, hi = thresholds
    if reverse:
        if value <= lo:
            return "#34D399"
        elif value <= hi:
            return "#FBBF24"
        return "#F87171"
    else:
        if value >= hi:
            return "#34D399"
        elif value >= lo:
            return "#FBBF24"
        return "#F87171"


def render():
    apply_style()
    page_header(
        "Dashboard",
        "Indicadores financieros calculados a partir del estado actual del sistema.",
    )

    ind = get_indicadores()

    if not ind:
        st.info("No hay datos suficientes para calcular indicadores. Cargá asientos primero.")
        return

    # ── Summary KPIs ─────────────────────────────────────────────────────────
    st.markdown("## Resumen patrimonial")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Activo Total", fmt_money(ind["activo_total"]))
    with k2:
        st.metric("Pasivo Total", fmt_money(ind["pasivo_total"]))
    with k3:
        st.metric("Patrimonio Neto", fmt_money(ind["patrimonio"]))
    with k4:
        res = ind["resultado"]
        st.metric(
            "Resultado del período",
            fmt_money(res),
            delta="Ganancia" if res >= 0 else "Pérdida",
        )

    divider()

    # ── Ratios grid ───────────────────────────────────────────────────────────
    st.markdown("## Indicadores de liquidez")
    liq = ind.get("liquidez_corriente")
    lac = ind.get("liquidez_acida")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            _ratio_card(
                "Liquidez Corriente",
                liq,
                ideal="Óptimo: mayor a 1.5",
                interpretation=(
                    "Capacidad de la empresa de cubrir sus deudas de corto plazo "
                    "con sus activos corrientes. Valores entre 1.5 y 2 son saludables."
                ),
                color=_signal_color(liq, (1.0, 1.5)) if liq else None,
            ),
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            _ratio_card(
                "Liquidez Ácida",
                lac,
                ideal="Óptimo: mayor a 0.8",
                interpretation=(
                    "Igual que liquidez corriente pero excluye inventarios, "
                    "que son el activo menos líquido. Mide la liquidez inmediata."
                ),
                color=_signal_color(lac, (0.8, 1.2)) if lac else None,
            ),
            unsafe_allow_html=True,
        )

    divider()
    st.markdown("## Indicadores de solvencia y endeudamiento")
    sol = ind.get("solvencia")
    end = ind.get("endeudamiento")
    col3, col4 = st.columns(2)
    with col3:
        st.markdown(
            _ratio_card(
                "Solvencia Total",
                sol,
                ideal="Óptimo: mayor a 1",
                interpretation=(
                    "Relación entre activos y pasivos totales. Indica si la empresa "
                    "tiene suficientes activos para cubrir todas sus deudas."
                ),
                color=_signal_color(sol, (1.0, 1.5)) if sol else None,
            ),
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            _ratio_card(
                "Endeudamiento",
                end,
                ideal="Óptimo: menor a 1",
                interpretation=(
                    "Deuda total sobre patrimonio neto. Mide cuántas veces el "
                    "pasivo supera al capital propio. Menor es más saludable."
                ),
                color=_signal_color(end, (0.5, 1.0), reverse=True) if end else None,
            ),
            unsafe_allow_html=True,
        )

    divider()
    st.markdown("## Indicadores de rentabilidad")
    roa = ind.get("rentabilidad")
    mg = ind.get("margen_neto")
    col5, col6 = st.columns(2)
    with col5:
        st.markdown(
            _ratio_card(
                "ROA — Rentabilidad sobre Activos",
                roa,
                fmt=".1f",
                ideal="Óptimo: mayor a 5%",
                interpretation=(
                    "Resultado neto sobre activo total, expresado en porcentaje. "
                    "Indica qué tan eficientemente se usan los activos para generar ganancias."
                ),
                color=_signal_color(roa, (3, 8)) if roa else None,
            ),
            unsafe_allow_html=True,
        )
        if roa is not None:
            st.markdown(
                '<div style="margin-top:-0.5rem;font-size:0.75rem;color:#8892B0">%</div>',
                unsafe_allow_html=True,
            )
    with col6:
        st.markdown(
            _ratio_card(
                "Margen Neto",
                mg,
                fmt=".1f",
                ideal="Óptimo: mayor a 10%",
                interpretation=(
                    "Resultado neto sobre ingresos totales. Cuántos centavos de ganancia "
                    "quedan por cada peso de venta."
                ),
                color=_signal_color(mg, (5, 15)) if mg else None,
            ),
            unsafe_allow_html=True,
        )
        if mg is not None:
            st.markdown(
                '<div style="margin-top:-0.5rem;font-size:0.75rem;color:#8892B0">%</div>',
                unsafe_allow_html=True,
            )

    divider()

    # ── Composition bars ──────────────────────────────────────────────────────
    st.markdown("## Composición del financiamiento")
    total = ind["activo_total"]
    if total > 0:
        pct_pas = ind["pasivo_total"] / total * 100
        pct_pn = ind["patrimonio"] / total * 100

        st.markdown(
            f"""
            <div class="card" style="padding:1.25rem 1.5rem">
              <div style="font-size:0.8rem;color:#8892B0;margin-bottom:0.75rem">
                Financiamiento del Activo Total ({fmt_money(total)})
              </div>
              <div style="display:flex;border-radius:6px;overflow:hidden;height:28px;margin-bottom:0.6rem">
                <div style="width:{max(pct_pas,0):.1f}%;background:#F87171;
                     display:flex;align-items:center;justify-content:center;
                     font-size:0.72rem;font-weight:700;color:#fff">
                  {pct_pas:.1f}%
                </div>
                <div style="width:{max(pct_pn,0):.1f}%;background:#34D399;
                     display:flex;align-items:center;justify-content:center;
                     font-size:0.72rem;font-weight:700;color:#0F1117">
                  {pct_pn:.1f}%
                </div>
              </div>
              <div style="display:flex;gap:1.5rem;font-size:0.8rem">
                <div><span style="color:#F87171">■</span>
                  Pasivo: {fmt_money(ind['pasivo_total'])} ({pct_pas:.1f}%)
                </div>
                <div><span style="color:#34D399">■</span>
                  Patrimonio: {fmt_money(ind['patrimonio'])} ({pct_pn:.1f}%)
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    divider()

    # ── Color legend ─────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="hint-box">
        <strong>Semáforo de indicadores:</strong>
        <span style="color:#34D399">■ Verde</span> = óptimo &nbsp;|&nbsp;
        <span style="color:#FBBF24">■ Amarillo</span> = aceptable &nbsp;|&nbsp;
        <span style="color:#F87171">■ Rojo</span> = requiere atención &nbsp;|&nbsp;
        <span style="color:#8892B0">■ Gris</span> = sin datos suficientes
        </div>
        """,
        unsafe_allow_html=True,
    )
