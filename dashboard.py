"""
dashboard.py
Santec Software — Enrutador Principal
"""
import streamlit as st
import pandas as pd
import sqlite3

# Importación de los motores modulares
from modulo_proveedores import render_proveedores
from modulo_clientes import render_clientes  
from modulo_articulos import render_articulos
from modulo_facturacion import render_facturacion
from modulo_listados import render_listados         
from modulo_estadisticas import render_estadisticas 
# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Santec Software - Gestión Avícola",
    page_icon="🐓",
    layout="wide"
)

# --- 2. BARRA LATERAL (SIDEBAR) ---
st.title("Gestión Avícola - Demostración")
st.caption("Versión de portfolio con datos 100% sintéticos. Sin conexión a la empresa ni validez fiscal.")
with st.expander("Cómo probar esta demo", expanded=False):
    st.markdown("1. Explorá Clientes y sus cuentas corrientes.\n2. En Ventas, elegí un cliente Demo y agregá un artículo.\n3. Emití un comprobante de prueba y revisá el historial.\n4. Consultá Proveedores, Artículos y Listados.\n\nCada visitante usa su propia base temporal. Las pantallas biológicas incluyen cálculos demostrativos; no implementan todas las funciones del sistema original.")
from demo_db import reset_demo
st.sidebar.title("🐓 Menú Principal")
if st.sidebar.button("Reiniciar mis datos de prueba"):
    reset_demo()
    st.rerun()
st.sidebar.caption("No ingreses datos reales. La sesión no es almacenamiento permanente.")
st.sidebar.markdown("---")

modulo = st.sidebar.selectbox(
    "MÓDULO:",
    ["CLIENTES", "PROVEEDORES", "ARTICULOS", "VENTAS", "LISTADOS", "ESTADISTICA"]
)
st.sidebar.markdown("---")

# ==========================================
# INTERFAZ Y LÓGICA DE MÓDULOS
# ==========================================

# --- MÓDULO CLIENTES ---
if modulo == "CLIENTES":
    accion = st.sidebar.radio(
        "Opciones:",
        ["Listados clientes", "Informe Cta. Cte.", "Saldos", "Altas/Modificaciones", 
         "Pagos", "Cheques", "Códigos postales", "Recibos", "Venta por provincias", "Libro Percepción IB"]
    )
    # Delegamos el control directo al archivo modular
    render_clientes(accion)

# --- MÓDULO PROVEEDORES ---
elif modulo == "PROVEEDORES":
    accion = st.sidebar.radio(
        "Opciones:",
        ["Altas/Modificaciones", "Rubros", "Artículos", "Listado", "Facturas", 
         "Nota Crédito", "Nota Débito", "Ver pagos", "Bancos", "Cancela facturas", 
         "Retención I.B.", "Retención Ganancias", "Retención IVA", "Libros retenciones", "Informes cta cte"]
    )
    # Delegamos el control directo al archivo modular
    render_proveedores(accion)

# --- MÓDULO ARTÍCULOS ---
elif modulo == "ARTICULOS":
    accion = st.sidebar.radio(
        "Opciones:", 
        ["Artículos", "Lista de Precios", "Precios clientes"]
    )
    # Delegamos el control directo al archivo modular
    render_articulos(accion)

# --- MÓDULO VENTAS / FACTURACIÓN ---
elif modulo == "VENTAS":
    accion = st.sidebar.radio(
        "Opciones:", 
        ["Nueva Venta / Remito", "Notas de Crédito", "Notas de Débito", "Historial / Buscar", "Libro IVA Ventas"]
    )
    # Delegamos el control directo al archivo modular
    render_facturacion(accion)

# --- MÓDULOS RESTANTES ---
elif modulo == "LISTADOS":
    accion = st.sidebar.radio("Opciones:", ["Cert. vacunas"])
    render_listados(accion)

elif modulo == "ESTADISTICA":
    accion = st.sidebar.radio("Opciones:", ["Galpones recría", "Recría", "Galpones Producción", "Producción"])
    render_estadisticas(accion)