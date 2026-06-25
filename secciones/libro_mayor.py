"""Libro Mayor — general ledger page."""

import streamlit as st
from utils.contabilidad import get_libro_mayor, TIPO_LABELS, SALDO_NORMAL
from utils.styles import apply_style, page_header, fmt_money, badge, divider


def render():
    apply_style()
    page_header(
        "Libro Mayor",
        "Movimientos por cuenta con saldo acumulado. Se genera automáticamente del Libro Diario.",
    )

    mayor = get_libro_mayor()
    if not mayor:
        st.info("No hay movimientos registrados. Cargá asientos en el Libro Diario primero.")
        return

    # ── Filters ────────────────────────────────────────────────────────────
    all_tipos = list({d["tipo"] for d in mayor.values()})
    tipo_filter = st.selectbox(
        "Filtrar por tipo",
        ["Todos"] + sorted(all_tipos),
        format_func=lambda x: "Todos" if x == "Todos" else TIPO_LABELS.get(x, x),
    )

    st.markdown(
        f'<p style="color:#8892B0;font-size:0.82rem;margin:0.5rem 0 1rem">'
        f'{len(mayor)} cuenta(s) con movimientos</p>',
        unsafe_allow_html=True,
    )
    divider()

    # ── Group display ───────────────────────────────────────────────────────
    tipo_orden = ["activo", "pasivo", "patrimonio", "r_positivo", "r_negativo"]

    for tipo in tipo_orden:
        cuentas_tipo = {
            cid: d for cid, d in mayor.items() if d["tipo"] == tipo
        }
        if not cuentas_tipo:
            continue
        if tipo_filter != "Todos" and tipo != tipo_filter:
            continue

        st.markdown(
            f'<div style="margin:1.5rem 0 0.75rem">{badge(tipo)}</div>',
            unsafe_allow_html=True,
        )

        for cid, data in sorted(cuentas_tipo.items(), key=lambda x: x[1]["codigo"]):
            movs = data["movimientos"]
            total_d = data["total_debe"]
            total_h = data["total_haber"]
            saldo = data["saldo"]
            tipo_saldo = data["tipo_saldo"]

            saldo_color = "#34D399" if saldo >= 0 else "#F87171"

            # Build table rows
            saldo_parcial = 0.0
            rows_html = ""
            for mov in movs:
                d = mov["debe"]
                h = mov["haber"]
                natural = SALDO_NORMAL.get(data["tipo"], "deudor")
                if natural == "deudor":
                    saldo_parcial += d - h
                else:
                    saldo_parcial += h - d

                deudor_str = f"{saldo_parcial:,.2f}" if saldo_parcial >= 0 else ""
                acreedor_str = f"{abs(saldo_parcial):,.2f}" if saldo_parcial < 0 else ""

                rows_html += (
                    f"<tr>"
                    f"<td style='color:#8892B0'>{mov['fecha']}</td>"
                    f"<td>{mov['descripcion']}</td>"
                    f"<td style='color:#8892B0;font-size:0.78rem'>Asiento N°{mov['asiento_num']}</td>"
                    f"<td class='num' style='color:#60A5FA'>{f'{d:,.2f}' if d else ''}</td>"
                    f"<td class='num' style='color:#34D399'>{f'{h:,.2f}' if h else ''}</td>"
                    f"<td class='num' style='color:#A78BFA'>{deudor_str}</td>"
                    f"<td class='num' style='color:#F87171'>{acreedor_str}</td>"
                    f"</tr>"
                )

            sub_badge = badge(data["subcategoria"]) if data.get("subcategoria") else ""

            st.markdown(
                f"""
                <div class="card" style="margin-bottom:1rem;padding:0">
                  <!-- Cuenta header -->
                  <div style="padding:0.9rem 1.25rem;border-bottom:1px solid #2D3150;
                               display:flex;justify-content:space-between;align-items:center">
                    <div>
                      <code style="color:#A78BFA;font-size:0.8rem">{data['codigo']}</code>
                      <strong style="margin-left:0.75rem;font-size:1rem">{data['nombre']}</strong>
                      <span style="margin-left:0.5rem">{sub_badge}</span>
                    </div>
                    <div style="text-align:right">
                      <span style="font-size:0.7rem;color:#8892B0;display:block">Saldo {tipo_saldo}</span>
                      <strong style="font-size:1.1rem;color:{saldo_color}">{fmt_money(abs(saldo))}</strong>
                    </div>
                  </div>
                  <!-- Movements table -->
                  <div style="overflow-x:auto">
                  <table class="ledger-table" style="margin:0">
                    <thead>
                      <tr>
                        <th>Fecha</th>
                        <th>Descripción</th>
                        <th>Ref.</th>
                        <th class="num">Debe</th>
                        <th class="num">Haber</th>
                        <th class="num">Deudor</th>
                        <th class="num">Acreedor</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows_html}
                    </tbody>
                    <tfoot>
                      <tr class="total-row">
                        <td colspan="3">Totales</td>
                        <td class="num">{total_d:,.2f}</td>
                        <td class="num">{total_h:,.2f}</td>
                        <td class="num" colspan="2"></td>
                      </tr>
                      <tr class="saldo-row">
                        <td colspan="5">Saldo {tipo_saldo}</td>
                        <td class="num" colspan="2" style="color:{saldo_color}">{abs(saldo):,.2f}</td>
                      </tr>
                    </tfoot>
                  </table>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
