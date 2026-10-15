"""
modulo_facturacion.py
Santec Software — Módulo Principal de Ventas, Notas y Reportes
"""
import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime

from demo_db import get_db_path



def render_facturacion(accion: str):
    if "carrito" not in st.session_state:
        st.session_state.carrito = pd.DataFrame(columns=["CODIGO", "DESCRIPCION", "CANTIDAD", "UNITARIO", "SUBTOTAL"])
    """Enrutador principal de pantallas del módulo de Facturación."""
    if accion == "Nueva Venta / Remito":
        _pantalla_emisor("Factura / Remito")
    elif accion == "Notas de Crédito":
        _pantalla_emisor("Nota de Crédito")
    elif accion == "Notas de Débito":
        _pantalla_emisor("Nota de Débito")
    elif accion == "Historial / Buscar":
        _pantalla_historial_facturas()
    elif accion == "Libro IVA Ventas":
        _pantalla_libro_iva()
    else:
        st.title(f"🛒 Facturación › {accion}")

                                                                                
def _pantalla_emisor(tipo_doc: str):
    st.title(f"🛒 Emisión de {tipo_doc}")
    
    con = sqlite3.connect(get_db_path())
    cursor = con.cursor()
    
    try:
        cursor.execute("ALTER TABLE factgral ADD COLUMN PAGO REAL DEFAULT 0")
        con.commit()
    except:
        pass
    
                      
    st.subheader("1. Datos del Comprobante")
    col_t1, col_t2, col_t3 = st.columns(3)
    
    with col_t1:
        if tipo_doc == "Factura / Remito":
            opciones = ["Factura A", "Factura B", "Remito R"]
        elif tipo_doc == "Nota de Crédito":
            opciones = ["Nota de Crédito A", "Nota de Crédito B"]
        elif tipo_doc == "Nota de Débito":
            opciones = ["Nota de Débito A", "Nota de Débito B"]
            
        tipo_comprobante = st.selectbox("Tipo:", opciones)
        
    with col_t2:
        fecha_fact = st.date_input("Fecha")
    with col_t3:
        if "Remito" in opciones:
            nro_remito = st.text_input("Nº Remito (Opcional)", max_chars=8)
        else:
            nro_remito = "00000000"
            st.info("No aplica remito.")

                                                                            
    try:
        if " A" in tipo_comprobante:
            filtro_sql = "TIPO IN ('I', 'NI')"
        elif " B" in tipo_comprobante:
            filtro_sql = "TIPO IN ('MT', 'CF', 'E')"
        else:
            filtro_sql = "1=1" 
            
        df_clientes = pd.read_sql_query(f"SELECT NUMERO, NOMBRE, CUIT, TIPO FROM clientes WHERE {filtro_sql} ORDER BY NOMBRE", con)
        lista_clie = [f"{row['NUMERO']} - {row['NOMBRE']} ({row['TIPO']})" for _, row in df_clientes.iterrows()]
    except:
        lista_clie = []

    cliente_sel = st.selectbox("Cliente:", [""] + lista_clie)

                           
    st.markdown("---")
    st.subheader("2. Carga de Artículos / Conceptos")
    
    try:
        df_articulos = pd.read_sql_query("SELECT CODIGO, DESCRIP, PRECIO FROM articulo ORDER BY DESCRIP", con)
        lista_art = [f"{row['CODIGO']} - {row['DESCRIP']} ($ {row['PRECIO']})" for _, row in df_articulos.iterrows()]
    except:
        lista_art = []

    with st.form("form_agregar_item", clear_on_submit=True):
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            art_sel = st.selectbox("Artículo", [""] + lista_art)
        with c2:
            cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1)
        with c3:
            btn_add = st.form_submit_button("➕ Añadir", use_container_width=True)
            
        if btn_add and art_sel:
            cod_art = art_sel.split(" - ")[0]
            desc_art = art_sel.split(" - ")[1].split(" ($")[0]
            precio_unit = float(art_sel.split("($ ")[1].replace(")", ""))
            subt = cantidad * precio_unit
            
            nuevo_item = pd.DataFrame([{
                'CODIGO': cod_art, 'DESCRIPCION': desc_art, 
                'CANTIDAD': cantidad, 'UNITARIO': precio_unit, 'SUBTOTAL': subt
            }])
            st.session_state.carrito = pd.concat([st.session_state.carrito, nuevo_item], ignore_index=True)
            st.rerun()

                                         
    if not st.session_state.carrito.empty:
        st.dataframe(st.session_state.carrito, use_container_width=True, hide_index=True)
        
        if st.button("🗑️ Vaciar Grilla"):
            st.session_state.carrito = pd.DataFrame(columns=['CODIGO', 'DESCRIPCION', 'CANTIDAD', 'UNITARIO', 'SUBTOTAL'])
            st.rerun()
            
                               
        total_items = st.session_state.carrito['SUBTOTAL'].sum()
        iva_insc = 21.0
        perc_ib = 3.0 
        
        iva_calculado = 0.0
        neto_calculado = total_items
        monto_ib = 0.0

        if " A" in tipo_comprobante or ("Remito" in tipo_comprobante and " (I)" in str(cliente_sel)):
            iva_calculado = total_items * (iva_insc / 100)
            neto_calculado = total_items
        elif " B" in tipo_comprobante:
            iva_calculado = total_items - (total_items / (1 + (iva_insc / 100)))
            neto_calculado = total_items - iva_calculado
            
        if neto_calculado > 4000.0 and "Remito" not in tipo_comprobante:
            monto_ib = neto_calculado * (perc_ib / 100)
            
        total_final = neto_calculado + iva_calculado + monto_ib

        st.markdown("---")
        c_tot1, c_tot2, c_tot3, c_tot4 = st.columns(4)
        c_tot1.metric("Neto Gravado", f"$ {neto_calculado:,.2f}")
        c_tot2.metric("I.V.A.", f"$ {iva_calculado:,.2f}")
        c_tot3.metric("Perc. I.B.", f"$ {monto_ib:,.2f}")
        
        color = "normal" if "Crédito" not in tipo_comprobante else "inverse"
        c_tot4.metric("TOTAL FINAL", f"$ {total_final:,.2f}", delta="A Favor Cliente" if "Crédito" in tipo_comprobante else None, delta_color=color)

                              
        st.markdown("---")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            pago_contado = st.checkbox("Pago al Contado / Cancelación Automática")
            
        with col_btn2:
            if st.button(f"💾 EMITIR {tipo_comprobante.upper()}", type="primary", use_container_width=True):
                if not cliente_sel:
                    st.error("Debe seleccionar un cliente.")
                else:
                    cod_cliente = cliente_sel.split(" - ")[0]
                    
                                                      
                    if "Factura" in tipo_comprobante: tipo_c = tipo_comprobante.split(" ")[1]            
                    elif "Remito" in tipo_comprobante: tipo_c = "R"
                    elif "Crédito A" in tipo_comprobante: tipo_c = "NCA"
                    elif "Crédito B" in tipo_comprobante: tipo_c = "NCB"
                    elif "Débito A" in tipo_comprobante: tipo_c = "NDA"
                    elif "Débito B" in tipo_comprobante: tipo_c = "NDB"
                    
                    fecha_str = fecha_fact.strftime("%Y-%m-%d")
                    periodo = fecha_fact.strftime("%Y%m")
                    
                    try:
                        cursor.execute("SELECT MAX(CAST(NUMERO AS INTEGER)) FROM factgral WHERE TIPO = ? AND PREFIJO = '0001'", (tipo_c,))
                        ult_num = cursor.fetchone()[0]
                        nuevo_num = str(1 if ult_num is None else ult_num + 1).zfill(8)
                        
                                                        
                        cursor.execute("""
                            INSERT INTO factgral (FECHA, TIPO, PREFIJO, NUMERO, PERIODO, CLIENTE, TOTALITEMS, NETO, IVA1, PERCIBSF, TOTAL, REMITO, PAGO)
                            VALUES (?, ?, '0001', ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                        """, (fecha_str, tipo_c, nuevo_num, periodo, cod_cliente, len(st.session_state.carrito), neto_calculado, iva_calculado, monto_ib, total_final, str(nro_remito).zfill(8)))
                        
                                             
                        for _, row in st.session_state.carrito.iterrows():
                            cursor.execute("""
                                INSERT INTO factdato (TIPO, NUMERO, CANTIDAD, CODIGO, UNITARIO, TOTAL)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (tipo_c, nuevo_num, row['CANTIDAD'], row['CODIGO'], row['UNITARIO'], row['SUBTOTAL']))
                        
                                                                            
                        detalle_op = f"Comp.{tipo_c} 0001-{nuevo_num}"
                        
                        if "Crédito" in tipo_comprobante:
                                                                            
                            cursor.execute("""
                                INSERT INTO ctacte (NUMERO, FECHA, OPERACION, DEBE, HABER, SALDO)
                                VALUES (?, ?, ?, 0, ?, 0)
                            """, (cod_cliente, fecha_str, detalle_op, total_final))
                        else:
                                                                                       
                            cursor.execute("""
                                INSERT INTO ctacte (NUMERO, FECHA, OPERACION, DEBE, HABER, SALDO)
                                VALUES (?, ?, ?, ?, 0, 0)
                            """, (cod_cliente, fecha_str, detalle_op, total_final))
                        
                            if pago_contado:
                                cursor.execute("""
                                    INSERT INTO ctacte (NUMERO, FECHA, OPERACION, DEBE, HABER, SALDO)
                                    VALUES (?, ?, ?, 0, ?, 0)
                                """, (cod_cliente, fecha_str, f"Pago/Canc. {detalle_op}", total_final))
                                
                                cursor.execute("UPDATE factgral SET PAGO = ? WHERE TIPO = ? AND NUMERO = ?", (total_final, tipo_c, nuevo_num))
                        
                        con.commit()
                        
                        st.session_state.carrito = pd.DataFrame(columns=['CODIGO', 'DESCRIPCION', 'CANTIDAD', 'UNITARIO', 'SUBTOTAL'])
                        st.success(f"✅ ¡{tipo_comprobante} 0001-{nuevo_num} emitida con éxito!")
                        
                    except Exception as e:
                        con.rollback()
                        st.error(f"Error al procesar el comprobante: {e}")

    con.close()

                                                                                
def _pantalla_historial_facturas():
    st.title("🗄️ Historial de Comprobantes Emitidos")
    
    con = sqlite3.connect(get_db_path())
    try:
        query = """
            SELECT f.FECHA, f.TIPO, f.PREFIJO, f.NUMERO, c.NOMBRE AS CLIENTE, 
                   f.NETO, f.IVA1 AS IVA, f.PERCIBSF AS IB, f.TOTAL, 
                   COALESCE(f.PAGO, 0) AS PAGO, (f.TOTAL - COALESCE(f.PAGO, 0)) AS SALDO
            FROM factgral f
            LEFT JOIN clientes c ON f.CLIENTE = c.NUMERO
            ORDER BY f.rowid DESC
            LIMIT 500
        """
        df_historial = pd.read_sql_query(query, con)
        
        busqueda = st.text_input("🔍 Buscar por Número o Cliente:")
        if busqueda:
            df_historial = df_historial[df_historial.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]

        st.dataframe(
            df_historial,
            use_container_width=True,
            hide_index=True,
            column_config={
                "NETO": st.column_config.NumberColumn(format="$ %.2f"),
                "IVA": st.column_config.NumberColumn(format="$ %.2f"),
                "IB": st.column_config.NumberColumn(format="$ %.2f"),
                "TOTAL": st.column_config.NumberColumn(format="$ %.2f"),
                "PAGO": st.column_config.NumberColumn(format="$ %.2f"),
                "SALDO": st.column_config.NumberColumn(format="$ %.2f")
            }
        )
    except Exception as e:
        st.error(f"Error al leer el historial: {e}")
        
    con.close()

                                                                                
def _pantalla_libro_iva():
    st.title("📚 Libro IVA Ventas")
    st.markdown("Reporte impositivo mensual para exportar al contador.")
    
    con = sqlite3.connect(get_db_path())
    
    col1, col2 = st.columns(2)
    with col1:
        mes_filtro = st.selectbox("Mes", ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"], index=datetime.now().month - 1)
    with col2:
        anio_filtro = st.selectbox("Año", [str(y) for y in range(2023, 2030)], index=[str(y) for y in range(2023, 2030)].index(str(datetime.now().year)))

    periodo_str = f"{anio_filtro}{mes_filtro}"
    
    try:
                                               
        query = f"""
            SELECT f.FECHA, f.TIPO, f.PREFIJO, f.NUMERO, c.CUIT, c.NOMBRE AS RAZON_SOCIAL, 
                   f.NETO AS NETO_GRAVADO, f.IVA1 AS IMPORTE_IVA, f.PERCIBSF, f.TOTAL
            FROM factgral f
            LEFT JOIN clientes c ON f.CLIENTE = c.NUMERO
            WHERE f.PERIODO = '{periodo_str}' AND f.TIPO != 'R'
            ORDER BY f.FECHA ASC, f.NUMERO ASC
        """
        df_iva = pd.read_sql_query(query, con)
        
        if not df_iva.empty:
            st.dataframe(df_iva, use_container_width=True, hide_index=True)
            
                             
            st.markdown("---")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Neto Gravado", f"$ {df_iva['NETO_GRAVADO'].sum():,.2f}")
            c2.metric("Total I.V.A.", f"$ {df_iva['IMPORTE_IVA'].sum():,.2f}")
            c3.metric("Total Percepciones", f"$ {df_iva['PERCIBSF'].sum():,.2f}")
            c4.metric("TOTAL FACTURADO", f"$ {df_iva['TOTAL'].sum():,.2f}")
            
                      
            csv = df_iva.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Exportar Libro IVA a Excel (CSV)",
                data=csv,
                file_name=f'Libro_IVA_Ventas_{periodo_str}.csv',
                mime='text/csv',
                type="primary"
            )
        else:
            st.info(f"No hay facturas registradas en el período {periodo_str}.")
            
    except Exception as e:
        st.error(f"Error al generar Libro IVA: {e}")
        
    con.close()