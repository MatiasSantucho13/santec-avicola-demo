from pathlib import Path
import sqlite3
import pytest
from streamlit.testing.v1 import AppTest
from demo_db import create_demo
ROOT=Path(__file__).resolve().parents[1]


def test_synthetic_database(tmp_path):
    path=create_demo(tmp_path/'demo.sqlite')
    with sqlite3.connect(path) as con:
        assert con.execute('SELECT COUNT(*) FROM clientes').fetchone()[0]==8
        assert con.execute('SELECT COUNT(*) FROM factgral').fetchone()[0]==30
        assert con.execute('SELECT COUNT(*) FROM proveedores_maestro').fetchone()[0]==5
        assert con.execute('SELECT COUNT(*) FROM articulo').fetchone()[0]==12
        assert con.execute("SELECT COUNT(*) FROM clientes WHERE NOMBRE NOT LIKE 'Cliente Demo %'").fetchone()[0]==0
        assert con.execute("SELECT COUNT(*) FROM clientes WHERE CUIT != '00000000000'").fetchone()[0]==0
        assert con.execute('SELECT COUNT(*) FROM v_resumen_proveedores').fetchone()[0]==5
        assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok'


def test_sessions_use_separate_databases():
    a=AppTest.from_file(str(ROOT/'dashboard.py')).run()
    b=AppTest.from_file(str(ROOT/'dashboard.py')).run()
    assert not a.exception and not b.exception
    assert a.session_state['_demo_db']!=b.session_state['_demo_db']


PAGES={
 'CLIENTES':['Listados clientes','Informe Cta. Cte.','Saldos','Altas/Modificaciones','Pagos','Cheques','Códigos postales','Recibos','Venta por provincias','Libro Percepción IB'],
 'PROVEEDORES':['Altas/Modificaciones','Rubros','Artículos','Listado','Facturas','Nota Crédito','Nota Débito','Ver pagos','Bancos','Cancela facturas','Retención I.B.','Retención Ganancias','Retención IVA','Libros retenciones','Informes cta cte'],
 'ARTICULOS':['Artículos','Lista de Precios','Precios clientes'],
 'VENTAS':['Nueva Venta / Remito','Notas de Crédito','Notas de Débito','Historial / Buscar','Libro IVA Ventas'],
 'LISTADOS':['Cert. vacunas'],
 'ESTADISTICA':['Galpones recría','Recría','Galpones Producción','Producción']}


@pytest.mark.parametrize('module,page',[(m,p) for m,pages in PAGES.items() for p in pages])
def test_screen_renders(module,page):
    app=AppTest.from_file(str(ROOT/'dashboard.py'),default_timeout=15).run()
    app.sidebar.selectbox[0].select(module).run()
    app.sidebar.radio[0].set_value(page).run()
    assert not app.exception,[e.message for e in app.exception]
    assert not app.error,[e.value for e in app.error]

@pytest.mark.parametrize('invoice_type',['Factura A','Factura B'])
def test_issue_synthetic_invoice(invoice_type):
    app=AppTest.from_file(str(ROOT/'dashboard.py'),default_timeout=15).run()
    app.sidebar.selectbox[0].select('VENTAS').run()
    next(s for s in app.selectbox if s.label=='Tipo:').select(invoice_type).run()
    client=next(s for s in app.selectbox if s.label=='Cliente:')
    client.select(client.options[1]).run()
    article=next(s for s in app.selectbox if s.label=='Artículo')
    article.select(article.options[1])
    next(b for b in app.button if 'Añadir' in b.label).click().run()
    assert not app.exception
    next(b for b in app.button if 'EMITIR' in b.label).click().run()
    assert not app.exception and not app.error,[e.value for e in app.error]
    with sqlite3.connect(app.session_state['_demo_db']) as con:
        assert con.execute('SELECT COUNT(*) FROM factgral').fetchone()[0]==31
        net,vat,total=con.execute('SELECT NETO,IVA1,TOTAL FROM factgral ORDER BY rowid DESC LIMIT 1').fetchone()
        assert abs(net+vat-total)<0.01
        if invoice_type=='Factura B':assert total==625.5


def test_reset_restores_seed():
    app=AppTest.from_file(str(ROOT/'dashboard.py')).run()
    old=app.session_state['_demo_db']
    with sqlite3.connect(old) as con:con.execute('DELETE FROM clientes');con.commit()
    app.sidebar.button[0].click().run()
    assert not app.exception
    new=app.session_state['_demo_db']
    assert old!=new
    with sqlite3.connect(new) as con:assert con.execute('SELECT COUNT(*) FROM clientes').fetchone()[0]==8
