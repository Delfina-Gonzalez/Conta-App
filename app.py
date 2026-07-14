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
        "Simulador de contabilidad de partida doble para uso educativo.",
    )

    col_intro, col_estado = st.columns([3, 2], gap="large")

    with col_intro:
        st.markdown("## Bienvenida")
        st.markdown(
            """
            <div class="card card-accent">
            <p>Esta herramienta permite simular el ciclo contable de una organización:
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

        st.markdown("## ¿Cómo usar esta app?")
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

        with st.expander("Recurso económico"):
            st.markdown(
                """
**Recurso económico:** Son elementos cuantificables, libres de utilización, que permiten cumplir con metas (objetivos propuestos según la actividad del ente). 
Generan beneficios económicos futuros y pueden ser propiedad de la entidad o estar bajo su control, aunque no sean de su propiedad.
- Propios: son los activos que pertenecen a la entidad y están bajo su control.
- De terceros: El ente los utiliza libremente, pero no puede disponer de ellos. La cuantificación se hará según el valor del servicio que le prestan.

                """
            )

        with st.expander("Beneficio económico"):
            st.markdown(
                """
**Beneficio económico:** Cuando un recurso tiene valor de uso o de cambio para el ente.
                """
            )

        with st.expander("Fuentes de recursos"):
            st.markdown(
                """
**Fuentes de recursos:** 
Son los orígenes de los recursos económicos que posee la entidad. Pueden ser:
- **Permanentes:** aportes de los propietarios, que no se espera recuperar (capital social, reservas, reinversiones). Sin fecha de devolución.
- **Transitorios:** préstamos de terceros y contraprestaciones (servicios adeudados), que se espera devolver en un plazo determinado. Deben tener una fecha cierta de devolución.
                """
            )

        with st.expander("Activo, Pasivo y Patrimonio Neto"):
            st.markdown(
                """
**Activo:** recursos económicos (bienes y derechos) transferidos al ente en propiedad por sus propietarios o terceros. Son controlados por la entidad, y de los cuales se espera obtener beneficios económicos futuros.
Condiciones para "ser un activo":
    - Debe tener utilidad para en ente.
    - Tiene la capacidad de generar beneficios económicos futuros.
    - Tiene que tener derecho sobre el bien y ser controlado por la entidad.
    - Debe haber surgido a raíz de un hecho económico pasado.
    - Debe poder medirse en términos monetarios: un importe sobre bases objetivas y verificables.
    - Debe poder transferirse a terceros, ya sea en propiedad o en usufructo.
    - Debe poder convertirse en efectivo o equivalentes de efectivo, o bien, consumirse en el proceso productivo.
    - Tiene que poder distribuirse entre los propietarios.

    ACTIVO = PASIVO: Fuente de terceros (patrimonio de terceros) + PATRIMONIO NETO: Fuente de propietarios (patrimonio de los propietarios)

**Pasivo:** obligaciones de la entidad para entregar activos o prestar servicios a terceros surgidas a raíz de eventos pasados, cuyo cumplimiento se espera que resulte en una salida de recursos.
Condiciones para "ser un pasivo":
    - Debe representar una obligación presente de la entidad, ya sea de entrega de activos o prestación de servicios a terceros con plazo cierto.
    - Debe surgir a raíz de un hecho económico pasado.
    - Debe poder medirse en términos monetarios: un importe sobre bases objetivas y verificables.
    - Es una obligación ineludible a fecha cierta o ante el requerimiento de los acreedores.
    - La posibilidad de que la entidad cumpla con la obligación no depende de su voluntad, sino de la de terceros.
**Patrimonio Neto:** obligaciones de la entidad con sus propietarios, representando la diferencia entre activos y pasivos.
    - Patrimonio Jurídico: capital social, reservas, reinversiones, aportes de socios.
    - Patrimonio Financiero: considera que todos los activos son inversiones de fondos que necesariamente son producidos internamente o externamente.
    - Patrimonio Contable: diferencia entre activos y pasivos, que puede ser positivo (ganancia) o negativo (pérdida).

    PN = Activo − Pasivo

Variaciones del Patrimonio Neto:
    - CuanTitativas (modificativos): hay un cambio en el valor del patrimonio, ya sea positivo (ganancia) o negativo (pérdida). Ejemplo:
    Se vende mercadería por $1000, que costó $600. El patrimonio aumenta en $400 (ganancia).
    Las variaciones cuantitativas se producen por los propietarios (retiros, aportes) o por terceros (resultados).

    - CuaLitativas (permutativos): hay un cambio en la composición del patrimonio. Ejemplo:
    Se paga a un proveedor con dinero de la caja (disminuye el activo caja y disminuye el pasivo proveedores, pero no cambia el patrimonio neto).
    Las variaciones cualitativas se dan por cambios de activos x activos, pasivos x pasivos y aumentos/disminuciones de activos con un equivalente en otro pasivo.
    No generan resultados, ya sea que son producto de los propietarios o de terceros.

Elementos del Patrimonio Neto:
    - Capital social: aportes de los propietarios.
    - Reservas: utilidades retenidas de ejercicios anteriores. Pueden ser legales (obligatorias por ley), estatutarias (obligatorias por estatutos) o voluntarias (decisión de los propietarios).
    - Resultados: no asignados del ejercicio y acumulados.

                 """
            )
        
        with st.expander("Resultado del ejercicio"):
            st.markdown(
                """
**Resultado del ejercicio:** es la variación cuantitativa del patrimonio durante un período (que no represente aportes o retiros de los propietarios). Representa la ganancia o pérdida acumulada durante ese período.
    RESULTADO = PATRIMONIO FINAL − PATRIMONIO INICIAL − APORTES + Retiros

Fuentes de varación de resultados:
- Hechos transaccionales: operaciones que generan ingresos y gastos, que afectan el patrimonio de la entidad (ej. venta de mercadería).
- Hechos internos: producción de bienes o servicios, como la cosecha de un cultivo, que genera ingresos y gastos sin que haya una transacción con terceros.
- Hechos externos: cambios en las cotizaciones de mercado, inflación, devaluación, etc., que afectan el valor de los activos y pasivos de la entidad.
                
                """
            )

        with st.expander("Unidad de medida: moneda"):
            st.markdown(
                """
**Unidad de medida:** la moneda es la unidad de medida utilizada para expresar los valores en los estados financieros. Es la base para la medición y presentación de la información contable.
            - Moneda Nominal: no considera la inflación, se expresa en términos de la moneda corriente.
            - Moneda Homogénea: considera la inflación, se expresa por ajuste de poder adquisitivo, para reflejar el valor real de los activos y pasivos.
             
Inflación: aumento generalizado y sostenido de los precios de bienes y servicios en un país durante un período de tiempo. La inflación reduce el poder adquisitivo de la moneda, afectando la capacidad de compra de los consumidores y la rentabilidad de las empresas.
        COEFICIENTE DE INFLACIÓN = Índice al cierre del ejercicio / Índice al inicio del ejercicio.
                      """ 
            )

        with st.expander("Criterios de medición de valor monetario"):
            st.markdown(
                """
**Criterios de medición de valor monetario:**
    - **Valor de costo histórico:** se mide al costo original de adquisición o producción.
    - **Valor corriente:** se mide al valor actualizado por la inflación. Puede ser "de entrada" (costo de reposición o refabricación) o "de salida" (valor de venta menos gastos de venta).
    - **Valor actual:** es el valor hoy de un importe a pagar o a cobrar en el futuro (aplica a créditos y deudas).

Valor límite: el valor de un activo no puede ser mayor que el valor de mercado, ni menor que el valor de reposición. El valor de un pasivo no puede ser mayor que el valor de mercado, ni menor que el valor de liquidación.
Nunca debe registrarse un activo por encima de su valor de mercado, ni un pasivo por debajo de su valor de liquidación.

    - En un modelo de "valor de costo histórico", el valor de mercado sería el valor de reposición o refabricación. En caso de bienes de fácil comercialización el mismo será el costo de reposición. En caso de bienes de difícil comercialización, el mismo será el VNR (precio de venta - gastos de venta).
    - En un modelo de "valor corriente", el valor de mercado sería el el mayor valor entre el VNR (precio de venta - gastos de venta) y el VUE (valor de uso del bien, es el valor actual de ingresos generados).  """
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

        with st.expander("Principios de la partida doble"):
            st.markdown(
                """
**La partida doble** (Luca Pacioli, 1494) es el fundamento de la contabilidad moderna:
- Todo hecho económico afecta al menos **dos cuentas**.
- El total del **Debe siempre debe igual al Haber** en cada asiento.
- La ecuación contable: **Activo = Pasivo + Patrimonio Neto** se mantiene en equilibrio permanente.
                """
            )

        with st.expander("Estados financieros básicos"):
            st.markdown(
                """
**Balance General (ESP):** fotografía del patrimonio en un momento dado.
Activo = Pasivo + Patrimonio Neto.

**Estado de Resultados (PyG):** muestra si la empresa ganó o perdió en el período.
Resultado = PN inicial - PN final - Aportes + Retiros.

**Estado de Evolución del PN:** explica los cambios en el patrimonio entre dos períodos.

**Estado de Flujo de Efectivo:** muestra entradas y salidas de dinero por actividades
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
