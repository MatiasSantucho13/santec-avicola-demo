"""
modulo_proveedores.py
Santec Software — Módulo Proveedores Completo
"""
import sqlite3
import pandas as pd
import streamlit as st
import datetime

from demo_db import get_db_path

def render_proveedores(accion: str):
    """Enrutador de pantallas del módulo proveedores."""
    if accion == "Informes cta cte":
        _pantalla_ctacte()
    elif accion == "Altas/Modificaciones":
        _pantalla_padron_maestro()
    elif accion == "Listado":
        _pantalla_listado_proveedores()
    elif accion == "Rubros":
        _pantalla_rubros()
    elif accion == "Artículos":
        _pantalla_articulos()
    elif accion == "Ver pagos" or accion == "Cancela facturas":
        _pantalla_pagos()
    elif accion in ["Facturas", "Nota Crédito", "Nota Débito"]:
                                                                       
        _pantalla_cargar_factura()
    elif accion == "Bancos":
        _pantalla_bancos()
    elif accion == "Retención I.B.":
        _pantalla_retenciones("I.B.")
    elif accion == "Retención Ganancias":
        _pantalla_retenciones("Ganancias")
    elif accion == "Retención IVA":
        _pantalla_retenciones("IVA")
    elif accion == "Libros retenciones":
        _pantalla_libro_retenciones()
    else:
        st.info(f"La opción **{accion}** está en desarrollo.")

                                                                                
def _pantalla_facturas():
    st.title("🧾 Proveedores › Facturas de Compra")
    con = sqlite3.connect(get_db_path())

    col1, col2, col3 = st.columns(3)
    with col1:
        busqueda = st.text_input("🔍 Buscar (proveedor, CUIT, número)")
    with col2:
        tipo = st.selectbox("Tipo comprobante", ["Todos", "A", "B", "C"])
    with col3:
        periodo = st.text_input("Período (ej: 202403)")

    query = "SELECT * FROM proveedores_facturas WHERE 1=1"
    params = []

    if busqueda:
        query += " AND (CLIEDENO LIKE ? OR CUIT LIKE ? OR NUMERO LIKE ?)"
        like = f"%{busqueda}%"
        params += [like, like, like]
    if tipo != "Todos":
        query += " AND TIPO = ?"
        params.append(tipo)
    if periodo:
        query += " AND PERIODO = ?"
        params.append(periodo)

    query += " ORDER BY FECHA DESC LIMIT 5000"

    try:
        df = pd.read_sql_query(query, con, params=params)
        con.close()

        if df.empty:
            st.warning("No se encontraron facturas con esos filtros.")
            return

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Comprobantes", f"{len(df):,}")
        m2.metric("Total Neto", f"${df['NETO'].sum():,.0f}")
        m3.metric("Total IVA", f"${df['IVA1'].sum():,.0f}")
        m4.metric("Total General", f"${df['TOTAL_A'].sum():,.0f}")

        st.markdown("---")
        columnas_mostrar = {
            "FECHA": "Fecha", "TIPO": "Tipo", "NUMERO": "Número",
            "CLIEDENO": "Proveedor", "CUIT": "CUIT", "NETO": "Neto",
            "IVA1": "IVA 21%", "IVA10_5": "IVA 10.5%", "TOTAL_A": "Total"
        }
        cols_existentes = {k: v for k, v in columnas_mostrar.items() if k in df.columns}
        df_mostrar = df[list(cols_existentes.keys())].rename(columns=cols_existentes)

        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Error al leer la base: {e}")


                                                                                
def _pantalla_ctacte():
    st.title("📒 Proveedores › Cuenta Corriente")
    con = sqlite3.connect(get_db_path())

    col1, col2 = st.columns(2)
    with col1:
        nro_prov = st.text_input("Número de proveedor")
    with col2:
        busq_op = st.text_input("🔍 Buscar en operación")

    query = "SELECT * FROM proveedores_ctacte WHERE 1=1"
    params = []

    if nro_prov:
        query += " AND NUMERO = ?"
        params.append(nro_prov)
    if busq_op:
        query += " AND OPERACION LIKE ?"
        params.append(f"%{busq_op}%")

    query += " ORDER BY FECHA DESC LIMIT 3000"

    try:
        df = pd.read_sql_query(query, con, params=params)
        con.close()

        if df.empty:
            st.warning("No hay movimientos con esos filtros.")
            return

        m1, m2, m3 = st.columns(3)
        m1.metric("Movimientos", f"{len(df):,}")
        m2.metric("Total Debe", f"${df['DEBE'].sum():,.2f}")
        m3.metric("Total Haber", f"${df['HABER'].sum():,.2f}")

        st.markdown("---")
        st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Error: {e}")


                                                                                
def _pantalla_listado_proveedores():
    st.title("🏭 Proveedores › Resumen Operativo")
    st.markdown("Vista analítica generada automáticamente desde el historial.")
    con = sqlite3.connect(get_db_path())
    busqueda = st.text_input("🔍 Buscar proveedor")

    query = "SELECT * FROM v_resumen_proveedores WHERE 1=1"
    params = []
    if busqueda:
        query += " AND (nombre LIKE ? OR CUIT LIKE ?)"
        params += [f"%{busqueda}%", f"%{busqueda}%"]

    try:
        df = pd.read_sql_query(query, con, params=params)
        con.close()
        st.success(f"{len(df)} proveedores encontrados")
        st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Error: {e}")


                                                                                
def _pantalla_padron_maestro():
    st.title("📇 Proveedores › Altas y Modificaciones")
    st.markdown("Gestión directa del padrón maestro de proveedores (Mapeo exacto FoxPro).")
    
    con = sqlite3.connect(get_db_path())
    tab_alta, tab_mod = st.tabs(["➕ Alta de Proveedor", "✏️ Modificar Existente"])

                                  
    with tab_alta:
        st.subheader("Ingresar Nuevo Proveedor")
        with st.form("form_alta_prov", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                nombre = st.text_input("NOMBRE (Razón Social) *")
                cuit = st.text_input("CUIT")
                tipo = st.text_input("TIPO (Condición IVA)")
                ing_brutos = st.text_input("ING_BRUTOS (Nº Ingresos Brutos)")
            with col2:
                direccion = st.text_input("DIRECCION")
                localidad = st.text_input("LOCALIDAD")
                codpostal = st.text_input("CODPOSTAL")
                provincia = st.text_input("PROVINCIA")
            with col3:
                cm = st.text_input("CM (Convenio Multilateral)")
                imputa = st.text_input("IMPUTA (Cuenta Imputación)")
                discrimina = st.text_input("DISCRIMINA (Cuenta Contable)", help="Debe ser numérico")
                tipo_gana = st.text_input("TIPO_GANA (Cat. Ganancias)")

            st.markdown("*Campos obligatorios")
            submit_alta = st.form_submit_button("💾 Guardar Nuevo Proveedor", type="primary")

        if submit_alta:
            if not nombre:
                st.error("⚠️ El campo NOMBRE es obligatorio.")
            else:
                try:
                    cursor = con.cursor()
                    cursor.execute("SELECT MAX(CAST(NUMERO AS INTEGER)) FROM proveedores_maestro")
                    max_num = cursor.fetchone()[0]
                    nuevo_numero = str(1 if max_num is None else max_num + 1)

                    val_discrimina = float(discrimina) if discrimina.strip() else 0.0

                    cursor.execute("""
                        INSERT INTO proveedores_maestro 
                        (NUMERO, NOMBRE, DIRECCION, CODPOSTAL, LOCALIDAD, PROVINCIA, CUIT, TIPO, ING_BRUTOS, CM, IMPUTA, DISCRIMINA, TIPO_GANA)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (nuevo_numero, nombre.upper(), direccion.upper(), codpostal, localidad.upper(), provincia.upper(), cuit, tipo, ing_brutos, cm, imputa, val_discrimina, tipo_gana))
                    
                    con.commit()
                    st.success(f"✔️ ¡Proveedor '{nombre}' guardado con el Código Nº {nuevo_numero}!")
                except ValueError:
                    st.error("❌ El campo DISCRIMINA debe ser un número válido.")
                except Exception as e:
                    st.error(f"❌ Error al guardar en la base de datos: {e}")

                                          
    with tab_mod:
        st.subheader("Editar Proveedor Existente")
        
        try:
            df_provs = pd.read_sql_query("SELECT NUMERO, NOMBRE FROM proveedores_maestro ORDER BY NOMBRE", con)
            lista_edicion = [f"{row['NUMERO']} - {row['NOMBRE']}" for _, row in df_provs.iterrows()]
        except Exception:
            lista_edicion = []

        if lista_edicion:
            prov_a_editar = st.selectbox("🔍 Buscar proveedor a modificar:", lista_edicion)
            
            if prov_a_editar:
                cod_edit = prov_a_editar.split(" - ")[0]
                
                cursor = con.cursor()
                cursor.execute("""
                    SELECT NOMBRE, DIRECCION, CODPOSTAL, LOCALIDAD, PROVINCIA, CUIT, TIPO, ING_BRUTOS, CM, IMPUTA, DISCRIMINA, TIPO_GANA 
                    FROM proveedores_maestro WHERE NUMERO = ?
                """, (cod_edit,))
                datos = cursor.fetchone()
                
                if datos:
                    with st.form("form_mod_prov"):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            mod_nombre = st.text_input("NOMBRE", value=datos[0] or "")
                            mod_cuit = st.text_input("CUIT", value=datos[5] or "")
                            mod_tipo = st.text_input("TIPO", value=datos[6] or "")
                            mod_ing_brutos = st.text_input("ING_BRUTOS", value=datos[7] or "")
                        with c2:
                            mod_direccion = st.text_input("DIRECCION", value=datos[1] or "")
                            mod_localidad = st.text_input("LOCALIDAD", value=datos[3] or "")
                            mod_codpostal = st.text_input("CODPOSTAL", value=datos[2] or "")
                            mod_provincia = st.text_input("PROVINCIA", value=datos[4] or "")
                        with c3:
                            mod_cm = st.text_input("CM", value=datos[8] or "")
                            mod_imputa = st.text_input("IMPUTA", value=datos[9] or "")
                            mod_discrimina = st.text_input("DISCRIMINA", value=str(datos[10]) if datos[10] is not None else "")
                            mod_tipo_gana = st.text_input("TIPO_GANA", value=datos[11] or "")

                        submit_mod = st.form_submit_button("🔄 Actualizar Datos", type="primary")

                    if submit_mod:
                        try:
                            val_mod_discrimina = float(mod_discrimina) if mod_discrimina.strip() else 0.0
                            cursor.execute("""
                                UPDATE proveedores_maestro 
                                SET NOMBRE=?, DIRECCION=?, CODPOSTAL=?, LOCALIDAD=?, PROVINCIA=?, CUIT=?, TIPO=?, ING_BRUTOS=?, CM=?, IMPUTA=?, DISCRIMINA=?, TIPO_GANA=?
                                WHERE NUMERO=?
                            """, (mod_nombre.upper(), mod_direccion.upper(), mod_codpostal, mod_localidad.upper(), mod_provincia.upper(), mod_cuit, mod_tipo, mod_ing_brutos, mod_cm, mod_imputa, val_mod_discrimina, mod_tipo_gana, cod_edit))
                            
                            con.commit()
                            st.success(f"✔️ Datos del proveedor {cod_edit} actualizados correctamente.")
                            st.rerun() 
                        except ValueError:
                            st.error("❌ El campo DISCRIMINA debe ser numérico.")
                        except Exception as e:
                            st.error(f"❌ Error al actualizar: {e}")
        else:
            st.warning("No hay proveedores en la base de datos para modificar.")

    con.close()


                                                                                
def _pantalla_cargar_factura():
    st.title("➕ Proveedores › Cargar Comprobante")
    con = sqlite3.connect(get_db_path())
    
    try:
        df_prov = pd.read_sql_query("SELECT cod_proveedor, nombre FROM v_resumen_proveedores ORDER BY nombre", con)
        lista_proveedores = [f"{row['cod_proveedor']} - {row['nombre']}" for _, row in df_prov.iterrows()]
    except:
        lista_proveedores = ["0 - Sin datos (Correr migración)"]

    with st.form("form_nueva_factura", clear_on_submit=True):
        st.subheader("Datos del Comprobante")
        col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
        with col1:
            proveedor_sel = st.selectbox("Proveedor", lista_proveedores)
        with col2:
            operacion = st.selectbox("Operación", ["FC", "NC", "ND"])
        with col3:
            tipo_comp = st.selectbox("Tipo", ["A", "B", "C", "M"])
        with col4:
            fecha_comp = st.date_input("Fecha", datetime.date.today())

        col_p, col_n = st.columns(2)
        with col_p:
            prefijo = st.text_input("Punto de Venta (ej: 12)", max_chars=4)
        with col_n:
            numero = st.text_input("Número (ej: 345)", max_chars=8)

        st.markdown("---")
        st.subheader("Importes")
        c1, c2, c3 = st.columns(3)
        with c1:
            neto = st.number_input("Neto Gravado ($)", min_value=0.0)
            no_gravado = st.number_input("No Gravado ($)", min_value=0.0)
        with c2:
            iva_21 = st.number_input("IVA 21% ($)", min_value=0.0)
            iva_105 = st.number_input("IVA 10.5% ($)", min_value=0.0)
        with c3:
            percepciones = st.number_input("Percepciones ($)", min_value=0.0)
            total_calculado = st.number_input("TOTAL COMPROBANTE ($)", min_value=0.0)

        st.markdown("---")
        pago_contado = st.checkbox("💰 Registrar como Pago al Contado (Cancela saldo automáticamente)")
        submit = st.form_submit_button("💾 Guardar Comprobante", type="primary")

    if submit:
        if not prefijo or not numero:
            st.error("⚠️ El punto de venta y número de comprobante son obligatorios.")
            return
            
        numero_formateado = f"{prefijo.zfill(4)}-{numero.zfill(8)}"
        cod_prov = proveedor_sel.split(" - ")[0]
        nom_prov = proveedor_sel.split(" - ")[1]
        periodo = fecha_comp.strftime("%Y%m")
        fecha_str = fecha_comp.strftime("%Y-%m-%d")

        multiplicador = -1 if operacion == "NC" else 1
        m_neto = neto * multiplicador
        m_iva21 = iva_21 * multiplicador
        m_iva105 = iva_105 * multiplicador
        m_nograv = no_gravado * multiplicador
        m_percep = percepciones * multiplicador
        m_total = total_calculado * multiplicador

        cursor = con.cursor()
        try:
            cursor.execute("""
                INSERT INTO proveedores_facturas 
                (FECHA, PERIODO, COMPROB, TIPO, NUMERO, CLIENTE, CLIEDENO, NETO, IVA1, IVA10_5, NOGRAVA, PERCEP, TOTAL_A)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (fecha_str, periodo, operacion, tipo_comp, numero_formateado, cod_prov, nom_prov, m_neto, m_iva21, m_iva105, m_nograv, m_percep, m_total))

            detalle_op = f"{operacion}{tipo_comp} {numero_formateado} - {fecha_comp.strftime('%d/%m/%y')}"
            cursor.execute("""
                INSERT INTO proveedores_ctacte (NUMERO, FECHA, OPERACION, DEBE, HABER, SALDO)
                VALUES (?, ?, ?, ?, 0, 0)
            """, (cod_prov, fecha_str, detalle_op, m_total))

            if pago_contado:
                cursor.execute("""
                    INSERT INTO proveedores_ctacte (NUMERO, FECHA, OPERACION, DEBE, HABER, SALDO)
                    VALUES (?, ?, ?, 0, ?, 0)
                """, (cod_prov, fecha_str, f"Canc. Contado {numero_formateado}", m_total))

            con.commit()
            st.success(f"✔️ ¡Comprobante {numero_formateado} cargado con éxito e impactado en cuenta corriente!")

        except Exception as e:
            con.rollback()
            st.error(f"❌ Error al guardar en la base: {e}")
        finally:
            con.close()


                                                                                
def _pantalla_rubros():
    st.title("📂 Rubros de Proveedores")
    con = sqlite3.connect(get_db_path())
    
    st.subheader("Rubros Existentes")
    try:
        df_rubros = pd.read_sql_query("SELECT RUBRO, CONCEPTO FROM rubros ORDER BY CONCEPTO", con)
        st.dataframe(df_rubros, use_container_width=True, hide_index=True)
    except:
        st.error("No se pudo cargar la tabla de rubros.")

    st.markdown("---")
    st.subheader("➕ Agregar Nuevo Rubro")
    with st.form("form_nuevo_rubro", clear_on_submit=True):
        nuevo_concepto = st.text_input("Nuevo Concepto de Rubro")
        submit_rubro = st.form_submit_button("Guardar Rubro", type="primary")

    if submit_rubro:
        if not nuevo_concepto.strip():
            st.error("⚠️ DEBE INGRESAR UN RUBRO")
        else:
            cursor = con.cursor()
            cursor.execute("SELECT 1 FROM rubros WHERE CONCEPTO = ?", (nuevo_concepto.upper(),))
            if cursor.fetchone():
                st.warning("⚠️ DICHO RUBRO YA EXISTE")
            else:
                cursor.execute("SELECT MAX(CAST(RUBRO AS INTEGER)) FROM rubros")
                max_rubro = cursor.fetchone()[0] or 0
                nuevo_id = max_rubro + 1
                
                cursor.execute("INSERT INTO rubros (RUBRO, CONCEPTO) VALUES (?, ?)", 
                               (nuevo_id, nuevo_concepto.upper()))
                con.commit()
                st.success(f"✔️ Rubro '{nuevo_concepto}' guardado con éxito.")
                st.rerun() 
    con.close()


                                                                                
def _pantalla_articulos():
    st.title("📦 Artículos y Lista de Precios")
    con = sqlite3.connect(get_db_path())
    
    tab_alta, tab_lista = st.tabs(["➕ Nuevo Artículo", "📋 Listado y Edición"])

    with tab_alta:
        st.subheader("Ingresar Nuevo Artículo")
        
        cursor = con.cursor()
        try:
            cursor.execute("SELECT RUBRO, CONCEPTO FROM rubros ORDER BY CONCEPTO")
            lista_rubros = [f"{row[0]} - {row[1]}" for row in cursor.fetchall()]
        except:
            lista_rubros = []

        with st.form("form_alta_art", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                rubro_sel = st.selectbox("Rubro", lista_rubros) if lista_rubros else st.text_input("Rubro (Código)")
                subrubro = st.text_input("Subrubro (Código Opcional)")
                codigo = st.text_input("Código Interno del Artículo *")
            with col2:
                descrip = st.text_input("Descripción *")
                unidad = st.text_input("Unidad (Ej: KG, UN, LT)")
                precio = st.number_input("Precio Base", min_value=0.0, step=100.0, format="%.2f")
                
            st.info("💡 Nota: El sistema original aplica un 15% de descuento sobre este precio en algunas pantallas contables.")
            
            submit_alta = st.form_submit_button("💾 Guardar Artículo", type="primary")

        if submit_alta:
            if not codigo or not descrip:
                st.error("⚠️ El Código y la Descripción son obligatorios.")
            else:
                try:
                    id_rubro = rubro_sel.split(" - ")[0] if " - " in rubro_sel else rubro_sel
                    
                    cursor.execute("SELECT 1 FROM articulo WHERE CODIGO = ?", (codigo.upper(),))
                    if cursor.fetchone():
                        st.warning(f"⚠️ El código '{codigo}' ya existe en la base de datos.")
                    else:
                        cursor.execute("""
                            INSERT INTO articulo (CODIGO, UNIDAD, DESCRIP, PRECIO)
                            VALUES (?, ?, ?, ?)
                        """, (codigo.upper(), unidad.upper(), descrip.upper(), precio))
                        
                        try:
                            cursor.execute("""
                                INSERT INTO COMP_ART (RUBRO, CODIGO, UNIDAD, DESCRIP, PRECIO)
                                VALUES (?, ?, ?, ?, ?)
                            """, (id_rubro, codigo.upper(), unidad.upper(), descrip.upper(), precio))
                        except Exception:
                            pass 
                            
                        con.commit()
                        st.success(f"✔️ Artículo '{descrip}' guardado con éxito.")
                except Exception as e:
                    st.error(f"❌ Error al guardar: {e}")

    with tab_lista:
        st.subheader("Buscador de Artículos")
        try:
            df_arts = pd.read_sql_query("SELECT CODIGO, DESCRIP, PRECIO, UNIDAD FROM articulo ORDER BY DESCRIP", con)
            
            df_arts['PRECIO CON DTO (15%)'] = (df_arts['PRECIO'] * 0.85).round(2)
            
            st.dataframe(
                df_arts,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "PRECIO": st.column_config.NumberColumn("Precio Base", format="$ %.2f"),
                    "PRECIO CON DTO (15%)": st.column_config.NumberColumn("Precio c/ Dto", format="$ %.2f")
                }
            )
        except Exception as e:
            st.warning(f"No se pudo cargar la tabla de artículos: {e}")
            
    con.close()


                                                                                
def _pantalla_pagos():
    st.title("💸 Proveedores › Registro de Pagos (Cancelaciones)")
    st.markdown("Armado de órdenes de pago para cancelar facturas de compra.")
    con = sqlite3.connect(get_db_path())

                                                   
    try:
        df_prov = pd.read_sql_query("SELECT cod_proveedor, nombre FROM v_resumen_proveedores ORDER BY nombre", con)
        lista_proveedores = [f"{row['cod_proveedor']} - {row['nombre']}" for _, row in df_prov.iterrows()]
    except:
        lista_proveedores = []

    proveedor_sel = st.selectbox("1️⃣ Seleccionar Proveedor:", lista_proveedores)

    if proveedor_sel:
        cod_prov = proveedor_sel.split(" - ")[0]

                                                                                    
        cursor = con.cursor()
        cursor.execute("SELECT SUM(DEBE) - SUM(HABER) FROM proveedores_ctacte WHERE NUMERO = ?", (cod_prov,))
        saldo_actual = cursor.fetchone()[0] or 0.0

        st.info(f"💰 Saldo deudor actual: **$ {saldo_actual:,.2f}**")

        if saldo_actual > 0:
            st.markdown("---")
            st.subheader("2️⃣ Registrar Cancelación")
            
            with st.form("form_nuevo_pago", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    fecha_pago = st.date_input("Fecha de Pago", datetime.date.today())
                    medio_pago = st.selectbox("Medio de Pago", [
                        "Efectivo", 
                        "Cheque de Terceros (Cartera)", 
                        "Cheque Propio", 
                        "Transferencia Bancaria"
                    ])
                    nro_referencia = st.text_input("Nº Referencia / Cheque / Transferencia")
                
                with col2:
                    importe_pago = st.number_input("Importe a Pagar ($)", min_value=0.01, value=float(saldo_actual))
                    detalle = st.text_input("Detalle Libre (Opcional)", placeholder="Ej: Pago total Fra 001-0023")

                st.warning("⚡ Al guardar, este importe ingresará como HABER en la cuenta corriente, disminuyendo el saldo.")
                btn_pagar = st.form_submit_button("✅ Procesar Pago", type="primary")

            if btn_pagar:
                fecha_str = fecha_pago.strftime("%Y-%m-%d")
                concepto = f"Pago {medio_pago} {nro_referencia}".strip()
                if detalle:
                    concepto += f" | {detalle}"

                try:
                    cursor.execute("""
                        INSERT INTO proveedores_ctacte (NUMERO, FECHA, OPERACION, DEBE, HABER, SALDO)
                        VALUES (?, ?, ?, 0, ?, 0)
                    """, (cod_prov, fecha_str, concepto, importe_pago))
                    
                    con.commit()
                    st.success(f"✔️ Pago de $ {importe_pago:,.2f} registrado exitosamente para {proveedor_sel}.")
                    st.rerun()
                except Exception as e:
                    con.rollback()
                    st.error(f"❌ Error al registrar el pago: {e}")
        else:
            st.success("Este proveedor no tiene saldo deudor pendiente.")

    con.close()
                                                                                
def _pantalla_bancos():
    st.title("🏦 Bancos")
    st.markdown("Gestión de entidades bancarias (Alta y Modificación)")
    con = sqlite3.connect(get_db_path())
    
    tab_alta, tab_lista = st.tabs(["➕ Nuevo Banco", "📋 Listado de Bancos"])

                              
    with tab_alta:
        st.subheader("Ingresar Nuevo Banco")
        with st.form("form_alta_banco", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nombre_banco = st.text_input("Nombre del Banco *", max_chars=40)
            with col2:
                cuit_banco = st.text_input("CUIT del Banco", max_chars=11, help="Ingresar solo números, sin guiones")
            
            submit_alta = st.form_submit_button("💾 Guardar Banco", type="primary")

        if submit_alta:
            if not nombre_banco.strip():
                st.error("⚠️ El Nombre del Banco es obligatorio.")
            else:
                try:
                    cursor = con.cursor()
                                                               
                    cursor.execute("SELECT 1 FROM bancos WHERE NOMBRE = ?", (nombre_banco.upper(),))
                    if cursor.fetchone():
                        st.warning("⚠️ Ya existe un banco registrado con ese nombre.")
                    else:
                                                                     
                        cursor.execute("""
                            INSERT INTO bancos (NOMBRE, CUIT)
                            VALUES (?, ?)
                        """, (nombre_banco.upper(), cuit_banco.strip()))
                        
                        con.commit()
                        st.success(f"✔️ Banco '{nombre_banco}' guardado con éxito.")
                except Exception as e:
                    st.error(f"❌ Error al guardar en la base de datos: {e}")

                                  
    with tab_lista:
        st.subheader("Bancos Registrados")
        try:
                                                       
            df_bancos = pd.read_sql_query("SELECT NOMBRE, CUIT FROM bancos ORDER BY NOMBRE", con)
            
            st.dataframe(
                df_bancos.rename(columns={"NOMBRE": "Entidad Bancaria", "CUIT": "CUIT"}),
                use_container_width=True,
                hide_index=True
            )
        except Exception as e:
            st.error(f"Error al cargar la tabla de bancos: {e}")

    con.close()
                                                                               
def _pantalla_retenciones(tipo_retencion):
    st.title(f"🏛️ Retención de {tipo_retencion}")
    st.markdown(f"Emisión de certificados de retención de {tipo_retencion} para proveedores.")
    con = sqlite3.connect(get_db_path())

    try:
        df_prov = pd.read_sql_query("SELECT cod_proveedor, nombre FROM v_resumen_proveedores ORDER BY nombre", con)
        lista_proveedores = [f"{row['cod_proveedor']} - {row['nombre']}" for _, row in df_prov.iterrows()]
    except:
        lista_proveedores = []

    proveedor_sel = st.selectbox("1️⃣ Seleccionar Proveedor:", lista_proveedores)

    if proveedor_sel:
        cod_prov = proveedor_sel.split(" - ")[0]

        try:
            df_fac = pd.read_sql_query(
                "SELECT NUMERO, FECHA, NETO, TOTAL_A FROM proveedores_facturas WHERE CLIENTE = ? ORDER BY FECHA DESC LIMIT 20", 
                con, params=[cod_prov]
            )
        except:
            df_fac = pd.DataFrame()

        if not df_fac.empty:
            st.markdown("---")
            st.subheader("2️⃣ Base de Cálculo")
            
            facturas_lista = [f"{row['NUMERO']} | Fecha: {row['FECHA']} | Neto: ${row['NETO']:,.2f} | Total: ${row['TOTAL_A']:,.2f}" for _, row in df_fac.iterrows()]
            facturas_sel = st.multiselect("Seleccionar comprobantes a retener:", facturas_lista)

            if facturas_sel:
                neto_total = sum([float(f.split("Neto: $")[1].split(" |")[0].replace(",", "")) for f in facturas_sel])
                
                st.info(f"📊 Base Imponible Neta Seleccionada: **$ {neto_total:,.2f}**")
                
                with st.form("form_retencion", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        fecha_ret = st.date_input("Fecha del Certificado", datetime.date.today())
                        nro_cert = st.text_input("Nº de Certificado (Ej: 0001-000456)")
                    with col2:
                        alicuota = st.number_input("Alícuota Aplicable (%)", min_value=0.00, value=2.00, step=0.50)
                        min_no_imponible = st.number_input("Mínimo No Imponible ($)", min_value=0.00, value=0.00)
                    
                    base_sujeta = max(0, neto_total - min_no_imponible)
                    retencion_calculada = base_sujeta * (alicuota / 100)
                    
                    st.metric("Importe a Retener Calculado", f"$ {retencion_calculada:,.2f}")
                    importe_final = st.number_input("Importe Final a Retener ($)", min_value=0.00, value=float(retencion_calculada))
                    
                    submit_ret = st.form_submit_button("💾 Guardar y Emitir Certificado", type="primary")

                if submit_ret:
                    if not nro_cert:
                        st.error("⚠️ El número de certificado es obligatorio.")
                    else:
                        fecha_str = fecha_ret.strftime("%Y-%m-%d")
                        
                                                             
                        if tipo_retencion == "Ganancias":
                            tabla_destino = "contabil__rete_dgr"
                        elif tipo_retencion == "I.B.":
                            tabla_destino = "reten_ib"
                        else:
                            tabla_destino = "contabil__rete_iva"
                        
                        try:
                            cursor = con.cursor()
                            cursor.execute(f"""
                                INSERT INTO {tabla_destino} (NUMERO, FECHA, PROVEEDOR, NETO, ALICUOTA, RETENCION)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (nro_cert, fecha_str, cod_prov, neto_total, alicuota, importe_final))
                            
                            concepto = f"Retención {tipo_retencion} Cert. {nro_cert}"
                            cursor.execute("""
                                INSERT INTO proveedores_ctacte (NUMERO, FECHA, OPERACION, DEBE, HABER, SALDO)
                                VALUES (?, ?, ?, 0, ?, 0)
                            """, (cod_prov, fecha_str, concepto, importe_final))
                            
                            con.commit()
                            st.success(f"✔️ Certificado {nro_cert} guardado. La retención de $ {importe_final:,.2f} se descontó de la cuenta corriente.")
                        except Exception as e:
                            con.rollback()
                            st.error(f"❌ Error al registrar: {e}")
        else:
            st.warning("Este proveedor no tiene facturas recientes cargadas.")

    con.close()


                                                                                
def _pantalla_libro_retenciones():
    st.title("🖨️ Libros de Retenciones")
    st.markdown("Visor y reporte de retenciones emitidas por período.")
    con = sqlite3.connect(get_db_path())

    col1, col2 = st.columns(2)
    with col1:
        tipo_libro = st.selectbox("Tipo de Retención", ["Ganancias", "Ingresos Brutos (I.B.)", "IVA"])
    with col2:
        periodo = st.text_input("Período (YYYY-MM) - Dejar vacío para ver todo", placeholder="Ej: 2026-06")

                                         
    if tipo_libro == "Ganancias":
        tabla = "contabil__rete_dgr" 
    elif tipo_libro == "Ingresos Brutos (I.B.)":
        tabla = "reten_ib"
    else:
        tabla = "contabil__rete_iva"

    query = f"SELECT * FROM {tabla} WHERE 1=1"
    params = []

    if periodo:
        query += " AND FECHA LIKE ?"
        params.append(f"{periodo}%")

    query += " ORDER BY FECHA DESC"

    try:
        df_libros = pd.read_sql_query(query, con, params=params)
        
        if df_libros.empty:
            st.warning(f"No se encontraron retenciones de {tipo_libro} para los filtros aplicados.")
        else:
            m1, m2 = st.columns(2)
            m1.metric("Cantidad de Certificados", f"{len(df_libros)}")
            
            col_importe = next((col for col in ["RETENCION", "IMPORTE", "TOTAL"] if col in df_libros.columns), None)
            
            if col_importe:
                m2.metric("Total Retenido del Período", f"$ {df_libros[col_importe].sum():,.2f}")
            
            st.markdown("---")
            st.dataframe(
                df_libros, 
                use_container_width=True, 
                hide_index=True
            )
            
    except Exception as e:
        st.error(f"Error al leer el libro de retenciones ({tabla}): {e}")
        
    con.close()