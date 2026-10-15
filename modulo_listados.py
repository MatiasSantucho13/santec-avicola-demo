"""
modulo_listados.py
Santec Software — Módulo de Listados y Sanidad
"""
import sqlite3
import pandas as pd
import streamlit as st

from demo_db import get_db_path

def render_listados(accion: str):
    """Enrutador de pantallas del módulo listados."""
    if accion == "Cert. vacunas":
        _pantalla_vacunas()
    else:
        st.title(f"🖨️ Listados › {accion}")
        st.info(f"La pantalla **{accion}** está en desarrollo.")

def _pantalla_vacunas():
    st.title("💉 Control y Certificados de Vacunación")
    st.markdown("Registro sanitario de los lotes y aplicaciones de vacunas.")
    
    con = sqlite3.connect(get_db_path())
    cursor = con.cursor()
    
                                                                           
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vacunas (
            ID INTEGER PRIMARY KEY AUTOINCREMENT
        )
    """)
    con.commit()

                                                                                              
    columnas_requeridas = [
        "FACTURA", "FECHA", "RAZA", "LOTE_VACUNA", "NOMBRE_VACUNA", 
        "TIPO", "VIA", "SERIES", "MARCAS", "VENCE", "DOSIS"
    ]
    
    for col in columnas_requeridas:
        try:
            cursor.execute(f"ALTER TABLE vacunas ADD COLUMN {col} TEXT")
        except Exception:
            pass                                                                        
            
    con.commit()
                                                                           

    tab_ver, tab_alta = st.tabs(["📋 Historial de Vacunación", "➕ Registrar Aplicación"])

    with tab_alta:
        st.subheader("Cargar Nuevo Certificado")
        with st.form("form_alta_vacuna", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                factura = st.text_input("Nº Factura / Remito")
                fecha = st.date_input("Fecha de Aplicación")
                raza = st.text_input("Raza / Línea Genética")
                lote_vacunas = st.text_input("Lote de Vacunas")
            with col2:
                nombre = st.text_input("Nombre de la Vacuna")
                tipo = st.text_input("Tipo (Aviar, etc.)")
                via = st.selectbox("Vía de Aplicación", ["Ocular", "Oral/Agua", "Inyectable", "Spray", "Punzón Alar"])
                dosis = st.text_input("Dosis Aplicada")
                
            col3, col4, col5 = st.columns(3)
            with col3: series = st.text_input("Nº de Serie")
            with col4: marcas = st.text_input("Marca / Laboratorio")
            with col5: vence = st.date_input("Fecha de Vencimiento")

            if st.form_submit_button("💾 Guardar Registro Sanitario", type="primary"):
                cursor.execute("""
                    INSERT INTO vacunas (FACTURA, FECHA, RAZA, LOTE_VACUNA, NOMBRE_VACUNA, TIPO, VIA, SERIES, MARCAS, VENCE, DOSIS)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (factura, fecha.strftime("%Y-%m-%d"), raza.upper(), lote_vacunas.upper(), nombre.upper(), tipo.upper(), via, series, marcas.upper(), vence.strftime("%Y-%m-%d"), dosis))
                con.commit()
                st.success("¡Registro guardado correctamente!")
                st.rerun()

    with tab_ver:
        df_vac = pd.read_sql_query("SELECT * FROM vacunas ORDER BY FECHA DESC", con)
        if not df_vac.empty:
            st.dataframe(df_vac.drop(columns=['ID'], errors='ignore'), use_container_width=True, hide_index=True)
        else:
            st.info("No hay registros de vacunación en la base.")
            
    con.close()