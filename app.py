"""
Contabilidad Básica — Simulador Educativo
Entry point: streamlit run app.py
"""

import streamlit as st
from utils.database import init_db, reset_db
from utils.contabilidad import get_indicadores, get_all_asientos, get_all_cuentas
from utils.styles import apply_style, page_header, fmt_money, badge, divider

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ContaSim — Simulador Contable",
    page_icon="📒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Init DB ──────────────────────────────────────────────────────────────────
init_db()
apply_style()

# ─── Sidebar navigation ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 1rem 0 0.5rem">
            <span style="font-family:'DM Serif Display',serif;font-size:1.4rem;
                         color:#E8EAF6;letter-spacing:-0.02em">ContaSim</span><br>
            <span style="font-size:0.7rem;color:#8892B0;letter-spacing:0.08em;
                         text-transform:uppercase">Simulador Contable</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    page = st.radio(
        "Navegación",
        [
            "Inicio",
            "Plan de Cuentas",
            "Libro Diario",
            "Libro Mayor",
            "Estados Financieros",
            "Dashboard",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown(
        '<span style="font-size:0.7rem;color:#8892B0;">Estado del sistema</span>',
        unsafe_allow_html=True,
    )
    ind = get_indicadores()
    asientos = get_all_asientos()
    cuentas_df = get_all_cuentas()
    col1, col2 = st.columns(2)
    col1.metric("Asientos", len(asientos))
    col2.metric("Cuentas", len(cuentas_df))

    st.divider()
    with st.expander("⚠ Reiniciar sistema"):
        st.warning("Esto borrará todos los asientos y datos cargados.")
        if st.button("Confirmar reinicio", type="primary"):
            reset_db()
            st.cache_data.clear()
            st.success("Sistema reiniciado.")
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGES
# ═══════════════════════════════════════════════════════════════════════════════

if page == "Inicio":
    # ── HOME ──────────────────────────────────────────────────────────────────
    page_header(
        "ContaSim",
        "Simulador de contabilidad de partida doble para uso educativo universitario.",
    )

    col_intro, col_estado = st.columns([3, 2], gap="large")

    with col_intro:
        st.markdown("## Bienvenida")
        st.markdown(
            """
            <div class="card card-accent">
            <p>Esta herramienta permite simular el ciclo contable completo de una organización:
            desde el registro de asientos en el <strong>Libro Diario</strong> hasta la generación
            automática del <strong>Balance General</strong>, <strong>Estado de Resultados</strong>,
            <strong>Estado de Evolución del Patrimonio Neto</strong> y
            <strong>Estado de Flujo de Efectivo</strong>.</p>
            <p style="margin-top:0.75rem;color:#8892B0;font-size:0.85rem;">
            Diseñado como complemento pedagógico — no reemplaza software contable profesional.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("## Cómo usar esta app")
        steps = [
            ("1", "Plan de Cuentas", "Revisá y personalizá el catálogo de cuentas. Cada cuenta tiene su tipo y clasificación."),
            ("2", "Libro Diario", "Cargá los asientos contables. El sistema valida la partida doble (Debe = Haber)."),
            ("3", "Libro Mayor", "Visualizá los movimientos por cuenta con saldo automático."),
            ("4", "Estados Financieros", "Generá y descargá los cuatro estados contables principales."),
            ("5", "Dashboard", "Analizá indicadores de liquidez, solvencia, endeudamiento y rentabilidad."),
        ]
        for num, titulo, desc in steps:
            st.markdown(
                f"""<div class="card" style="display:flex;gap:1rem;align-items:flex-start;padding:1rem 1.25rem;margin-bottom:0.6rem">
                <div style="min-width:28px;height:28px;border-radius:50%;background:#6C7BFF22;
                     border:1px solid #6C7BFF;display:flex;align-items:center;justify-content:center;
                     font-size:0.75rem;font-weight:700;color:#6C7BFF">{num}</div>
                <div><strong style="color:#E8EAF6">{titulo}</strong><br>
                <span style="font-size:0.83rem;color:#8892B0">{desc}</span></div></div>""",
                unsafe_allow_html=True,
            )

    with col_estado:
        st.markdown("## Estado actual")
        ind = get_indicadores()
        if ind:
            st.markdown(
                f"""
                <div class="kpi-grid">
                  <div class="kpi">
                    <div class="kpi-label">Activo Total</div>
                    <div class="kpi-value" style="font-size:1.2rem">{fmt_money(ind.get('activo_total', 0))}</div>
                  </div>
                  <div class="kpi">
                    <div class="kpi-label">Pasivo Total</div>
                    <div class="kpi-value" style="font-size:1.2rem">{fmt_money(ind.get('pasivo_total', 0))}</div>
                  </div>
                  <div class="kpi">
                    <div class="kpi-label">Patrimonio Neto</div>
                    <div class="kpi-value" style="font-size:1.2rem">{fmt_money(ind.get('patrimonio', 0))}</div>
                  </div>
                  <div class="kpi">
                    <div class="kpi-label">Resultado</div>
                    <div class="kpi-value" style="font-size:1.2rem;color:{'#34D399' if ind.get('resultado',0)>=0 else '#F87171'}">{fmt_money(ind.get('resultado', 0))}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("Sin movimientos registrados aún.")

        divider()

        st.markdown("## Marco teórico")

        with st.expander("Principios de la partida doble"):
            st.markdown(
                """
**La partida doble** (Luca Pacioli, 1494) es el fundamento de la contabilidad moderna:
- Todo hecho económico afecta al menos **dos cuentas**.
- El total del **Debe siempre debe igual al Haber** en cada asiento.
- La ecuación contable: **Activo = Pasivo + Patrimonio Neto** se mantiene en equilibrio permanente.
                """
            )

        with st.expander("Tipos de cuentas"):
            st.markdown(
                """
| Tipo | Saldo normal | Aumenta con | Disminuye con |
|------|-------------|-------------|---------------|
| **Activo** | Deudor | Debe | Haber |
| **Pasivo** | Acreedor | Haber | Debe |
| **Patrimonio** | Acreedor | Haber | Debe |
| **R. Positivo** | Acreedor | Haber | Debe |
| **R. Negativo** | Deudor | Debe | Haber |

Los activos corrientes se convierten en efectivo en menos de 12 meses.
Los no corrientes, en más de 12 meses.
                """
            )

        with st.expander("Estados financieros básicos"):
            st.markdown(
                """
**Balance General (ESP):** fotografía del patrimonio en un momento dado.
Activo = Pasivo + Patrimonio Neto.

**Estado de Resultados (PyG):** muestra si la empresa ganó o perdió en el período.
Resultado = Ingresos − Egresos.

**Estado de Evolución del PN:** explica los cambios en el patrimonio entre dos fechas.

**Estado de Flujo de Efectivo:** muestra entradas y salidas reales de dinero por actividades
operativas, de inversión y de financiación.
                """
            )

        with st.expander("Indicadores financieros clave"):
            st.markdown(
                """
- **Liquidez corriente** = Activo Corriente / Pasivo Corriente (óptimo > 1)
- **Liquidez ácida** = (Activo Corriente − Inventarios) / Pasivo Corriente (óptimo > 0.8)
- **Solvencia total** = Activo Total / Pasivo Total (óptimo > 1)
- **Endeudamiento** = Pasivo Total / Patrimonio Neto (menor es mejor)
- **Rentabilidad sobre activos (ROA)** = Resultado Neto / Activo Total × 100
- **Margen neto** = Resultado Neto / Ingresos × 100
                """
            )


# ─── Other pages live in pages/ and are imported here ─────────────────────────
elif page == "Plan de Cuentas":
    from secciones.plan_cuentas import render
    render()

elif page == "Libro Diario":
    from secciones.libro_diario import render
    render()

elif page == "Libro Mayor":
    from secciones.libro_mayor import render
    render()

elif page == "Estados Financieros":
    from secciones.estados_financieros import render
    render()

elif page == "Dashboard":
    from secciones.dashboard import render
    render()
