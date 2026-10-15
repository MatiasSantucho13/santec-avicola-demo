"""
modulo_articulos.py
Santec Software — Módulo Artículos y Precios
"""
import sqlite3
import pandas as pd
import streamlit as st

from demo_db import get_db_path

def render_articulos(accion: str):
    """Enrutador principal de pantallas del módulo de Artículos."""
    if accion == "Artículos":
        _pantalla_abm_articulos()
    elif accion == "Lista de Precios":
        _pantalla_lista_precios()
    elif accion == "Precios clientes":
        _pantalla_precios_clientes()
    else:
        st.title(f"📦 Artículos › {accion}")
        st.info(f"La pantalla **{accion}** está en desarrollo.")

                                                                                
def _pantalla_abm_articulos():
    st.title("📦 Maestro de Artículos")
    st.markdown("Gestión de productos, clasificación por rubros y asignación de precios.")
    
    con = sqlite3.connect(get_db_path())
    cursor = con.cursor()
    
                                                                                       
    try:
                                                                                          
        cursor.execute("ALTER TABLE articulo ADD COLUMN RUBRO TEXT DEFAULT '01'")
        cursor.execute("ALTER TABLE articulo ADD COLUMN SUBRUBRO TEXT DEFAULT '01'")
        con.commit()
    except Exception:
        pass                                                            
        
    try:
        cursor.execute("SELECT count(*) FROM rubros")
        if cursor.fetchone()[0] == 0:
             cursor.execute("INSERT INTO rubros (RUBRO, CONCEPTO) VALUES ('01', 'POLLOS EVISCERADOS')")
             cursor.execute("INSERT INTO rubros (RUBRO, CONCEPTO) VALUES ('02', 'HUEVOS')")
             cursor.execute("INSERT INTO subrubro (RUBRO, SUBRUBRO, CONCEPTO) VALUES ('01', '01', 'FRESCO')")
             cursor.execute("INSERT INTO subrubro (RUBRO, SUBRUBRO, CONCEPTO) VALUES ('01', '02', 'CONGELADO')")
             con.commit()
    except:
        pass

                                                                          
    try:
        df_rubros = pd.read_sql_query("SELECT RUBRO, CONCEPTO FROM rubros", con)
        lista_rubros = [f"{row['RUBRO']} - {row['CONCEPTO']}" for _, row in df_rubros.iterrows()]
    except Exception:
        lista_rubros = ["01 - GENERAL"]

    tab_ver, tab_alta = st.tabs(["🔍 Ver Catálogo", "➕ Nuevo Artículo"])

                                                   
    with tab_ver:
        st.subheader("Catálogo de Artículos Activos")
        try:
                                        
            query_catalogo = """
                SELECT a.CODIGO, r.CONCEPTO AS RUBRO_DESC, s.CONCEPTO AS SUBRUBRO_DESC, 
                       a.DESCRIP AS DESCRIPCION, a.PRECIO 
                FROM articulo a
                LEFT JOIN rubros r ON a.RUBRO = r.RUBRO
                LEFT JOIN subrubro s ON a.RUBRO = s.RUBRO AND a.SUBRUBRO = s.SUBRUBRO
                ORDER BY a.RUBRO, a.SUBRUBRO, a.CODIGO
            """
            df_articulos = pd.read_sql_query(query_catalogo, con)
            
            if not df_articulos.empty:
                filtro = st.text_input("🔍 Filtrar por código o descripción:")
                if filtro:
                    mask = df_articulos.astype(str).apply(lambda x: x.str.contains(filtro, case=False, na=False)).any(axis=1)
                    df_mostrar = df_articulos[mask]
                else:
                    df_mostrar = df_articulos
                
                               
                st.dataframe(
                    df_mostrar.rename(columns={
                        "CODIGO": "Código", "RUBRO_DESC": "Rubro", "SUBRUBRO_DESC": "Subrubro",
                        "DESCRIPCION": "Descripción", "PRECIO": "Precio Base"
                    }),
                    use_container_width=True,
                    hide_index=True,
                    column_config={"Precio Base": st.column_config.NumberColumn(format="$ %.2f")}
                )
                
                                                                             
                st.markdown("---")
                st.subheader("✏️ Modificación Rápida de Precio")
                lista_edicion = [f"{row['CODIGO']} - {row['DESCRIPCION']}" for _, row in df_mostrar.iterrows()]
                
                if lista_edicion:
                    art_editar = st.selectbox("Seleccionar artículo a modificar:", [""] + lista_edicion)
                    if art_editar:
                        cod_edit = art_editar.split(" - ")[0]
                        precio_actual = df_articulos[df_articulos['CODIGO'] == cod_edit]['PRECIO'].values[0]
                        
                        with st.form("form_edit_precio", clear_on_submit=True):
                            col_p1, col_p2 = st.columns(2)
                            with col_p1:
                                nuevo_precio = st.number_input("Nuevo Precio ($)", min_value=0.0, value=float(precio_actual or 0), step=10.0)
                            with col_p2:
                                st.info(f"Precio final sugerido (15% desc.): **$ {nuevo_precio * 0.85:,.2f}**")
                            
                            if st.form_submit_button("🔄 Actualizar Precio", type="primary"):
                                cursor.execute("UPDATE articulo SET PRECIO = ? WHERE CODIGO = ?", (nuevo_precio, cod_edit))
                                con.commit()
                                st.success(f"¡Precio del artículo {cod_edit} actualizado exitosamente!")
                                st.rerun()

            else:
                st.info("El maestro de artículos está vacío.")
        except Exception as e:
            st.error(f"Error al leer la base de artículos: {e}")

                                         
    with tab_alta:
        st.subheader("Dar de Alta un Producto")
        
                                                                                            
                                                           
        rubro_sel = st.selectbox("1. Clasificación Principal (Rubro)", lista_rubros)
        
        if rubro_sel:
            cod_rubro = rubro_sel.split(" - ")[0]
            try:
                df_subrubros = pd.read_sql_query("SELECT SUBRUBRO, CONCEPTO FROM subrubro WHERE RUBRO = ?", con, params=[cod_rubro])
                lista_subrubros = [f"{row['SUBRUBRO']} - {row['CONCEPTO']}" for _, row in df_subrubros.iterrows()]
            except:
                lista_subrubros = ["01 - GENERAL"]
                
            subrubro_sel = st.selectbox("2. Clasificación Secundaria (Subrubro)", lista_subrubros)
            
            with st.form("form_alta_art"):
                st.write("**3. Detalles del Producto**")
                descripcion = st.text_input("Descripción *", max_chars=40)
                precio_base = st.number_input("Precio Base de Venta ($)", min_value=0.0, step=100.0)
                
                st.info("El código del artículo será generado automáticamente.")
                
                if st.form_submit_button("💾 Guardar Artículo", type="primary"):
                    if not descripcion.strip():
                        st.error("⚠️ La descripción es obligatoria.")
                    else:
                        cod_subrubro = subrubro_sel.split(" - ")[0] if subrubro_sel else "01"
                        
                        try:
                                                                                       
                            cursor.execute("SELECT MAX(CAST(CODIGO AS INTEGER)) FROM articulo")
                            max_cod = cursor.fetchone()[0]
                            nuevo_cod_num = 1 if max_cod is None else max_cod + 1
                            nuevo_cod = str(nuevo_cod_num).zfill(3)                                             
                            
                            cursor.execute("""
                                INSERT INTO articulo (CODIGO, RUBRO, SUBRUBRO, DESCRIP, PRECIO)
                                VALUES (?, ?, ?, ?, ?)
                            """, (nuevo_cod, cod_rubro, cod_subrubro, descripcion.upper(), precio_base))
                            
                            con.commit()
                            st.success(f"✅ ¡Artículo '{descripcion}' guardado con el Código Nº {nuevo_cod}!")
                            st.rerun()
                        except Exception as e:
                            con.rollback()
                            st.error(f"❌ Error al guardar en la base: {e}")

    con.close()

                                                                                
def _pantalla_lista_precios():
    st.title("📄 Emisión de Lista de Precios")
    st.markdown("Generación del tarifario vigente con cálculo de descuentos.")
    
    con = sqlite3.connect(get_db_path())
    
    try:
        query = """
            SELECT r.CONCEPTO AS RUBRO, s.CONCEPTO AS SUBRUBRO, a.CODIGO, 
                   a.DESCRIP AS DESCRIPCION, a.PRECIO AS PRECIO_BASE
            FROM articulo a
            LEFT JOIN rubros r ON a.RUBRO = r.RUBRO
            LEFT JOIN subrubro s ON a.RUBRO = s.RUBRO AND a.SUBRUBRO = s.SUBRUBRO
            ORDER BY a.RUBRO, a.SUBRUBRO, a.CODIGO
        """
        df_precios = pd.read_sql_query(query, con)
        
        if not df_precios.empty:
                                                                      
            porcentaje_dto = st.slider("Descuento mayorista a mostrar en lista (%):", 0, 50, 15)
            df_precios['PRECIO_FINAL'] = df_precios['PRECIO_BASE'] * (1 - (porcentaje_dto/100))
            
            st.dataframe(
                df_precios,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "PRECIO_BASE": st.column_config.NumberColumn("Precio Lista ($)", format="$ %.2f"),
                    "PRECIO_FINAL": st.column_config.NumberColumn("Precio c/ Dto ($)", format="$ %.2f")
                }
            )
            
                                                                                 
                                                                               
            csv = df_precios.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Tarifario (Excel/CSV)",
                data=csv,
                file_name='lista_precios_santec.csv',
                mime='text/csv',
            )
        else:
            st.info("No hay artículos en la base de datos para generar la lista.")
    except Exception as e:
        st.error(f"Error al generar la lista: {e}")
        
    con.close()


                                                                                
def _pantalla_precios_clientes():
    st.title("📈 Actualización Masiva de Precios")
    st.markdown("Herramienta rápida para indexar o rebajar precios por rubro (Reemplaza los scripts manuales de FoxPro).")
    
    con = sqlite3.connect(get_db_path())
    cursor = con.cursor()
    
    try:
        df_rubros = pd.read_sql_query("SELECT RUBRO, CONCEPTO FROM rubros", con)
        lista_rubros = ["TODOS LOS RUBROS"] + [f"{row['RUBRO']} - {row['CONCEPTO']}" for _, row in df_rubros.iterrows()]
    except:
        lista_rubros = ["TODOS LOS RUBROS"]

    with st.form("form_indexacion"):
        st.write("Seleccioná el alcance de la actualización:")
        rubro_afectar = st.selectbox("Rubro a modificar:", lista_rubros)
        
        col1, col2 = st.columns(2)
        with col1:
            operacion = st.radio("Acción:", ["Aumentar Precios (+)", "Bajar Precios (-)"])
        with col2:
            porcentaje = st.number_input("Porcentaje a aplicar (%)", min_value=0.1, max_value=200.0, value=10.0, step=1.0)
            
        st.warning("⚠️ Atención: Esta acción modificará los precios base de los artículos inmediatamente.")
        btn_aplicar = st.form_submit_button("🚀 Aplicar Modificación", type="primary")
        
        if btn_aplicar:
            try:
                factor = (1 + (porcentaje / 100)) if "Aumentar" in operacion else (1 - (porcentaje / 100))
                
                if rubro_afectar == "TODOS LOS RUBROS":
                    cursor.execute("UPDATE articulo SET PRECIO = PRECIO * ?", (factor,))
                    afectados = cursor.rowcount
                else:
                    cod_rub = rubro_afectar.split(" - ")[0]
                    cursor.execute("UPDATE articulo SET PRECIO = PRECIO * ? WHERE RUBRO = ?", (factor, cod_rub))
                    afectados = cursor.rowcount
                    
                con.commit()
                st.success(f"¡Éxito! Se actualizaron {afectados} artículos.")
                st.info("Revisá la Lista de Precios para confirmar los nuevos valores.")
            except Exception as e:
                con.rollback()
                st.error(f"Error al actualizar la base de datos: {e}")

    con.close()