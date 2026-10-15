"""
modulo_estadisticas.py
Santec Software — Módulo de Estadísticas Biológicas
"""
import streamlit as st
import pandas as pd
import sqlite3

from demo_db import get_db_path

def render_estadisticas(accion: str):
    """Enrutador de pantallas del módulo estadísticas."""
    if accion == "Recría":
        _pantalla_recria()
    elif accion == "Producción":
        _pantalla_produccion()
    elif accion in ["Galpones recría", "Galpones Producción"]:
        _pantalla_gestion_galpones(accion)
    else:
        st.title(f"📈 Estadística › {accion}")

                                                                                
def _pantalla_gestion_galpones(tipo_modulo: str):
    st.title(f"🛖 Administrador de {tipo_modulo}")
    st.markdown("Alta y configuración de los lotes de aves alojadas en los galpones.")
    
    tipo_bd = "RECRIA" if "recría" in tipo_modulo.lower() else "PRODUCCION"
    
    con = sqlite3.connect(get_db_path())
    cursor = con.cursor()
    
                                                                       
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS galpones_maestro (
            NUMERO TEXT PRIMARY KEY,
            TIPO TEXT,
            PLANTEL TEXT,
            AVES_ALOJADAS INTEGER,
            SEMANA_ACTUAL INTEGER,
            ESTADO TEXT
        )
    """)
    con.commit()

    tab_ver, tab_alta = st.tabs(["📋 Galpones Activos", "➕ Habilitar Nuevo Lote/Galpón"])

    with tab_alta:
        with st.form("form_alta_galpon", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nro_galpon = st.text_input("Número de Galpón (Ej: 01)")
                plantel = st.text_input("Nombre/Código del Plantel")
            with c2:
                aves_alojadas = st.number_input("Cantidad de Aves Alojadas", min_value=1, value=10000, step=100)
                semana_ini = st.number_input("Semana de Vida Inicial", min_value=1, value=1)
                
            if st.form_submit_button("💾 Guardar y Habilitar Galpón", type="primary"):
                if not nro_galpon:
                    st.error("El número de galpón es obligatorio.")
                else:
                    try:
                        cursor.execute("""
                            INSERT OR REPLACE INTO galpones_maestro (NUMERO, TIPO, PLANTEL, AVES_ALOJADAS, SEMANA_ACTUAL, ESTADO)
                            VALUES (?, ?, ?, ?, ?, 'ACTIVO')
                        """, (nro_galpon.zfill(2), tipo_bd, plantel.upper(), aves_alojadas, semana_ini))
                        con.commit()
                        st.success(f"¡Galpón {nro_galpon.zfill(2)} habilitado correctamente para {tipo_bd}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

    with tab_ver:
        df_galpones = pd.read_sql_query("SELECT * FROM galpones_maestro WHERE TIPO = ?", con, params=[tipo_bd])
        if not df_galpones.empty:
            st.dataframe(df_galpones, use_container_width=True, hide_index=True)
        else:
            st.info(f"No hay galpones de {tipo_bd} cargados en el sistema.")

    con.close()


                                                                                
def _pantalla_recria():
    st.title("🐣 Control de Recría")
    st.markdown("Seguimiento diario de mortalidad y consumo de alimento en fase de desarrollo.")
    
    with st.form("form_recria"):
        st.subheader("Carga Diaria")
        col_g, col_f = st.columns(2)
        with col_g: galpon = st.text_input("Nº de Galpón", value="01")
        with col_f: aves_inicio = st.number_input("Stock Inicial de Aves", min_value=1, value=10000)
        
        st.markdown("---")
        st.write("**1. Mortalidad y Descartes**")
        c1, c2, c3 = st.columns(3)
        with c1: mortandad = st.number_input("Mortandad Diaria (Cabezas)", min_value=0, value=0)
        with c2: descarte = st.number_input("Descarte (Cabezas)", min_value=0, value=0)
        with c3: recuperado = st.number_input("Recuperados (Cabezas)", min_value=0, value=0)
        
        aves_vivas = aves_inicio - mortandad - descarte + recuperado
        
        st.markdown("---")
        st.write("**2. Consumo de Alimento**")
        c_al1, c_al2 = st.columns(2)
        with c_al1: 
            consumo_total_kg = st.number_input("Alimento Total del Galpón (Kgs)", min_value=0.0, step=10.0)
        with c_al2:
            cons_individual_gr = (consumo_total_kg / aves_vivas) * 1000 if aves_vivas > 0 else 0
            st.info(f"**Consumo Individual:** {cons_individual_gr:.2f} gramos/ave")

        if st.form_submit_button("📊 Calcular planilla (sin guardar)", type="primary"):
            st.info(f"Cálculo de ejemplo para el Galpón {galpon}. Aves vivas: {aves_vivas}. Esta pantalla no persiste planillas.")


                                                                                
def _pantalla_produccion():
    st.title("🥚 Control de Producción")
    st.markdown("Seguimiento de postura (huevos), mortalidad y consumo en fase productiva.")
    
    with st.form("form_produccion"):
        st.subheader("Planilla Diaria de Producción")
        col_g, col_f = st.columns(2)
        with col_g: galpon = st.text_input("Nº de Galpón", value="02")
        with col_f: aves_alojadas = st.number_input("Alojadas al Inicio", min_value=1, value=15000)
        
        st.markdown("---")
        st.write("**1. Producción de Huevos (Postura)**")
        c1, c2 = st.columns(2)
        with c1: huevos_incubables = st.number_input("Huevos Aptos / Incubables", min_value=0, value=0)
        with c2: huevos_descarte = st.number_input("Huevos Rotos / Descarte", min_value=0, value=0)
        
        total_huevos = huevos_incubables + huevos_descarte
        porcentaje_postura = (total_huevos / aves_alojadas) * 100 if aves_alojadas > 0 else 0
        
        st.markdown("---")
        st.write("**2. Bajas y Alimentación**")
        c3, c4 = st.columns(2)
        with c3: mortandad = st.number_input("Mortandad Diaria", min_value=0, value=0)
        with c4: consumo_kg = st.number_input("Alimento (Kgs)", min_value=0.0, step=10.0)
        
        if st.form_submit_button("📈 Procesar Día", type="primary"):
            st.success(f"Galpón {galpon} procesado.")
            c_r1, c_r2, c_r3 = st.columns(3)
            c_r1.metric("Total Huevos Día", f"{total_huevos}")
            c_r2.metric("% de Postura", f"{porcentaje_postura:.1f} %")
            
            aves_vivas = aves_alojadas - mortandad
            gr_por_ave = (consumo_kg / aves_vivas) * 1000 if aves_vivas > 0 else 0
            c_r3.metric("Consumo x Ave", f"{gr_por_ave:.1f} grs")