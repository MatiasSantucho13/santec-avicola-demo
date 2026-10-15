"""
modulo_clientes.py
Santec Software — Módulo Clientes Completo
"""
import sqlite3
import pandas as pd
import streamlit as st

from demo_db import get_db_path

def render_clientes(accion: str):
    """Enrutador de pantallas del módulo clientes."""
    if accion == "Listados clientes":
        _pantalla_listado_clientes()
    elif accion == "Informe Cta. Cte.":
        _pantalla_informe_ctacte()
    elif accion == "Saldos":
        _pantalla_saldos_clientes()
    elif accion == "Altas/Modificaciones":
        _pantalla_abm_clientes()
    elif accion == "Pagos":
        _pantalla_pagos()
    elif accion == "Cheques":
        _pantalla_cheques()
    elif accion == "Recibos":
        _pantalla_recibos()
    elif accion == "Códigos postales":
        _pantalla_codigos_postales()
    elif accion == "Venta por provincias":                                    
        _pantalla_ventas_provincia()                                          
    elif accion == "Libro Percepción IB":                                     
        _pantalla_libro_ib()                                                  
    else:
        st.title(f"👥 Clientes › {accion}")
        st.info(f"La pantalla **{accion}** está en desarrollo.")

                                                                                
def _pantalla_listado_clientes():
    st.markdown("### Visor del Padrón de Clientes Migrados")
    con = sqlite3.connect(get_db_path())
    try:
        df_clientes = pd.read_sql_query("SELECT * FROM clientes", con)
        
        busqueda = st.text_input("🔍 Filtrar por nombre, CUIT o localidad:")
        if busqueda:
            mask = df_clientes.astype(str).apply(lambda x: x.str.contains(busqueda, case=False, na=False, regex=False)).any(axis=1)
            df_mostrar = df_clientes[mask]
        else:
            df_mostrar = df_clientes
            
        st.success(f"Se encontraron {len(df_mostrar)} registros activos en la base de datos.")
        
                                                                           
        col_cuit = "cuit" if "cuit" in df_mostrar.columns else "cuil" if "cuil" in df_mostrar.columns else None
        
        columnas_clave = ["numero", "nombre", col_cuit, "telefono", "relacion"] 
        cols_existentes = [col for col in columnas_clave if col and col in df_mostrar.columns]
        df_limpio = df_mostrar[cols_existentes].copy()
        
        nombres_amigables = {
            "numero": "Nº Cliente", "nombre": "Razón Social", 
            col_cuit: "CUIT / CUIL", "telefono": "Teléfono", "relacion": "Condición Comercial"
        }
        df_limpio.rename(columns={k: v for k, v in nombres_amigables.items() if k in df_limpio.columns}, inplace=True)
        
        st.dataframe(df_limpio, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"No se pudo leer la tabla de clientes: {e}")
    finally:
        con.close()


                                                                                
def _pantalla_informe_ctacte():
    st.markdown("### Extracto de Cuenta Corriente Histórica")
    con = sqlite3.connect(get_db_path())
    
    try:
        df_c = pd.read_sql_query("SELECT numero, nombre FROM clientes ORDER BY nombre", con)
        lista_clientes = [f"{row['numero']} - {row['nombre']}" for _, row in df_c.iterrows()]
    except Exception:
        lista_clientes = []

    cliente_sel = st.selectbox("🔍 Seleccionar Cliente:", lista_clientes)
    
    if cliente_sel:
        id_cliente = cliente_sel.split(" - ")[0]
        
        query = "SELECT FECHA, OPER_NRO, OPERACION, DEBE, HABER, SALDO FROM ctacte WHERE NUMERO = ? ORDER BY FECHA DESC"
        try:
            df_movs = pd.read_sql_query(query, con, params=[id_cliente])
            
            if df_movs.empty:
                st.warning("Este cliente no registra movimientos históricos en su cuenta corriente.")
            else:
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Facturado (Debe)", f"$ {df_movs['DEBE'].sum():,.2f}")
                m2.metric("Total Cobrado (Haber)", f"$ {df_movs['HABER'].sum():,.2f}")
                
                saldo_calculado = df_movs['DEBE'].sum() - df_movs['HABER'].sum()
                m3.metric("Saldo Neto Acumulado", f"$ {saldo_calculado:,.2f}", 
                          delta="Deuda" if saldo_calculado > 0 else "Saldo a Favor",
                          delta_color="inverse" if saldo_calculado > 0 else "normal")
                
                st.markdown("---")
                st.dataframe(
                    df_movs.rename(columns={
                        "FECHA": "Fecha", "OPER_NRO": "Nº Op", "OPERACION": "Detalle Operación",
                        "DEBE": "Debe (+)", "HABER": "Haber (-)", "SALDO": "Saldo Registrado"
                    }),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Debe (+)": st.column_config.NumberColumn(format="$ %.2f"),
                        "Haber (-)": st.column_config.NumberColumn(format="$ %.2f"),
                        "Saldo Registrado": st.column_config.NumberColumn(format="$ %.2f")
                    }
                )
        except Exception as e:
            st.error(f"Error al consultar los movimientos: {e}")
            
    con.close()


                                                                                
def _pantalla_saldos_clientes():
    st.markdown("### Resumen General de Saldos de Clientes")
    con = sqlite3.connect(get_db_path())
    
    query = """
        SELECT NUMERO AS cod_cliente, MAX(FECHA) AS ultima_op,
               ROUND(SUM(DEBE), 2) AS total_debe,
               ROUND(SUM(HABER), 2) AS total_haber,
               ROUND(SUM(DEBE) - SUM(HABER), 2) AS saldo_actual
        FROM ctacte
        GROUP BY NUMERO 
        HAVING saldo_actual != 0
        ORDER BY saldo_actual DESC
    """
    try:
        df_saldos = pd.read_sql_query(query, con)
        df_nombres = pd.read_sql_query("SELECT numero AS cod_cliente, nombre FROM clientes", con)
        
        df_consolidado = pd.merge(df_saldos, df_nombres, on="cod_cliente", how="left")
        
        columnas = ["cod_cliente", "nombre", "ultima_op", "total_debe", "total_haber", "saldo_actual"]
        df_consolidado = df_consolidado[[c for c in columnas if c in df_consolidado.columns]]
        
        st.dataframe(
            df_consolidado.rename(columns={
                "cod_cliente": "Código", "nombre": "Razón Social", "ultima_op": "Última Actividad",
                "total_debe": "Histórico Debe", "total_haber": "Histórico Haber", "saldo_actual": "Saldo Pendiente"
            }),
            use_container_width=True, hide_index=True,
            column_config={
                "Histórico Debe": st.column_config.NumberColumn(format="$ %.2f"),
                "Histórico Haber": st.column_config.NumberColumn(format="$ %.2f"),
                "Saldo Pendiente": st.column_config.NumberColumn(format="$ %.2f")
            }
        )
    except Exception as e:
        st.error(f"Error al procesar saldos: {e}")
    finally:
        con.close()


                                                                                
def _pantalla_abm_clientes():
    st.title("📇 Clientes › Altas y Modificaciones")
    st.markdown("Gestión del padrón maestro de clientes.")
    
    con = sqlite3.connect(get_db_path())
    tab_alta, tab_mod = st.tabs(["➕ Alta de Cliente", "✏️ Modificar Existente"])

    opciones_tipo = {"Inscripto": "I", "No inscripto": "NI", "Exento": "E", "Cons. Final": "CF", "Monotributo": "MT"}
    opciones_imputa = {"Nada": " ", "Producción": "P", "Comercialización": "C", "Administración": "A"}

                                
    with tab_alta:
        st.subheader("Ingresar Nuevo Cliente")
        with st.form("form_alta_cliente", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                nombre = st.text_input("Razón Social / Nombre *", max_chars=40)
                cuit = st.text_input("C.U.I.T.", help="Formato numérico sin guiones", max_chars=11)
                telefono = st.text_input("Teléfono")
                actividad = st.text_input("Actividad Comercial")
            with c2:
                direccion = st.text_input("Dirección")
                localidad = st.text_input("Localidad")
                codpostal = st.text_input("C.P.", max_chars=8)
                provincia = st.text_input("Provincia")
            with c3:
                tipo_iva = st.selectbox("Condición frente al IVA", list(opciones_tipo.keys()))
                imputacion = st.selectbox("Imputación Contable", list(opciones_imputa.keys()))
                ing_brutos = st.text_input("Nº Ingresos Brutos")
                
                sc1, sc2 = st.columns(2)
                with sc1:
                    cm = st.text_input("C.M.")
                    tipo_polla = st.selectbox("Tipo Ave", ["0 - Parrillero", "1 - Ponedora"])
                with sc2:
                    pibrusfe = st.number_input("Perc. IB Sta.Fe", min_value=0.0, step=0.1)
                    relacion = st.text_input("Relación")

            st.markdown("*Campos obligatorios")
            submit_alta = st.form_submit_button("💾 Guardar Nuevo Cliente", type="primary")

        if submit_alta:
            if not nombre.strip():
                st.error("⚠️ La Razón Social es obligatoria.")
            else:
                try:
                    cursor = con.cursor()
                    cursor.execute("SELECT MAX(CAST(NUMERO AS INTEGER)) FROM clientes")
                    max_num = cursor.fetchone()[0]
                    nuevo_numero = str(1 if max_num is None else max_num + 1).zfill(5)

                    val_tipo = opciones_tipo[tipo_iva]
                    val_imputa = opciones_imputa[imputacion]
                    val_polla = tipo_polla.split(" - ")[0]
                    
                                                                                               
                    cursor.execute("PRAGMA table_info(clientes)")
                    columnas_db = [col[1].lower() for col in cursor.fetchall()]
                    col_cuit = "cuit" if "cuit" in columnas_db else "cuil"

                    query_insert = f"""
                        INSERT INTO clientes 
                        (NUMERO, NOMBRE, DIRECCION, LOCALIDAD, CODPOSTAL, PROVINCIA, {col_cuit}, TELEFONO, TIPO, IMPUTA, ING_BRUTOS, CM, PIBRUSFE, RELACION, ACTIVIDAD, TIPO_POLLA, ACTIVO)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(query_insert, (nuevo_numero, nombre.upper(), direccion.upper(), localidad.upper(), codpostal, provincia.upper(), cuit, telefono, val_tipo, val_imputa, ing_brutos, cm, pibrusfe, relacion, actividad.upper(), val_polla, "S"))
                    
                    con.commit()
                    st.success(f"✔️ ¡Cliente '{nombre}' guardado con el Código Nº {nuevo_numero}!")
                except Exception as e:
                    con.rollback()
                    st.error(f"❌ Error al guardar en la base: {e}")

                             
    with tab_mod:
        st.subheader("Editar Cliente Existente")
        
        try:
            df_clie = pd.read_sql_query("SELECT NUMERO, NOMBRE FROM clientes ORDER BY NOMBRE", con)
            lista_edicion = [f"{row['NUMERO']} - {row['NOMBRE']}" for _, row in df_clie.iterrows()]
        except Exception:
            lista_edicion = []

        if lista_edicion:
            clie_a_editar = st.selectbox("🔍 Buscar cliente a modificar:", lista_edicion)
            
            if clie_a_editar:
                cod_edit = clie_a_editar.split(" - ")[0]
                
                cursor = con.cursor()
                cursor.execute("PRAGMA table_info(clientes)")
                columnas_db = [col[1].lower() for col in cursor.fetchall()]
                col_cuit = "cuit" if "cuit" in columnas_db else "cuil"

                cursor.execute(f"""
                    SELECT NOMBRE, DIRECCION, LOCALIDAD, CODPOSTAL, PROVINCIA, {col_cuit}, TELEFONO, ACTIVIDAD
                    FROM clientes WHERE NUMERO = ?
                """, (cod_edit,))
                datos = cursor.fetchone()
                
                if datos:
                    with st.form("form_mod_cliente"):
                        m1, m2 = st.columns(2)
                        with m1:
                            mod_nombre = st.text_input("Razón Social", value=datos[0] or "")
                            mod_cuit = st.text_input("CUIT/CUIL", value=datos[5] or "")
                            mod_telefono = st.text_input("Teléfono", value=datos[6] or "")
                            mod_actividad = st.text_input("Actividad", value=datos[7] or "")
                        with m2:
                            mod_direccion = st.text_input("Dirección", value=datos[1] or "")
                            mod_localidad = st.text_input("Localidad", value=datos[2] or "")
                            mod_codpostal = st.text_input("C.P.", value=datos[3] or "")
                            mod_provincia = st.text_input("Provincia", value=datos[4] or "")

                        submit_mod = st.form_submit_button("🔄 Actualizar Datos", type="primary")

                    if submit_mod:
                        try:
                            cursor.execute(f"""
                                UPDATE clientes 
                                SET NOMBRE=?, DIRECCION=?, LOCALIDAD=?, CODPOSTAL=?, PROVINCIA=?, {col_cuit}=?, TELEFONO=?, ACTIVIDAD=?
                                WHERE NUMERO=?
                            """, (mod_nombre.upper(), mod_direccion.upper(), mod_localidad.upper(), mod_codpostal, mod_provincia.upper(), mod_cuit, mod_telefono, mod_actividad.upper(), cod_edit))
                            
                            con.commit()
                            st.success(f"✔️ Datos del cliente {cod_edit} actualizados correctamente.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al actualizar: {e}")
        else:
            st.warning("No hay clientes en la base de datos para modificar.")

    con.close()
                                                                                
def _pantalla_pagos():
    st.title("💸 Ingreso de Pagos y Cheques")
    st.markdown("Registro de cobranzas e imputación directa en cuenta corriente.")
    
    con = sqlite3.connect(get_db_path())
    
                             
    try:
        df_clientes = pd.read_sql_query("SELECT NUMERO, NOMBRE FROM clientes ORDER BY NOMBRE", con)
        lista_clientes = [f"{row['NUMERO']} - {row['NOMBRE']}" for _, row in df_clientes.iterrows()]
    except Exception:
        lista_clientes = []
        
                            
    try:
        df_bancos = pd.read_sql_query("SELECT NOMBRE FROM bancos ORDER BY NOMBRE", con)
        lista_bancos = df_bancos['NOMBRE'].tolist()
    except Exception:
        lista_bancos = []

    cliente_sel = st.selectbox("👤 1. Seleccionar Cliente:", lista_clientes)
    
    if cliente_sel:
        cod_cliente = cliente_sel.split(" - ")[0]
        
                                                                   
        try:
            cursor = con.cursor()
            cursor.execute("SELECT SUM(DEBE) - SUM(HABER) FROM ctacte WHERE NUMERO = ?", (cod_cliente,))
            saldo_actual = cursor.fetchone()[0] or 0.0
            
            if saldo_actual > 0:
                st.warning(f"**Deuda actual del cliente:** $ {saldo_actual:,.2f}")
            else:
                st.success(f"**Saldo a favor del cliente:** $ {abs(saldo_actual):,.2f}")
        except:
            pass

        st.markdown("---")
        tipo_pago = st.radio("💵 2. Método de Pago:", ["Efectivo", "Cheque", "Varios Cheques"], horizontal=True)
        
        with st.form("form_pagos", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                fecha_pago = st.date_input("Fecha de Pago")
                importe = st.number_input("Importe Total a Imputar ($)", min_value=0.01, step=1000.0)
                
            with col2:
                if tipo_pago == "Cheque":
                    banco = st.selectbox("Banco del Cheque", lista_bancos)
                    nro_cheque = st.text_input("Número de Cheque")
                    fecha_vto = st.date_input("Fecha de Vencimiento")
                else:
                    st.write("")                                      
                    
            submit_pago = st.form_submit_button("💾 Imputar Pago en Cta. Cte.", type="primary")
            
        if submit_pago:
            if tipo_pago == "Cheque" and not nro_cheque.strip():
                st.error("⚠️ Para pagos con cheque, el Número de Cheque es obligatorio.")
            else:
                try:
                    fecha_str = fecha_pago.strftime("%Y-%m-%d")
                    cursor = con.cursor()
                    
                                                      
                    if tipo_pago == "Efectivo":
                        txt_pago = "Efectivo"
                    elif tipo_pago == "Varios Cheques":
                        txt_pago = "Varios Cheques"
                    else:
                        txt_pago = f"Cheque N° {nro_cheque}"
                        fecha_vto_str = fecha_vto.strftime("%Y-%m-%d")
                        
                                                                                   
                        cursor.execute("""
                            INSERT INTO cheques (NUMEROCLIE, NUMERO, BANCO, FECHA, VTO, IMPORTE)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (cod_cliente, nro_cheque, banco, fecha_str, fecha_vto_str, importe))
                    
                    detalle_operacion = f"Pago {txt_pago}"
                    
                                                                                  
                                                                                     
                    cursor.execute("""
                        INSERT INTO ctacte (NUMERO, FECHA, OPERACION, DEBE, HABER, SALDO)
                        VALUES (?, ?, ?, 0, ?, 0)
                    """, (cod_cliente, fecha_str, detalle_operacion, importe))
                    
                    con.commit()
                    st.success(f"✔️ ¡Pago de $ {importe:,.2f} registrado exitosamente! ({detalle_operacion})")
                    
                except Exception as e:
                    con.rollback()
                    st.error(f"❌ Error al procesar el pago: {e}")
                    st.info("Nota técnica: Verificá que la tabla 'cheques' exista con esas columnas exactas en SQLite.")
                
    con.close()    
                                                                                
def _pantalla_cheques():
    st.title("🏦 Gestión de Cheques de Terceros")
    st.markdown("Administración de la cartera de cheques, depósitos y rechazos.")
    
    con = sqlite3.connect(get_db_path())
    cursor = con.cursor()
    
                                                                             
                                                                                                                  
    try:
        cursor.execute("ALTER TABLE cheques ADD COLUMN ESTADO TEXT DEFAULT 'CARTERA'")
        con.commit()
                                                                  
        try:
            cursor.execute("UPDATE cheques SET ESTADO = 'DEPOSITADO' WHERE COBRADO = 1 OR COBRADO = 'T' OR COBRADO = 'S'")
            con.commit()
        except:
            pass
    except:
        pass                       

                                                               
    tab_cartera, tab_depositar, tab_rechazados = st.tabs([
        "📁 Cheques en Cartera", 
        "🏦 Mandar a Depósito", 
        "❌ Cheques Rechazados"
    ])

                                         
    with tab_cartera:
        st.subheader("Cheques Físicos Disponibles")
        try:
            df_cartera = pd.read_sql_query("SELECT NUMEROCLIE, BANCO, NUMERO, FECHA, VTO, IMPORTE FROM cheques WHERE ESTADO = 'CARTERA' OR ESTADO IS NULL ORDER BY VTO ASC", con)
            if df_cartera.empty:
                st.info("No hay cheques en cartera en este momento.")
            else:
                st.metric("Total en Cartera", f"$ {df_cartera['IMPORTE'].sum():,.2f}")
                st.dataframe(df_cartera, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Error al leer la cartera: {e}")

                                  
    with tab_depositar:
        st.subheader("Depositar Cheques")
        st.markdown("Seleccioná los cheques que vas a llevar al banco:")
        
        try:
            df_deposito = pd.read_sql_query("SELECT id, NUMERO, BANCO, VTO, IMPORTE FROM cheques WHERE ESTADO = 'CARTERA' OR ESTADO IS NULL ORDER BY VTO ASC", con)
            
            if not df_deposito.empty:
                lista_cheques = [f"ID:{row['id']} | {row['BANCO']} - Nº {row['NUMERO']} | Vence: {row['VTO']} | $ {row['IMPORTE']:,.2f}" for _, row in df_deposito.iterrows()]
                
                con_form = st.form("form_deposito", clear_on_submit=True)
                cheques_a_depositar = con_form.multiselect("Cheques a incluir en la boleta de depósito:", lista_cheques)
                
                if cheques_a_depositar:
                    total_deposito = sum([float(c.split("$ ")[1].replace(",", "")) for c in cheques_a_depositar])
                    con_form.info(f"Total de la boleta de depósito: **$ {total_deposito:,.2f}**")
                
                submit_deposito = con_form.form_submit_button("🏦 Marcar como Depositados", type="primary")
                
                if submit_deposito and cheques_a_depositar:
                    ids_depositar = [c.split(" |")[0].replace("ID:", "") for c in cheques_a_depositar]
                    
                                                                    
                    placeholders = ','.join('?' for _ in ids_depositar)
                    cursor.execute(f"UPDATE cheques SET ESTADO = 'DEPOSITADO' WHERE id IN ({placeholders})", ids_depositar)
                    con.commit()
                    
                    st.success(f"✔️ {len(ids_depositar)} cheques marcados como depositados exitosamente.")
                    st.rerun()
            else:
                st.info("No hay cheques disponibles para depositar.")
        except Exception as e:
            st.warning("⚠️ Nota técnica: La tabla 'cheques' necesita una columna autoincremental 'id' (Primary Key) para que esta selección funcione perfecto.")

                                                                       
    with tab_rechazados:
        st.subheader("Gestión de Rechazos")
        st.write("Si el banco rebotó un cheque depositado, buscalo acá para devolverlo a cartera o marcarlo como rechazado.")
        
        try:
            df_depositados = pd.read_sql_query("SELECT id, NUMERO, BANCO, VTO, IMPORTE FROM cheques WHERE ESTADO = 'DEPOSITADO' ORDER BY VTO DESC LIMIT 50", con)
            
            if not df_depositados.empty:
                lista_dep = [f"ID:{row['id']} | {row['BANCO']} - Nº {row['NUMERO']} | $ {row['IMPORTE']:,.2f}" for _, row in df_depositados.iterrows()]
                
                with st.form("form_rechazo"):
                    cheque_problema = st.selectbox("Seleccionar cheque depositado:", [""] + lista_dep)
                    accion_rebote = st.radio("Acción a tomar:", ["Volver a Cartera (Error salvable)", "Marcar como Rechazado (Generar deuda)"])
                    
                    submit_rebote = st.form_submit_button("⚠️ Aplicar Estado")
                    
                    if submit_rebote and cheque_problema:
                        id_rebote = cheque_problema.split(" |")[0].replace("ID:", "")
                        nuevo_estado = "CARTERA" if "Volver" in accion_rebote else "RECHAZADO"
                        
                        cursor.execute("UPDATE cheques SET ESTADO = ? WHERE id = ?", (nuevo_estado, id_rebote))
                        
                                                                                                                                              
                        con.commit()
                        st.success(f"El cheque se actualizó al estado: {nuevo_estado}")
                        st.rerun()
            else:
                st.info("No hay cheques depositados recientemente.")
        except:
            pass

    con.close()    
                                                                                
def _pantalla_recibos():
    st.title("🧾 Centro de Recibos")
    st.markdown("Emisión de recibos oficiales, imputación de facturas y visualización histórica.")
    
    con = sqlite3.connect(get_db_path())
    cursor = con.cursor()
    
                                                                     
    try:
        cursor.execute("SELECT MAX(CAST(numero AS INTEGER)) FROM recibos")
        max_recibo = cursor.fetchone()[0]
        prox_recibo = str(1 if max_recibo is None else max_recibo + 1).zfill(8)
    except:
        prox_recibo = "00000001"

                             
    try:
        df_clientes = pd.read_sql_query("SELECT NUMERO, NOMBRE, CUIT FROM clientes ORDER BY NOMBRE", con)
        lista_clientes = [f"{row['NUMERO']} - {row['NOMBRE']} (CUIT: {row['CUIT']})" for _, row in df_clientes.iterrows()]
    except Exception:
        lista_clientes = []

    tab_nuevo, tab_historial = st.tabs(["➕ Emitir Nuevo Recibo", "🔍 Buscar Historial"])

                                            
    with tab_nuevo:
        st.subheader("Carga de Cobranza")
        
        cliente_sel = st.selectbox("1. Cliente a cobrar:", [""] + lista_clientes)
        
        if cliente_sel:
            cod_cliente = cliente_sel.split(" - ")[0]
            
                                                 
            try:
                                                                                             
                df_facturas = pd.read_sql_query("""
                    SELECT TIPO, PREFIJO, NUMERO, FECHA, TOTAL, PAGO, (TOTAL - PAGO) AS SALDO_PENDIENTE 
                    FROM factgral 
                    WHERE CLIENTE = ? AND (TOTAL - PAGO) > 0
                """, con, params=[cod_cliente])
            except:
                df_facturas = pd.DataFrame()

            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"**Nº Recibo a generar:** {prox_recibo}")
                fecha_recibo = st.date_input("Fecha de Emisión")
                concepto_recibo = st.text_input("Concepto General", value="Cobranza de facturas")
                
            with col2:
                                                                       
                st.write("Valores / Retenciones Adicionales:")
                efectivo = st.number_input("Efectivo / Transferencia ($)", min_value=0.0, step=1000.0)
                ret_ib = st.number_input("Retención I.B. ($)", min_value=0.0, step=100.0)
                ret_iva = st.number_input("Retención I.V.A. ($)", min_value=0.0, step=100.0)
                descuento = st.number_input("Descuentos varios ($)", min_value=0.0, step=100.0)
                
                total_valores = efectivo + ret_ib + ret_iva + descuento
                st.success(f"**Total a imputar: $ {total_valores:,.2f}**")

            st.markdown("---")
            st.write("**2. Imputar a Facturas Pendientes:**")
            
            facturas_imputadas = []
            if not df_facturas.empty:
                st.write("El cliente registra la siguiente deuda comprobable:")
                                                         
                lista_fac = [f"{row['TIPO']} {row['PREFIJO']}-{row['NUMERO']} | Vence: {row['FECHA']} | Saldo: $ {row['SALDO_PENDIENTE']:,.2f}" for _, row in df_facturas.iterrows()]
                facturas_imputadas = st.multiselect("Seleccionar facturas a cancelar con este recibo:", lista_fac)
            else:
                st.success("El cliente no tiene facturas pendientes de pago en el sistema.")
                st.info("Podés generar un 'Pago a Cuenta' cargando el efectivo sin seleccionar facturas.")

            submit_recibo = st.button("💾 Generar Recibo Definitivo", type="primary", use_container_width=True)
            
            if submit_recibo:
                if total_valores <= 0 and not facturas_imputadas:
                    st.error("⚠️ Debes ingresar un importe o seleccionar una factura para generar el recibo.")
                else:
                    try:
                        fecha_str = fecha_recibo.strftime("%Y-%m-%d")
                        
                                                        
                        cursor.execute("""
                            INSERT INTO recibos (NUMERO, FECHA, CLIENTE, CONCEPTO, TOTAL)
                            VALUES (?, ?, ?, ?, ?)
                        """, (prox_recibo, fecha_str, cod_cliente, concepto_recibo, total_valores))
                        
                                                                      
                        for f_imp in facturas_imputadas:
                                                                                         
                            partes = f_imp.split(" | ")[0].split(" ")
                            tipo_fac = partes[0]
                            pref_num = partes[1].split("-")
                            prefijo = pref_num[0]
                            num_fac = pref_num[1]
                            
                                                                                                                           
                            cursor.execute("""
                                UPDATE factgral SET PAGO = TOTAL, RECI_NRO = ? 
                                WHERE CLIENTE = ? AND TIPO = ? AND PREFIJO = ? AND NUMERO = ?
                            """, (prox_recibo, cod_cliente, tipo_fac, prefijo, num_fac))
                            
                                                                                
                        detalle = f"Rec. Nº {prox_recibo}"
                        cursor.execute("""
                            INSERT INTO ctacte (NUMERO, FECHA, OPERACION, DEBE, HABER, SALDO)
                            VALUES (?, ?, ?, 0, ?, 0)
                        """, (cod_cliente, fecha_str, detalle, total_valores))

                        con.commit()
                        st.success(f"✅ ¡Recibo Nº {prox_recibo} generado correctamente por $ {total_valores:,.2f}!")
                        st.info("🖨️ En una próxima versión, este botón generará el PDF Original y Duplicado automáticamente.")
                        
                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al generar el recibo: {e}")

                                       
    with tab_historial:
        st.subheader("Buscador de Recibos Históricos")
        try:
            df_historial = pd.read_sql_query("""
                SELECT r.NUMERO, r.FECHA, c.NOMBRE AS CLIENTE, r.CONCEPTO, r.TOTAL 
                FROM recibos r
                LEFT JOIN clientes c ON r.CLIENTE = c.NUMERO
                ORDER BY r.FECHA DESC
            """, con)
            
            if not df_historial.empty:
                filtro_rec = st.text_input("🔍 Buscar por Número, Cliente o Concepto:")
                if filtro_rec:
                    mask = df_historial.astype(str).apply(lambda x: x.str.contains(filtro_rec, case=False, na=False)).any(axis=1)
                    df_mostrar_rec = df_historial[mask]
                else:
                    df_mostrar_rec = df_historial.head(100)                                      
                
                st.dataframe(
                    df_mostrar_rec, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={"TOTAL": st.column_config.NumberColumn(format="$ %.2f")}
                )
            else:
                st.info("No hay recibos registrados en la base de datos.")
        except Exception as e:
            st.warning(f"Error al leer el historial de recibos: {e}")

    con.close()    
                                                                                
def _pantalla_codigos_postales():
    st.title("📮 Gestión de Códigos Postales")
    st.markdown("Administrador de localidades y provincias para agilizar la carga de clientes.")
    
    con = sqlite3.connect(get_db_path())
    cursor = con.cursor()
    
                                                           
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS codigo (
            CODIGO TEXT PRIMARY KEY,
            LOCALIDAD TEXT,
            PROVINCIA TEXT
        )
    """)
    con.commit()

    tab_ver, tab_alta = st.tabs(["📋 Listado de Códigos", "➕ Agregar Localidad"])

    with tab_alta:
        with st.form("form_alta_codigo", clear_on_submit=True):
            st.subheader("Cargar Nuevo Código Postal")
            c1, c2, c3 = st.columns([1, 2, 2])
            with c1:
                codigo_postal = st.text_input("C.P. (Ej: 2200)")
            with c2:
                localidad = st.text_input("Localidad (Ej: San Lorenzo)")
            with c3:
                provincia = st.text_input("Provincia (Ej: Santa Fe)")
            
            btn_guardar = st.form_submit_button("💾 Guardar Código Postal", type="primary")
            
            if btn_guardar:
                if not codigo_postal or not localidad:
                    st.error("El Código Postal y la Localidad son obligatorios.")
                else:
                    try:
                                                                                                   
                        cursor.execute("""
                            INSERT OR REPLACE INTO codigo (CODIGO, LOCALIDAD, PROVINCIA)
                            VALUES (?, ?, ?)
                        """, (codigo_postal.strip(), localidad.strip().upper(), provincia.strip().upper()))
                        con.commit()
                        st.success(f"¡Localidad {localidad.upper()} ({codigo_postal}) guardada con éxito!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

    with tab_ver:
        try:
            df_codigos = pd.read_sql_query("SELECT CODIGO, LOCALIDAD, PROVINCIA FROM codigo ORDER BY LOCALIDAD", con)
            
            if not df_codigos.empty:
                                                                 
                busqueda = st.text_input("🔍 Buscar por C.P. o Localidad:")
                if busqueda:
                    df_codigos = df_codigos[df_codigos.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
                
                st.dataframe(df_codigos, use_container_width=True, hide_index=True)
            else:
                st.info("No hay códigos postales registrados en el sistema.")
                
        except Exception as e:
            st.error(f"Error al leer la base de datos: {e}")
            
    con.close()   
                                                                                
def _pantalla_ventas_provincia():
    st.title("🗺️ Estadística: Ventas por Provincia")
    st.markdown("Análisis del volumen de facturación agrupado por ubicación del cliente.")
    
    con = sqlite3.connect(get_db_path())
    
    col1, col2 = st.columns(2)
    with col1:
        mes_sel = st.selectbox("Mes:", ["Todos", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"])
    with col2:
        año_sel = st.number_input("Año:", min_value=2000, max_value=2050, value=2026, step=1)
    
    try:
                                                                      
        query = """
            SELECT c.PROVINCIA, COUNT(f.NUMERO) AS CANT_FACTURAS, SUM(f.NETO) AS TOTAL_NETO, SUM(f.TOTAL) AS TOTAL_FACTURADO
            FROM factgral f
            JOIN clientes c ON f.CLIENTE = c.NUMERO
            WHERE strftime('%Y', f.FECHA) = ?
        """
        params = [str(año_sel)]
        
        if mes_sel != "Todos":
            query += " AND strftime('%m', f.FECHA) = ?"
            params.append(mes_sel)
            
        query += " GROUP BY c.PROVINCIA ORDER BY TOTAL_FACTURADO DESC"
        
        df_ventas_prov = pd.read_sql_query(query, con, params=params)
        
        if not df_ventas_prov.empty:
            st.markdown("---")
            st.dataframe(
                df_ventas_prov, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "TOTAL_NETO": st.column_config.NumberColumn("Neto ($)", format="$ %.2f"),
                    "TOTAL_FACTURADO": st.column_config.NumberColumn("Facturado ($)", format="$ %.2f")
                }
            )
                                                                               
            st.bar_chart(data=df_ventas_prov.set_index("PROVINCIA")["TOTAL_FACTURADO"])
        else:
            st.warning(f"No se registraron ventas en el período seleccionado.")
            
    except Exception as e:
        st.error(f"Error al generar la estadística: {e}")
        st.info("Es posible que falte migrar la tabla de facturación (factgral) o cruzar los campos correctamente.")
        
    con.close()


                                                                                
def _pantalla_libro_ib():
    st.title("🏛️ Libro de Percepciones I.B. (Santa Fe)")
    st.markdown("Reporte quincenal de percepciones impositivas retenidas en facturación.")
    
    con = sqlite3.connect(get_db_path())
    
    with st.form("form_filtro_ib"):
        c1, c2, c3 = st.columns(3)
        with c1:
            mes = st.selectbox("Mes", ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"])
        with c2:
            anio = st.number_input("Año", min_value=2000, max_value=2050, value=2026, step=1)
        with c3:
            quincena = st.radio("Período", ["1ra. Quincena (Días 1 al 15)", "2da. Quincena (Días 16 al 31)"])
            
        btn_generar = st.form_submit_button("📊 Generar Reporte", type="primary")

    if btn_generar:
        try:
            operador_dia = "<=" if "1ra" in quincena else ">"
            
                                                                                                        
            query = f"""
                SELECT f.FECHA, f.TIPO, f.PREFIJO, f.NUMERO, c.NOMBRE AS CLIENTE, c.CUIT, f.NETO, f.PERCIBSF AS PERCEPCION_IB
                FROM factgral f
                JOIN clientes c ON f.CLIENTE = c.NUMERO
                WHERE strftime('%Y', f.FECHA) = ? 
                  AND strftime('%m', f.FECHA) = ?
                  AND cast(strftime('%d', f.FECHA) as integer) {operador_dia} 15
                  AND f.TIPO != 'R'
                  AND f.PERCIBSF > 0
                ORDER BY f.FECHA, f.NUMERO
            """
            
            df_libro_ib = pd.read_sql_query(query, con, params=[str(anio), mes])
            
            if not df_libro_ib.empty:
                st.success(f"Percepciones generadas para: {quincena.split(' (')[0]} de {mes}/{anio}")
                st.dataframe(
                    df_libro_ib,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "NETO": st.column_config.NumberColumn(format="$ %.2f"),
                        "PERCEPCION_IB": st.column_config.NumberColumn(format="$ %.2f")
                    }
                )
                
                st.metric("Total Percibido en la Quincena", f"$ {df_libro_ib['PERCEPCION_IB'].sum():,.2f}")
            else:
                st.info("No hay facturas con percepciones de I.B. Santa Fe en este período.")
                
        except Exception as e:
            st.error(f"Error al generar el libro: {e}")
            st.info("Asegurate de que la tabla 'factgral' tenga la columna 'PERCIBSF'.")
            
    con.close()