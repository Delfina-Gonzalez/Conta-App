"""Plan de Cuentas — account management page."""

import streamlit as st
import pandas as pd
from utils.contabilidad import (
    get_all_cuentas, add_cuenta, delete_cuenta, toggle_cuenta,
    TIPO_LABELS, SUBCATEGORIA_LABELS,
)
from utils.styles import apply_style, page_header, badge, divider


def render():
    apply_style()
    page_header(
        "Plan de Cuentas",
        "Catálogo de cuentas contables. Las cuentas predeterminadas no pueden eliminarse.",
    )

    tabs = st.tabs(["Ver cuentas", "Agregar cuenta"])

    # ── TAB 1: VIEW ──────────────────────────────────────────────────────────
    with tabs[0]:
        df = get_all_cuentas()
        if df.empty:
            st.info("No hay cuentas cargadas.")
            return

        # Filters
        col1, col2, col3 = st.columns([2, 2, 3])
        with col1:
            tipo_filter = st.selectbox(
                "Filtrar por tipo",
                ["Todos"] + list(TIPO_LABELS.keys()),
                format_func=lambda x: "Todos" if x == "Todos" else TIPO_LABELS[x],
            )
        with col2:
            sub_filter = st.selectbox(
                "Clasificación",
                ["Todos", "corriente", "no_corriente", "—"],
                format_func=lambda x: "Todos" if x == "Todos" else SUBCATEGORIA_LABELS.get(
                    None if x == "—" else x, x
                ),
            )
        with col3:
            search = st.text_input("Buscar cuenta", placeholder="Código o nombre...")

        filtered = df.copy()
        if tipo_filter != "Todos":
            filtered = filtered[filtered["tipo"] == tipo_filter]
        if sub_filter == "—":
            filtered = filtered[filtered["subcategoria"].isna()]
        elif sub_filter != "Todos":
            filtered = filtered[filtered["subcategoria"] == sub_filter]
        if search:
            mask = (
                filtered["codigo"].str.contains(search, case=False, na=False) |
                filtered["nombre"].str.contains(search, case=False, na=False)
            )
            filtered = filtered[mask]

        divider()
        st.markdown(
            f'<p style="color:#8892B0;font-size:0.82rem;margin-bottom:0.75rem">'
            f'{len(filtered)} cuenta(s) encontrada(s)</p>',
            unsafe_allow_html=True,
        )

        # Group by tipo
        tipo_orden = ["activo", "pasivo", "patrimonio", "r_positivo", "r_negativo"]
        for tipo in tipo_orden:
            grupo = filtered[filtered["tipo"] == tipo]
            if grupo.empty:
                continue

            st.markdown(
                f'<div style="margin-top:1rem">{badge(tipo)} '
                f'<span style="font-size:0.8rem;color:#8892B0;margin-left:8px">'
                f'{len(grupo)} cuenta(s)</span></div>',
                unsafe_allow_html=True,
            )

            for _, row in grupo.iterrows():
                with st.container():
                    c1, c2, c3, c4, c5 = st.columns([1.2, 2.5, 1.5, 0.8, 0.8])
                    with c1:
                        st.markdown(
                            f'<code style="color:#A78BFA;font-size:0.8rem">{row["codigo"]}</code>',
                            unsafe_allow_html=True,
                        )
                    with c2:
                        st.markdown(
                            f'<span style="font-weight:500">{row["nombre"]}</span>',
                            unsafe_allow_html=True,
                        )
                    with c3:
                        sub = row.get("subcategoria")
                        if sub:
                            st.markdown(badge(sub), unsafe_allow_html=True)
                        else:
                            st.markdown(
                                '<span style="color:#8892B0;font-size:0.75rem">—</span>',
                                unsafe_allow_html=True,
                            )
                    with c4:
                        default_tag = (
                            '<span style="color:#8892B0;font-size:0.7rem">predeterminada</span>'
                            if row.get("es_default") else ""
                        )
                        st.markdown(default_tag, unsafe_allow_html=True)
                    with c5:
                        if not row.get("es_default"):
                            if st.button(
                                "Eliminar",
                                key=f"del_{row['id']}",
                                help="Eliminar esta cuenta",
                            ):
                                ok, msg = delete_cuenta(row["id"])
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

                st.markdown(
                    f'<div style="font-size:0.75rem;color:#8892B0;'
                    f'padding:2px 0 8px 1rem;border-bottom:1px solid #2D3150">'
                    f'{row.get("descripcion") or ""}</div>',
                    unsafe_allow_html=True,
                )

    # ── TAB 2: ADD ───────────────────────────────────────────────────────────
    with tabs[1]:
        st.markdown("## Nueva cuenta")

        col_a, col_b = st.columns(2)
        with col_a:
            codigo = st.text_input(
                "Código",
                placeholder="Ej: 1.1.12",
                help="Formato sugerido: tipo.subtipo.número",
            )
            nombre = st.text_input("Nombre", placeholder="Ej: Cuentas por Cobrar Comerciales")
            tipo = st.selectbox(
                "Tipo de cuenta",
                list(TIPO_LABELS.keys()),
                format_func=lambda x: TIPO_LABELS[x],
            )
        with col_b:
            subcategoria = st.selectbox(
                "Clasificación",
                [None, "corriente", "no_corriente"],
                format_func=lambda x: "Sin clasificación" if x is None else SUBCATEGORIA_LABELS[x],
                help="Solo aplica a Activos y Pasivos.",
            )
            descripcion = st.text_area(
                "Descripción (opcional)",
                placeholder="Breve descripción del uso de esta cuenta",
                height=100,
            )

        st.markdown("")
        if st.button("Guardar cuenta", type="primary"):
            if not codigo or not nombre:
                st.error("Código y nombre son obligatorios.")
            else:
                ok, msg = add_cuenta(codigo, nombre, tipo, subcategoria, descripcion)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        divider()
        st.markdown(
            """
            <div class="hint-box">
            <strong>Convención de códigos sugerida:</strong><br>
            <code>1.x.xx</code> Activos &nbsp;|&nbsp;
            <code>2.x.xx</code> Pasivos &nbsp;|&nbsp;
            <code>3.x.xx</code> Patrimonio Neto &nbsp;|&nbsp;
            <code>4.x.xx</code> Ingresos (R+) &nbsp;|&nbsp;
            <code>5.x.xx</code> Egresos (R−)
            </div>
            """,
            unsafe_allow_html=True,
        )
