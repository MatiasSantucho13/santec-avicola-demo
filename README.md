# Gestión Avícola - Demo de portfolio

Versión de demostración de una aplicación modular escrita en Python con Streamlit, Pandas y SQLite. Incluye datos sintéticos generados al iniciar y una base temporal independiente por visitante.

## Datos incluidos

- 8 clientes ficticios.
- 5 proveedores ficticios.
- 12 productos y 3 rubros de ejemplo.
- 30 comprobantes ficticios de venta con detalles y cuentas corrientes.
- 15 comprobantes ficticios de compra y movimientos asociados.
- Recibos, cheques, bancos, vacunas y galpones de ejemplo.

Las fechas se generan en relación con el día de ejecución para que los reportes del período actual tengan datos. Los importes y movimientos son inventados; no preservan distribuciones ni valores de la empresa. Los identificadores fiscales se sustituyen por ceros y los domicilios, teléfonos y nombres son ficticios.

**No se incluye ni se copia la base original.** `data/schema.sql` contiene solamente las definiciones de las tablas necesarias. `demo_db.py` crea una SQLite nueva y genera todas sus filas. No existen rutas de descarga o carga de bases reales.

## Publicación sin instalar en tu PC

1. Crear un repositorio de GitHub para esta demo y subir los archivos de esta carpeta.
2. Ingresar a https://share.streamlit.io/ con la cuenta correspondiente y crear una aplicación.
3. Seleccionar el repositorio, rama y archivo principal **dashboard.py**.
4. Seleccionar Python 3.12 y desplegar. El servicio instala `requirements.txt`.

No requiere secretos ni conexiones con servicios de la empresa. No subir el ZIP entero como único archivo: hay que cargar su contenido en el repositorio.

El resultado de este paquete todavía no fue publicado en Streamlit Community Cloud. Las pruebas se ejecutaron con Streamlit AppTest, sin depender de un navegador. Confirmar la apertura de la URL pública después del despliegue. La disponibilidad y las condiciones de alojamiento dependen del proveedor.

## Recorrido sugerido

1. Clientes: revisar padrón, cuentas corrientes y saldos.
2. Ventas: seleccionar un cliente Demo compatible con el tipo de comprobante, agregar un Producto Demo y emitir un comprobante ficticio.
3. Historial de ventas: comprobar su aparición.
4. Clientes: consultar movimiento en cuenta corriente y registrar un pago de ejemplo.
5. Proveedores: consultar listado, compras y cuentas corrientes.
6. Artículos: revisar precios o dar de alta un artículo ficticio.
7. Listados: explorar certificados de vacunación ficticios.
8. Reiniciar mis datos de prueba: vuelve a generar el conjunto inicial de esa sesión.

## Arquitectura

- `dashboard.py`: configuración y navegación por módulos.
- `modulo_clientes.py`: padrón, movimientos, cobranzas, recibos y reportes.
- `modulo_proveedores.py`: proveedores, compras, pagos y retenciones demostrativas.
- `modulo_articulos.py`: artículos, rubros y precios.
- `modulo_facturacion.py`: comprobantes internos, detalles y registro de movimientos.
- `modulo_listados.py`: control sanitario de ejemplo.
- `modulo_estadisticas.py`: galpones y cálculos biológicos.
- `demo_db.py`: generación y aislamiento de bases temporales por sesión.
- `data/schema.sql`: estructura SQL sin datos de origen.

## Alcance y diferencias frente al material original

Se conservaron las pantallas y organización modular compartidas. La edición para demo incorpora base sintética por visitante, reinicio, carrito inicializado por sesión, búsqueda literal, identificador de cheques y tablas compatibles con las pantallas. También corrige el total de la Factura B para no sumar dos veces el IVA ya incluido.

Las pantallas de recría y producción son cálculos demostrativos: no se afirma persistencia de planillas biológicas. Donde el código no implementa una opción, se identifica como en desarrollo. Las búsquedas/reportes disponibles no acreditan una migración completa ni equivalencia de todas las reglas del sistema legacy.

**Sin validez fiscal.** No hay autorización electrónica, conexión con ARCA ni validación integral de impuestos, retenciones o normas contables. Los comprobantes y certificados son de prueba. No utilizar con información real ni para operar el negocio.

## Persistencia de la demo

La cookie/sesión de Streamlit determina el estado del visitante; cada sesión recibe un archivo SQLite aleatorio en el directorio temporal del servidor. No es una cuenta y no ofrece recuperación entre dispositivos. Un reinicio, desconexión o limpieza del alojamiento puede eliminar los datos. El directorio tiene limpieza de archivos con más de 24 horas sin modificaciones, realizada al crear nuevas sesiones. El acceso a un archivo cuyo plazo expiró puede requerir reiniciar la demo. Para producción hacen falta autenticación, roles, una base duradera, backups y políticas de retención.

## Pruebas

43 comprobaciones aprobadas: generación y coherencia básica, independencia de sesiones, apertura de 38 pantallas, reinicio y emisión de Factura A y B con registros persistidos. No constituyen validación fiscal ni prueba de todos los formularios.

Desarrollo opcional:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
streamlit run dashboard.py
```

No se incluyen los scripts originales de extracción desde DBF; la demo muestra la aplicación y su modelo de datos con un conjunto nuevo.
