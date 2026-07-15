"""Estados Financieros — all four financial statements."""

import io
import streamlit as st
from utils.contabilidad import (
    get_balance_general, get_estado_resultados,
    get_estado_evolucion_patrimonio, get_flujo_efectivo,
    export_estados_excel,
)
from utils.styles import apply_style, page_header, fmt_money, divider


def _money_row(label: str, value: float, indent: bool = False, bold: bool = False,
               color: str = None) -> str:
    style_label = "padding-left:1.5rem" if indent else ""
    style_val = f"color:{color}" if color else ""
    weight = "font-weight:700" if bold else ""
    val_str = fmt_money(value)
    return (
        f"<tr>"
        f"<td style='{style_label};{weight}'>{label}</td>"
        f"<td class='num' style='{style_val};{weight}'>{val_str}</td>"
        f"</tr>"
    )


def _section(label: str) -> str:
    return (
        f"<tr class='section-header'>"
        f"<td colspan='2'>{label}</td>"
        f"</tr>"
    )


def _subtotal(label: str, value: float) -> str:
    return (
        f"<tr class='subtotal-row'>"
        f"<td>{label}</td>"
        f"<td class='num'>{fmt_money(value)}</td>"
        f"</tr>"
    )


def _total(label: str, value: float) -> str:
    return (
        f"<tr class='total-row'>"
        f"<td>{label}</td>"
        f"<td class='num'>{fmt_money(value)}</td>"
        f"</tr>"
    )


def _grand_total(label: str, value: float, color: str = None) -> str:
    c = f"color:{color}" if color else ""
    return (
        f"<tr class='grand-total'>"
        f"<td>{label}</td>"
        f"<td class='num' style='{c}'>{fmt_money(value)}</td>"
        f"</tr>"
    )


def _cuenta_label(r: dict) -> str:
    """Format 'código — nombre', or just the name for computed lines without código."""
    return f"{r['codigo']} — {r['nombre']}" if r.get("codigo") else r["nombre"]


def render():
    apply_style()
    page_header(
        "Estados Financieros",
        "Generados automáticamente a partir de los asientos registrados.",
    )

    # ── Download button ──────────────────────────────────────────────────────
    buffer = io.BytesIO()
    try:
        export_estados_excel(buffer)
        buffer.seek(0)
        st.download_button(
            "Descargar todos los estados en Excel",
            data=buffer,
            file_name="estados_financieros.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        st.warning(f"No se pudo generar el Excel: {e}")

    divider()

    tabs = st.tabs([
        "Estado de Situación Patrimonial",
        "Estado de Resultados",
        "Estado de Evolución Patrimonial",
        "Estado de Flujo de Efectivo",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — BALANCE GENERAL
    # ════════════════════════════════════════
    with tabs[0]:
        st.markdown("## Estado de Situación Patrimonial")
        bg = get_balance_general()

        if not any([bg["activo_corriente"], bg["activo_no_corriente"],
                    bg["pasivo_corriente"], bg["pasivo_no_corriente"],
                    bg["patrimonio"]]):
            st.info("Sin movimientos registrados aún.")
        else:
            col_a, col_p = st.columns(2, gap="large")

            # ACTIVO side
            with col_a:
                st.markdown(
                    '<h3 style="color:#60A5FA;font-size:0.9rem;letter-spacing:0.08em;'
                    'text-transform:uppercase">ACTIVO</h3>',
                    unsafe_allow_html=True,
                )
                rows = ""
                rows += _section("Activo Corriente")
                for r in bg["activo_corriente"]:
                    rows += _money_row(f"{r['codigo']} — {r['nombre']}", r["saldo"], indent=True)
                total_ac = sum(r["saldo"] for r in bg["activo_corriente"])
                rows += _subtotal("Total Activo Corriente", total_ac)

                rows += _section("Activo No Corriente")
                for r in bg["activo_no_corriente"]:
                    rows += _money_row(f"{r['codigo']} — {r['nombre']}", r["saldo"], indent=True)
                total_anc = sum(r["saldo"] for r in bg["activo_no_corriente"])
                rows += _subtotal("Total Activo No Corriente", total_anc)

                rows += _grand_total("TOTAL ACTIVO", bg["total_activo"], color="#60A5FA")

                st.markdown(
                    f'<div class="card" style="padding:0;overflow:hidden">'
                    f'<table class="stmt-table">'
                    f'<thead><tr><th>Cuenta</th><th class="num">Monto</th></tr></thead>'
                    f'<tbody>{rows}</tbody></table></div>',
                    unsafe_allow_html=True,
                )

            # PASIVO + PN side
            with col_p:
                st.markdown(
                    '<h3 style="color:#F87171;font-size:0.9rem;letter-spacing:0.08em;'
                    'text-transform:uppercase">PASIVO + PATRIMONIO NETO</h3>',
                    unsafe_allow_html=True,
                )
                rows = ""
                rows += _section("Pasivo Corriente")
                for r in bg["pasivo_corriente"]:
                    rows += _money_row(f"{r['codigo']} — {r['nombre']}", r["saldo"], indent=True)
                total_pc = sum(r["saldo"] for r in bg["pasivo_corriente"])
                rows += _subtotal("Total Pasivo Corriente", total_pc)

                rows += _section("Pasivo No Corriente")
                for r in bg["pasivo_no_corriente"]:
                    rows += _money_row(f"{r['codigo']} — {r['nombre']}", r["saldo"], indent=True)
                total_pnc = sum(r["saldo"] for r in bg["pasivo_no_corriente"])
                rows += _subtotal("Total Pasivo No Corriente", total_pnc)

                rows += _total("TOTAL PASIVO", bg["total_pasivo"])

                rows += _section("Patrimonio Neto")
                for r in bg["patrimonio"]:
                    color = None
                    if not r.get("codigo"):
                        color = "#34D399" if r["saldo"] >= 0 else "#F87171"
                    rows += _money_row(_cuenta_label(r), r["saldo"], indent=True, color=color)
                rows += _subtotal("Total Patrimonio Neto", bg["total_patrimonio"])

               
                rows += _grand_total(
                    "TOTAL PASIVO + PN",
                    bg["total_pasivo_patrimonio"],
                    color="#34D399",
                )

                # Check balance
                diff = abs(bg["total_activo"] - bg["total_pasivo_patrimonio"])
                balance_label = (
                    '<div style="font-size:0.78rem;color:#34D399;padding:0.5rem 1.25rem">● Ecuación balanceada</div>'
                    if diff < 0.01 else
                    f'<div style="font-size:0.78rem;color:#F87171;padding:0.5rem 1.25rem">'
                    f'⚠ Diferencia: {fmt_money(diff)}</div>'
                )

                st.markdown(
                    f'<div class="card" style="padding:0;overflow:hidden">'
                    f'<table class="stmt-table">'
                    f'<thead><tr><th>Cuenta</th><th class="num">Monto</th></tr></thead>'
                    f'<tbody>{rows}</tbody></table>'
                    f'{balance_label}</div>',
                    unsafe_allow_html=True,
                )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — ESTADO DE RESULTADOS
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[1]:
        st.markdown("## Estado de Resultados")
        st.markdown(
            '<p style="color:#8892B0;font-size:0.82rem">Presentación por función, según el esquema '
            'clásico: Resultado Bruto → Resultado Operativo → Resultado antes de Impuestos → Resultado Neto.</p>',
            unsafe_allow_html=True,
        )
        er = get_estado_resultados()

        if not er["ingresos_venta"] and not er["costos_venta"] and not er["gastos_operativos"] \
                and not er["otros_ingresos"] and not er["ingresos_financieros"] and not er["egresos_financieros"]:
            st.info("Sin ingresos o egresos registrados.")
        else:
            rows = ""

            rows += _section("Ingresos por Ventas")
            for r in er["ingresos_venta"]:
                rows += _money_row(_cuenta_label(r), r["saldo"], indent=True)
            if not er["ingresos_venta"]:
                rows += "<tr><td colspan='2' style='color:#8892B0;padding-left:1.5rem'>Sin ventas registradas</td></tr>"
            rows += _subtotal("Total Ingresos por Ventas", er["total_ingresos_venta"])

            rows += _section("(-) Costo de Ventas")
            for r in er["costos_venta"]:
                rows += _money_row(_cuenta_label(r), -r["saldo"], indent=True)
            if not er["costos_venta"]:
                rows += "<tr><td colspan='2' style='color:#8892B0;padding-left:1.5rem'>Sin costo de ventas registrado</td></tr>"
            rows += _subtotal("Total Costo de Ventas", -er["total_costo_venta"])

            rows += _total(
                "RESULTADO BRUTO", er["resultado_bruto"]
            )

            if er["otros_ingresos"]:
                rows += _section("(+) Otros Ingresos Operativos")
                for r in er["otros_ingresos"]:
                    rows += _money_row(_cuenta_label(r), r["saldo"], indent=True)
                rows += _subtotal("Total Otros Ingresos", er["total_otros_ingresos"])

            rows += _section("(-) Gastos Operativos")
            for r in er["gastos_operativos"]:
                rows += _money_row(_cuenta_label(r), -r["saldo"], indent=True)
            if not er["gastos_operativos"]:
                rows += "<tr><td colspan='2' style='color:#8892B0;padding-left:1.5rem'>Sin gastos operativos registrados</td></tr>"
            rows += _subtotal("Total Gastos Operativos", -er["total_gastos_operativos"])

            rows += _total("RESULTADO OPERATIVO", er["resultado_operativo"])

            if er["ingresos_financieros"] or er["egresos_financieros"]:
                rows += _section("Resultados Financieros")
                for r in er["ingresos_financieros"]:
                    rows += _money_row(_cuenta_label(r), r["saldo"], indent=True)
                for r in er["egresos_financieros"]:
                    rows += _money_row(_cuenta_label(r), -r["saldo"], indent=True)
                rows += _subtotal("Resultado Financiero Neto", er["resultado_financiero"])

            rows += _total("RESULTADO ANTES DE IMPUESTOS", er["resultado_antes_impuestos"])

            if er["impuesto_ganancias"]:
                rows += _section("(-) Impuesto a las Ganancias")
                for r in er["impuesto_ganancias"]:
                    rows += _money_row(_cuenta_label(r), -r["saldo"], indent=True)
                rows += _subtotal("Total Impuesto a las Ganancias", -er["total_impuesto_ganancias"])

            resultado = er["resultado_neto"]
            color_res = "#34D399" if resultado >= 0 else "#F87171"
            label_res = "RESULTADO NETO DEL EJERCICIO (GANANCIA)" if resultado >= 0 else "RESULTADO NETO DEL EJERCICIO (PÉRDIDA)"
            rows += _grand_total(label_res, resultado, color=color_res)

            col_er, _ = st.columns([2, 1])
            with col_er:
                st.markdown(
                    f'<div class="card" style="padding:0;overflow:hidden">'
                    f'<table class="stmt-table">'
                    f'<thead><tr><th>Concepto</th><th class="num">Importe</th></tr></thead>'
                    f'<tbody>{rows}</tbody></table></div>',
                    unsafe_allow_html=True,
                )

            st.markdown(
                """
                <div class="hint-box" style="margin-top:1rem">
                <strong>Clasificación utilizada:</strong> las cuentas se agrupan automáticamente por su
                función: ventas y costo de ventas → Resultado Bruto; sueldos, alquileres, servicios,
                amortizaciones y otros gastos de administración/comercialización → Resultado Operativo;
                intereses y diferencias de cambio → Resultado Financiero; Impuesto a las Ganancias se
                deduce al final. Las cuentas nuevas que agregues se clasifican por palabras clave en su nombre.
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — EVOLUCIÓN PATRIMONIAL
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[2]:
        st.markdown("## Estado de Evolución del Patrimonio Neto")
        ep = get_estado_evolucion_patrimonio()

        hay_datos = ep["capital"] or ep["reservas"] or ep["resultados_acumulados"] or ep["resultado_ejercicio"]
        if not hay_datos:
            st.info("Sin cuentas de patrimonio con movimientos.")
        else:
            rows = ""

            rows += _section("Capital")
            for r in ep["capital"]:
                rows += _money_row(_cuenta_label(r), r["saldo"], indent=True)
            if not ep["capital"]:
                rows += "<tr><td colspan='2' style='color:#8892B0;padding-left:1.5rem'>Sin aportes de capital registrados</td></tr>"
            rows += _subtotal("Total Capital", ep["total_capital"])

            rows += _section("Reservas")
            for r in ep["reservas"]:
                rows += _money_row(_cuenta_label(r), r["saldo"], indent=True)
            if not ep["reservas"]:
                rows += "<tr><td colspan='2' style='color:#8892B0;padding-left:1.5rem'>Sin reservas constituidas</td></tr>"
            rows += _subtotal("Total Reservas", ep["total_reservas"])

            rows += _section("Resultados Acumulados")
            for r in ep["resultados_acumulados"]:
                rows += _money_row(_cuenta_label(r), r["saldo"], indent=True)
            if not ep["resultados_acumulados"]:
                rows += "<tr><td colspan='2' style='color:#8892B0;padding-left:1.5rem'>Sin resultados de ejercicios anteriores</td></tr>"
            rows += _subtotal("Total Resultados Acumulados", ep["total_resultados_acumulados"])

            rows += _section("Resultado del Ejercicio Actual")
            color_re = "#34D399" if ep["resultado_ejercicio"] >= 0 else "#F87171"
            rows += _money_row(
                "Resultado del ejercicio (según Estado de Resultados)",
                ep["resultado_ejercicio"], indent=True, color=color_re,
            )

            rows += _grand_total("PATRIMONIO NETO TOTAL", ep["total"], color="#34D399")

            col_ep, _ = st.columns([2, 1])
            with col_ep:
                st.markdown(
                    f'<div class="card" style="padding:0;overflow:hidden">'
                    f'<table class="stmt-table">'
                    f'<thead><tr><th>Componente</th><th class="num">Saldo</th></tr></thead>'
                    f'<tbody>{rows}</tbody></table></div>',
                    unsafe_allow_html=True,
                )

            # Cross-check against Balance General
            bg_check = get_balance_general()
            diff_pn = abs(bg_check["total_patrimonio"] - ep["total"])
            if diff_pn < 0.01:
                st.markdown(
                    '<div style="font-size:0.78rem;color:#34D399;margin-top:0.5rem">'
                    '● Coincide con el Patrimonio Neto del Balance General</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="font-size:0.78rem;color:#F87171;margin-top:0.5rem">'
                    f'⚠ Diferencia con el Balance General: {fmt_money(diff_pn)}</div>',
                    unsafe_allow_html=True,
                )

            st.markdown(
                """
                <div class="hint-box" style="margin-top:1rem">
                <strong>Nota metodológica:</strong> el Resultado del Ejercicio se incorpora aquí como
                componente del patrimonio para que el total coincida exactamente con el Estado de Situación
                Patrimonial. Como el sistema no maneja períodos contables separados (apertura/cierre), se
                muestran los saldos acumulados de cada componente en lugar de un cuadro de movimientos
                columna por columna.
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 — FLUJO DE EFECTIVO
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[3]:
        st.markdown("## Estado de Flujo de Efectivo")
        st.markdown(
            '<p style="color:#8892B0;font-size:0.82rem">Método indirecto: parte del Resultado Neto '
            'y lo concilia con el efectivo generado o utilizado.</p>',
            unsafe_allow_html=True,
        )
        fe = get_flujo_efectivo()

        rows = ""

        rows += _section("Actividades Operativas")
        color_rn = "#34D399" if fe["resultado_neto"] >= 0 else "#F87171"
        rows += _money_row("Resultado neto del ejercicio", fe["resultado_neto"], indent=True, color=color_rn)

        if fe["ajustes"]:
            rows += "<tr><td colspan='2' style='padding-left:1.5rem;padding-top:8px;color:#8892B0;font-size:0.78rem'>Ajustes por partidas sin movimiento de efectivo:</td></tr>"
            for r in fe["ajustes"]:
                rows += _money_row(r["cuenta"], r["monto"], indent=True)

        if fe["capital_trabajo"]:
            rows += "<tr><td colspan='2' style='padding-left:1.5rem;padding-top:8px;color:#8892B0;font-size:0.78rem'>Cambios en el capital de trabajo:</td></tr>"
            for r in fe["capital_trabajo"]:
                rows += _money_row(r["cuenta"], r["monto"], indent=True)

        rows += _subtotal("Flujo Neto de Actividades Operativas", fe["total_op"])

        rows += _section("Actividades de Inversión")
        for r in fe["inversion"]:
            rows += _money_row(r["cuenta"], r["monto"], indent=True)
        if not fe["inversion"]:
            rows += "<tr><td colspan='2' style='color:#8892B0;padding-left:1.5rem'>Sin movimientos de inversión</td></tr>"
        rows += _subtotal("Flujo Neto de Inversión", fe["total_inv"])

        rows += _section("Actividades de Financiación")
        for r in fe["financiacion"]:
            rows += _money_row(r["cuenta"], r["monto"], indent=True)
        if not fe["financiacion"]:
            rows += "<tr><td colspan='2' style='color:#8892B0;padding-left:1.5rem'>Sin movimientos de financiación</td></tr>"
        rows += _subtotal("Flujo Neto de Financiación", fe["total_fin"])

        var = fe["variacion_efectivo"]
        rows += _total(
            "AUMENTO (DISMINUCIÓN) NETO DE EFECTIVO",
            var,
        )
        rows += _money_row("Efectivo al inicio del período", fe["efectivo_inicial"], indent=False)
        rows += _grand_total(
            "EFECTIVO AL FINAL DEL PERÍODO",
            fe["efectivo_inicial"] + var,
            color="#34D399" if (fe["efectivo_inicial"] + var) >= 0 else "#F87171",
        )

        col_fe, _ = st.columns([2, 1])
        with col_fe:
            st.markdown(
                f'<div class="card" style="padding:0;overflow:hidden">'
                f'<table class="stmt-table">'
                f'<thead><tr><th>Concepto</th><th class="num">Importe</th></tr></thead>'
                f'<tbody>{rows}</tbody></table></div>',
                unsafe_allow_html=True,
            )

            diff = fe["diferencia_conciliacion"]
            if abs(diff) < 0.01:
                st.markdown(
                    '<div style="font-size:0.78rem;color:#34D399;margin-top:0.5rem">'
                    '● El efectivo calculado coincide con el saldo real de Caja/Banco en el Libro Mayor</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="font-size:0.78rem;color:#F87171;margin-top:0.5rem">'
                    f'⚠ Diferencia de conciliación con Caja/Banco: {fmt_money(diff)}</div>',
                    unsafe_allow_html=True,
                )

        st.markdown(
            """
            <div class="hint-box" style="margin-top:1rem">
            <strong>Clasificación utilizada (método indirecto):</strong>
            se parte del Resultado Neto y se suman las partidas que lo afectaron sin mover efectivo
            (amortizaciones, previsiones). Los cambios en cuentas de activo y pasivo corriente
            (excepto Caja/Banco) se tratan como variaciones del capital de trabajo dentro de Actividades
            Operativas. Los activos no corrientes "reales" (bienes de uso, inversiones) van a Inversión.
            Los préstamos a largo plazo y los aportes de capital van a Financiación. Como el sistema
            arranca desde cero (sin saldo de apertura de un período anterior), el saldo de cada cuenta
            equivale a su variación total.
            </div>
            """,
            unsafe_allow_html=True,
        )
