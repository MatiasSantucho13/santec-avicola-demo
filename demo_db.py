"""Independent synthetic SQLite database for each Streamlit visitor."""
from pathlib import Path
from datetime import date,timedelta
import os,sqlite3,tempfile,uuid
import streamlit as st
ROOT=Path(__file__).resolve().parent


def create_demo(path):
    path=Path(path)
    if path.exists(): path.unlink()
    con=sqlite3.connect(path)
    con.executescript((ROOT/'data/schema.sql').read_text())
    def insert(table,values):
        cols=','.join('"'+c+'"' for c in values)
        con.execute(f'INSERT INTO "{table}" ({cols}) VALUES ({",".join("?" for _ in values)})',tuple(values.values()))
    today=date.today()
    for i in range(1,9):
        insert('clientes',dict(NUMERO=f'{i:05}',NOMBRE=f'Cliente Demo {i:02}',DIRECCION=f'Domicilio ficticio {i}',CODPOSTAL='0000',LOCALIDAD='Localidad Demo',PROVINCIA=['SANTA FE','CORDOBA','BUENOS AIRES'][i%3],CUIT='00000000000',TIPO=['I','MT','CF'][i%3],TIPORESP=1,TIPODOC=80,TELEFONO='0000000000',ACTIVIDAD='Actividad ficticia',ACTIVO='S',CTACTE='S',PIBRUSFE=0,TIPO_POLLA=0,ING_BRUTOS='DEMO',CM='',RELACION='',IMPUTA='C',VALOR=0))
    for i in range(1,6):
        insert('proveedores_maestro',dict(NUMERO=f'{i:05}',NOMBRE=f'Proveedor Demo {i:02}',DIRECCION=f'Domicilio ficticio {i}',LOCALIDAD='Localidad Demo',PROVINCIA='SANTA FE',CODPOSTAL='0000',CUIT='00000000000',TIPO='I',ING_BRUTOS='DEMO',CM='',IMPUTA='C',DISCRIMINA=1,TIPO_GANA=''))
    for i,name in [(1,'AVES DEMO'),(2,'HUEVOS DEMO'),(3,'INSUMOS DEMO')]:
        insert('rubros',dict(RUBRO=i,CONCEPTO=name,TIPO=0,A_GASTOS='N'))
        insert('subrubro',dict(RUBRO=f'{i:02}',SUBRUBRO='01',CONCEPTO='GENERAL DEMO',CONCEPTO1=name))
    for i in range(1,13):
        rubro=(i-1)%3+1
        insert('articulo',dict(CODIGO=f'{i:05}',DESCRIP=f'Producto Demo {i:02}',UNIDAD='UN',PRECIO=round(500+i*125.5,2),RUBRO=f'{rubro:02}',SUBRUBRO='01'))
        insert('comp_art',dict(RUBRO=rubro,CODIGO=f'{i:05}',DESCRIP=f'Insumo Demo {i:02}',UNIDAD='UN',PRECIO=200+i*50,PROVEEDO=f'{(i%5)+1:05}'))
    balances={f'{i:05}':0.0 for i in range(1,9)}
    for i in range(1,31):
        client=f'{(i-1)%8+1:05}';day=(today-timedelta(days=31-i)).isoformat();net=10000+i*500;iva=round(net*.21,2);total=net+iva;paid=total if i%3==0 else 0;num=f'{i:08}'
        insert('factgral',dict(FECHA=day,TIPO='A',PREFIJO='0001',NUMERO=num,PERIODO=day[:7].replace('-',''),CLIENTE=client,CLIEDENO=f'Cliente Demo {(i-1)%8+1:02}',CUIT='00000000000',TOTALITEMS=1,NETO=net,IVA1=iva,PERCIBSF=0,TOTAL=total,PAGO=paid,REMITO='00000000',CAE='SIN-VALIDEZ-FISCAL'))
        insert('factdato',dict(TIPO='A',NUMERO=num,CANTIDAD=10,CODIGO=f'{(i-1)%12+1:05}',UNITARIO=net/10,TOTAL=net))
        balances[client]+=total
        insert('ctacte',dict(NUMERO=client,FECHA=day,OPER_NRO=i,OPERACION=f'Factura DEMO {num}',DEBE=total,HABER=0,SALDO=balances[client]))
        if paid:
            balances[client]-=paid
            insert('ctacte',dict(NUMERO=client,FECHA=day,OPER_NRO=100+i,OPERACION=f'Pago DEMO {num}',DEBE=0,HABER=paid,SALDO=balances[client]))
            insert('recibos',dict(NUMERO=num,FECHA=day,CLIENTE=client,CONCEPTO='Cobro ficticio',TOTAL=paid))
    prov_bal={f'{i:05}':0.0 for i in range(1,6)}
    for i in range(1,16):
        prov=f'{(i-1)%5+1:05}';day=(today-timedelta(days=16-i)).isoformat();net=20000+i*300;iva=round(net*.21,2);total=net+iva
        insert('proveedores_facturas',dict(FECHA=day,PERIODO=day[:7].replace('-',''),COMPROB='FACTURA DEMO',TIPO='A',NUMERO=f'{i:08}',CLIENTE=prov,CLIEDENO=f'Proveedor Demo {(i-1)%5+1:02}',CUIT='00000000000',NETO=net,NETO10_5=0,IVA1=iva,IVA2=0,IVA10_5=0,PERCEP=0,PERCIB=0,NOGRAVA=0,EXENTO=0,IB=0,TOTAL_A=total,TOTAL_BC=total))
        prov_bal[prov]+=total
        insert('proveedores_ctacte',dict(NUMERO=int(prov),FECHA=day,OPERACION=f'Compra DEMO {i:08}',DEBE=total,HABER=0,SALDO=prov_bal[prov]))
    for i in range(1,4):
        insert('bancos',dict(FECHA=today.isoformat(),NOMBRE=f'Banco Demo {i}',CUIT=0))
        insert('codigo',dict(CODIGO=f'{i:04}',LOCALIDAD=f'Localidad Demo {i}',PROVINCIA='SANTA FE'))
        insert('galpones_maestro',dict(NUMERO=f'{i:02}',TIPO='RECRIA' if i==1 else 'PRODUCCION',PLANTEL=f'Lote Demo {i}',AVES_ALOJADAS=10000+i*1000,SEMANA_ACTUAL=10+i,ESTADO='ACTIVO'))
    for i in range(1,7):
        insert('cheques',dict(NUMEROCLIE=f'{i:05}',FECHA=today.isoformat(),NUMERO=f'DEMO-{i:04}',BANCO=f'Banco Demo {(i%3)+1}',FECHACOMP=today.isoformat(),VTO=(today+timedelta(days=i*5)).isoformat(),IMPORTE=1000+i*500,COBRADO='N',ESTADO='CARTERA' if i<5 else 'DEPOSITADO'))
        insert('vacunas',dict(VACUNA=f'Vacuna Demo {i}',NOMBRE_VACUNA=f'Vacuna Demo {i}',TIPO='DEMO',VIA='SIMULADA',SERIES='DEMO',MARCAS='MARCA FICTICIA',VENCE=(today+timedelta(days=90)).isoformat(),DOSIS='1000',FACTURA=f'DEMO-{i:04}',FECHA=today.isoformat(),RAZA='LINEA DEMO',LOTE_VACUNA=f'LOTE-DEMO-{i}'))
    for table in ['reten_ib','contabil__rete_dgr','contabil__rete_iva']:
        insert(table,dict(NUMERO='DEMO-0001',FECHA=today.isoformat(),PROVEEDOR='00001',NETO=10000,ALICUOTA=2,RETENCION=200))
    con.commit();con.close()
    return str(path)


def get_db_path():
    if '_demo_db' not in st.session_state:
        directory=Path(tempfile.gettempdir())/'santec-avicola-demo'
        directory.mkdir(exist_ok=True)
        # Best-effort cleanup of old, non-current demo files after 24 hours.
        import time
        for old in directory.glob('*.sqlite'):
            try:
                if time.time()-old.stat().st_mtime>86400:old.unlink()
            except OSError:pass
        path=directory/(uuid.uuid4().hex+'.sqlite')
        st.session_state['_demo_db']=create_demo(path)
    return st.session_state['_demo_db']


def reset_demo():
    path=st.session_state.pop('_demo_db',None)
    if path:
        try:Path(path).unlink(missing_ok=True)
        except OSError:pass
    st.session_state.pop('carrito',None)
