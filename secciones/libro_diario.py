"""Libro Diario — journal entry page."""

import streamlit as st
import pandas as pd
from datetime import date
from utils.contabilidad import (
    get_all_cuentas, get_all_asientos, save_asiento,
    delete_asiento, update_asiento,
    TIPO_LABELS, CONTRAPARTIDAS_SUGERIDAS, SALDO_NORMAL,
)
from utils.styles import apply_style, page_header, fmt_money, badge, divider


# ── helpers ───────────────────────────────────────────────────────────────────

def _cuenta_lookup(df: pd.DataFrame) -> dict:
    """Return {cuenta_id: row_dict}, used with format_func for a searchable selectbox."""
    return {int(r["id"]): r.to_dict() for _, r in df.iterrows()}


def _fmt_cuenta(cuenta_id, lookup: dict) -> str:
    if cuenta_id is None or cuenta_id not in lookup:
        return ""
    c = lookup[cuenta_id]
    return f"{c['codigo']} — {c['nombre']}"


def _hint_contrapartida(tipo: str) -> str:
    sugerencias = CONTRAPARTIDAS_SUGERIDAS.get(tipo, [])
    if not sugerencias:
        return ""
    lines = "".join(
        f"<li><strong>{TIPO_LABELS.get(t, t)}</strong>: {razon}</li>"
        for t, razon in sugerencias
    )
    return (
        f'<div class="hint-box">'
        f"<strong>Contrapartida sugerida para {TIPO_LABELS.get(tipo, tipo)}:</strong>"
        f"<ul style='margin:0.4rem 0 0 1rem;padding:0'>{lines}</ul>"
        f"<p style='margin-top:0.5rem;font-size:0.78rem;color:#6C7BFF'>"
        f"Saldo normal: <strong>{SALDO_NORMAL.get(tipo, '?')}</strong> — "
        f"esta cuenta aumenta por el {'Debe' if SALDO_NORMAL.get(tipo) == 'deudor' else 'Haber'}."
        f"</p></div>"
    )


# ── RENDER ────────────────────────────────────────────────────────────────────

def render():
    apply_style()
    page_header(
        "Libro Diario",
        "Registro cronológico de asientos contables. Debe = Haber para cada asiento.",
    )

    # ── Feedback persistente tras guardar/editar/eliminar un asiento ──────────
    # st.toast() llamado justo antes de st.rerun() puede perderse en el rerun,
    # así que guardamos el mensaje en session_state y lo mostramos acá arriba,
    # de forma visible, apenas se recarga la página.
    if st.session_state.get("asiento_feedback"):
        kind, msg = st.session_state.pop("asiento_feedback")
        if kind == "success":
            st.success(msg)
        else:
            st.error(msg)

    cuentas_df = get_all_cuentas()
    if cuentas_df.empty:
        st.warning("No hay cuentas disponibles. Cargá el plan de cuentas primero.")
        return

    opts = _cuenta_lookup(cuentas_df)
    cuenta_ids = sorted(opts.keys(), key=lambda cid: opts[cid]["codigo"])

    tabs = st.tabs(["Nuevo asiento", "Asientos registrados"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — NEW ENTRY
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[0]:
        st.markdown("## Nuevo asiento")

        col_fecha, col_desc = st.columns([1, 3])
        with col_fecha:
            fecha = st.date_input("Fecha", value=date.today())
        with col_desc:
            descripcion = st.text_input(
                "Descripción del asiento",
                placeholder="Ej: Cobro de clientes en efectivo",
            )

        divider()
        st.markdown("### Líneas del asiento")
        st.markdown(
            '<p style="color:#8892B0;font-size:0.82rem">Agregá al menos una línea en el Debe y una en el Haber.</p>',
            unsafe_allow_html=True,
        )

        # Session state for lines
        if "lineas_nuevo" not in st.session_state:
            st.session_state.lineas_nuevo = [
                {"cuenta": None, "debe": 0.0, "haber": 0.0, "descripcion": ""},
                {"cuenta": None, "debe": 0.0, "haber": 0.0, "descripcion": ""},
            ]

        lineas = st.session_state.lineas_nuevo
        to_delete = []
        hint_tipo = None

        # Header row
        hdr = st.columns([3, 1.5, 1.5, 2, 0.5])
        for h, t in zip(hdr, ["Cuenta", "Debe ($)", "Haber ($)", "Detalle", ""]):
            h.markdown(
                f'<div style="font-size:0.7rem;font-weight:600;letter-spacing:0.06em;'
                f'text-transform:uppercase;color:#8892B0;padding-bottom:4px">{t}</div>',
                unsafe_allow_html=True,
            )

        for i, linea in enumerate(lineas):
            c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1.5, 2, 0.5])
            with c1:
                sel_id = st.selectbox(
                    f"cuenta_{i}",
                    cuenta_ids,
                    index=None,
                    format_func=lambda cid: _fmt_cuenta(cid, opts),
                    placeholder="Escribí código o nombre para buscar...",
                    key=f"sel_c_{i}",
                    label_visibility="collapsed",
                )
                if sel_id is not None:
                    linea["cuenta"] = opts[sel_id]
                    if hint_tipo is None:
                        hint_tipo = opts[sel_id]["tipo"]
                else:
                    linea["cuenta"] = None
            with c2:
                linea["debe"] = st.number_input(
                    f"debe_{i}", min_value=0.0, step=100.0,
                    value=float(linea["debe"]), format="%.2f",
                    key=f"debe_{i}", label_visibility="collapsed",
                )
            with c3:
                linea["haber"] = st.number_input(
                    f"haber_{i}", min_value=0.0, step=100.0,
                    value=float(linea["haber"]), format="%.2f",
                    key=f"haber_{i}", label_visibility="collapsed",
                )
            with c4:
                linea["descripcion"] = st.text_input(
                    f"ldesc_{i}", value=linea["descripcion"],
                    placeholder="Detalle (opcional)",
                    key=f"ldesc_{i}", label_visibility="collapsed",
                )
            with c5:
                if len(lineas) > 2 and st.button("✕", key=f"del_l_{i}"):
                    to_delete.append(i)

        for idx in reversed(to_delete):
            st.session_state.lineas_nuevo.pop(idx)
            st.rerun()

        # Totals
        total_debe = sum(l["debe"] for l in lineas)
        total_haber = sum(l["haber"] for l in lineas)
        diff = total_debe - total_haber
        balanced = abs(diff) < 0.01

        st.markdown(
            f"""
            <div style="display:flex;gap:2rem;padding:0.75rem 0;margin-top:0.5rem;
                        border-top:1px solid #2D3150">
              <div>
                <span style="font-size:0.7rem;color:#8892B0;text-transform:uppercase">Total Debe</span><br>
                <strong style="font-size:1.1rem">{fmt_money(total_debe)}</strong>
              </div>
              <div>
                <span style="font-size:0.7rem;color:#8892B0;text-transform:uppercase">Total Haber</span><br>
                <strong style="font-size:1.1rem">{fmt_money(total_haber)}</strong>
              </div>
              <div>
                <span style="font-size:0.7rem;color:#8892B0;text-transform:uppercase">Diferencia</span><br>
                <strong style="font-size:1.1rem;color:{'#34D399' if balanced else '#F87171'}">
                  {fmt_money(diff)} {'✓' if balanced else '⚠'}</strong>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Hint
        if hint_tipo:
            st.markdown(_hint_contrapartida(hint_tipo), unsafe_allow_html=True)

        col_add, col_save = st.columns([1, 4])
        with col_add:
            if st.button("+ Línea"):
                st.session_state.lineas_nuevo.append(
                    {"cuenta": None, "debe": 0.0, "haber": 0.0, "descripcion": ""}
                )
                st.rerun()
        with col_save:
            if st.button("Guardar asiento", type="primary"):
                if not descripcion.strip():
                    st.error("Ingresá una descripción para el asiento.")
                else:
                    lineas_data = [
                        {
                            "cuenta_id": l["cuenta"]["id"],
                            "debe": l["debe"],
                            "haber": l["haber"],
                            "descripcion": l["descripcion"],
                        }
                        for l in lineas
                        if l["cuenta"] is not None
                    ]
                    if len(lineas_data) < 2:
                        st.error("Seleccioná al menos dos cuentas.")
                    else:
                        ok, msg, _ = save_asiento(str(fecha), descripcion, lineas_data)
                        if ok:
                            st.session_state.asiento_feedback = (
                                "success", msg or "¡Asiento cargado con éxito!"
                            )
                            st.session_state.lineas_nuevo = [
                                {"cuenta": None, "debe": 0.0, "haber": 0.0, "descripcion": ""},
                                {"cuenta": None, "debe": 0.0, "haber": 0.0, "descripcion": ""},
                            ]
                            st.rerun()
                        else:
                            st.error(msg)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — VIEW / EDIT / DELETE
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[1]:
        asientos = get_all_asientos()
        if not asientos:
            st.info("No hay asientos registrados aún.")
            return

        st.markdown(
            f'<p style="color:#8892B0;font-size:0.82rem;margin-bottom:1rem">'
            f'{len(asientos)} asiento(s) registrado(s)</p>',
            unsafe_allow_html=True,
        )

        # Edit state
        if "editing_id" not in st.session_state:
            st.session_state.editing_id = None
        if "edit_lineas" not in st.session_state:
            st.session_state.edit_lineas = []

        for asiento in asientos:
            total_d = sum(l["debe"] for l in asiento["lineas"])
            total_h = sum(l["haber"] for l in asiento["lineas"])
            bal_ok = abs(total_d - total_h) < 0.01

            with st.expander(
                f"Asiento N° {asiento['numero']}  —  {asiento['fecha']}  |  {asiento['descripcion']}",
                expanded=(st.session_state.editing_id == asiento["id"]),
            ):
                if st.session_state.editing_id == asiento["id"]:
                    # ── EDIT MODE ────────────────────────────────────────────
                    st.markdown("**Editando asiento**")
                    edit_fecha = st.date_input(
                        "Fecha", value=date.fromisoformat(asiento["fecha"]),
                        key=f"ef_{asiento['id']}",
                    )
                    edit_desc = st.text_input(
                        "Descripción", value=asiento["descripcion"],
                        key=f"ed_{asiento['id']}",
                    )

                    edit_lineas = st.session_state.edit_lineas
                    e_to_del = []

                    hdr2 = st.columns([3, 1.5, 1.5, 2, 0.5])
                    for h, t in zip(hdr2, ["Cuenta", "Debe ($)", "Haber ($)", "Detalle", ""]):
                        h.markdown(
                            f'<div style="font-size:0.7rem;font-weight:600;'
                            f'color:#8892B0;text-transform:uppercase">{t}</div>',
                            unsafe_allow_html=True,
                        )

                    for j, el in enumerate(edit_lineas):
                        ec1, ec2, ec3, ec4, ec5 = st.columns([3, 1.5, 1.5, 2, 0.5])
                        with ec1:
                            cur_id = el["cuenta"]["id"] if el.get("cuenta") else None
                            sel2 = st.selectbox(
                                f"ec_{j}", cuenta_ids,
                                index=cuenta_ids.index(cur_id) if cur_id in opts else None,
                                format_func=lambda cid: _fmt_cuenta(cid, opts),
                                placeholder="Escribí código o nombre para buscar...",
                                key=f"esel_{asiento['id']}_{j}",
                                label_visibility="collapsed",
                            )
                            el["cuenta"] = opts[sel2] if sel2 is not None else None
                        with ec2:
                            el["debe"] = st.number_input(
                                f"ed_{j}", min_value=0.0, step=100.0,
                                value=float(el["debe"]), format="%.2f",
                                key=f"edebe_{asiento['id']}_{j}",
                                label_visibility="collapsed",
                            )
                        with ec3:
                            el["haber"] = st.number_input(
                                f"eh_{j}", min_value=0.0, step=100.0,
                                value=float(el["haber"]), format="%.2f",
                                key=f"ehaber_{asiento['id']}_{j}",
                                label_visibility="collapsed",
                            )
                        with ec4:
                            el["descripcion"] = st.text_input(
                                f"eldesc_{j}", value=el.get("descripcion", ""),
                                key=f"eldesc_{asiento['id']}_{j}",
                                label_visibility="collapsed",
                            )
                        with ec5:
                            if len(edit_lineas) > 2 and st.button("✕", key=f"edel_{asiento['id']}_{j}"):
                                e_to_del.append(j)

                    for idx in reversed(e_to_del):
                        st.session_state.edit_lineas.pop(idx)
                        st.rerun()

                    if st.button("+ Línea", key=f"eaddl_{asiento['id']}"):
                        st.session_state.edit_lineas.append(
                            {"cuenta": None, "codigo": None, "nombre": None,
                             "debe": 0.0, "haber": 0.0, "descripcion": ""}
                        )
                        st.rerun()

                    c_save, c_cancel = st.columns(2)
                    with c_save:
                        if st.button("Guardar cambios", key=f"esave_{asiento['id']}", type="primary"):
                            ld = [
                                {"cuenta_id": el["cuenta"]["id"], "debe": el["debe"],
                                 "haber": el["haber"], "descripcion": el.get("descripcion", "")}
                                for el in edit_lineas if el.get("cuenta")
                            ]
                            ok, msg = update_asiento(asiento["id"], str(edit_fecha), edit_desc, ld)
                            if ok:
                                st.session_state.asiento_feedback = ("success", msg)
                                st.session_state.editing_id = None
                                st.rerun()
                            else:
                                st.error(msg)
                    with c_cancel:
                        if st.button("Cancelar", key=f"ecancel_{asiento['id']}"):
                            st.session_state.editing_id = None
                            st.rerun()

                else:
                    # ── VIEW MODE ────────────────────────────────────────────
                    # Build ledger-style HTML table
                    rows_html = ""
                    for l in asiento["lineas"]:
                        debe_str = fmt_money(l["debe"]) if l["debe"] else ""
                        haber_str = fmt_money(l["haber"]) if l["haber"] else ""
                        rows_html += (
                            f"<tr>"
                            f"<td><code style='color:#A78BFA;font-size:0.78rem'>{l['codigo']}</code></td>"
                            f"<td>{l['nombre']}</td>"
                            f"<td style='color:#8892B0;font-size:0.8rem'>{l.get('descripcion','')}</td>"
                            f"<td class='num' style='color:#60A5FA'>{debe_str}</td>"
                            f"<td class='num' style='color:#34D399'>{haber_str}</td>"
                            f"</tr>"
                        )

                    status_color = "#34D399" if bal_ok else "#F87171"
                    status_label = "Balanceado" if bal_ok else "Desbalanceado"

                    st.markdown(
                        f"""
                        <table class="ledger-table" style="margin-bottom:0.75rem">
                          <thead>
                            <tr>
                              <th>Código</th><th>Cuenta</th><th>Detalle</th>
                              <th class="num">Debe</th><th class="num">Haber</th>
                            </tr>
                          </thead>
                          <tbody>
                            {rows_html}
                          </tbody>
                          <tfoot>
                            <tr class="total-row">
                              <td colspan="3">Totales</td>
                              <td class="num">{fmt_money(total_d)}</td>
                              <td class="num">{fmt_money(total_h)}</td>
                            </tr>
                          </tfoot>
                        </table>
                        <div style="font-size:0.78rem;color:{status_color};margin-bottom:0.5rem">
                          ● {status_label}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    col_e, col_d = st.columns([1, 5])
                    with col_e:
                        if st.button("Editar", key=f"edit_{asiento['id']}"):
                            st.session_state.editing_id = asiento["id"]
                            st.session_state.edit_lineas = [
                                {
                                    "cuenta": {"id": l["cuenta_id"]},
                                    "codigo": l["codigo"],
                                    "nombre": l["nombre"],
                                    "debe": l["debe"],
                                    "haber": l["haber"],
                                    "descripcion": l.get("descripcion", ""),
                                }
                                for l in asiento["lineas"]
                            ]
                            st.rerun()
                    with col_d:
                        if st.button("Eliminar asiento", key=f"del_{asiento['id']}"):
                            ok, msg = delete_asiento(asiento["id"])
                            if ok:
                                st.session_state.asiento_feedback = ("success", msg)
                                st.rerun()
                            else:
                                st.error(msg)
