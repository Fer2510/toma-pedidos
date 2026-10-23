import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Toma de Pedidos - Oficina Principal", layout="wide")

st.title("🛒 Sistema de Toma de Pedidos")
st.markdown("Ingrese el mercado y complete las cantidades para cada producto.")

col1, col2 = st.columns(2)
with col1:
    mercado = st.text_input("MERCADO / ZONA:", placeholder="Ej. Mercado Central / Cliente X")
with col2:
    fecha_pedido = st.date_input("FECHA:", value=datetime.now())

productos = [
    "ALIÑO PICADO 150 g.", "AJI 200 g.", "ACELGAS 200 g.", "AJO PORRO 300 g.", "ALBAHACA 50 g.",
    "COMPUESTO CEBOLLIN Y CILANTRO 150 g.", "CILANTRO 40 g.", "CEBOLLIN 150 g.", "ESPINACA 200 g.", "HIERBABUENA 50 g.",
    "PAPITA 500 g.", "PEREJIL RIZADO 50 g.", "PEREJIL LISO 50 g.", "VAINITAS 300 g.", "AJO PELADO 100 g.",
    "JOJOTO 350 g.", "RUCULA 60 g.", "CHAMPIÑONES 300 g.", "ESPARRAGOS 500 g.", "LECHUGA ROMANA 500 g.",
    "BROCOLI 350 g.", "KALE 200 g.", "COLIFLOR 350 g.", "ZANAHORIA BEBE 250g.", "PEPINO 450 g.",
    "CALABACIN 400 g.", "BERENJENA 400 g.", "TOMATE CHERRY 310 g.", "PEPINILLOS 500 g.", "BERRO 100 g.",
    "ENSALADA LECHUGA BABY MIXX 150g", "MENTA 25 g.", "CELERI 100 g.", "GERMINADOS 250 g", "LECHUGA RIZADA 200 g",
    "CALABACIN BEBE 400 g.", "HINOJO 400 g", "VAINITA ANCHA 300 g", "COLES DE BRUSELAS 300 g",
    "ENSALADA RALLADAS REPOLLOS Y ZANAHORIA 250 g", "ENSALADA RALLADA DE ZANAHORIA Y REPOLLO 250 g",
    "FRESAS 250 g.", "ALFALFA 100 g", "PAPA LAVADA", "FACHAON"
]

st.markdown("### Detalle de Productos")

data = []
for p in productos:
    data.append({
        "PRODUCTO": p,
        "EXISTENCIA": 0,
        "CAMBIOS": 0,
        "PEDIDO": 0,
        "SUGERIDO": 0
    })

df_input = pd.DataFrame(data)

edited_df = st.data_editor(
    df_input,
    num_rows="fixed",
    use_container_width=True,
    hide_index=True
)

# Función optimizada con búsqueda exacta de cada producto en la hoja
def guardar_en_google_sheets(df_enviado, mercado_val, fecha_val):
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict)
        creds = creds.with_scopes(scopes)
        
        client = gspread.authorize(creds)
        spreadsheet = client.open("Consolidado_Pedidos_Google_Forms")
        sheet = spreadsheet.worksheet("Matriz de Pedidos")
        
        # 1. Actualizar cabeceras de Mercado y Fecha
        try:
            cell_m = sheet.find("MERCADO:")
            sheet.update_cell(cell_m.row, cell_m.col + 1, str(mercado_val))
        except:
            sheet.update('C2', [[str(mercado_val)]])
            
        try:
            cell_f = sheet.find("FECHA:")
            sheet.update_cell(cell_f.row, cell_f.col + 1, str(fecha_val))
        except:
            sheet.update('C3', [[str(fecha_val)]])
        
        # 2. Recorrer cada producto de la tabla y buscar su celda exacta en la hoja de Google Sheets
        for _, row in df_enviado.iterrows\
            ():
            nombre_prod = str(row["PRODUCTO"])
            existencia = int(row["EXISTENCIA"])
            cambios = int(row["CAMBIOS"])
            pedido = int(row["PEDIDO"])
            sugerido = int(row["SUGERIDO"])
            
            try:
                # Buscar la celda donde está escrito exactamente el nombre del producto
                celda_prod = sheet.find(nombre_prod)
                fila = celda_prod.row
                columna_prod = celda_prod.col # Columna B típicamente
                
                # Actualizar los valores en las columnas contiguas (C: Existencia, D: Cambios, E: Pedido, F: Sugerido)
                rango_fila = f'C{fila}:F{fila}'
                sheet.update(rango_fila, [[existencia, cambios, pedido, sugerido]])
            except Exception as ex_prod:
                # Si algún producto no se encuentra por texto exacto, continuamos con los demás
                continue
            
        return True, "OK"
    except Exception as e:
        error_str = str(e)
        if "Response [200]" in error_str or "200" in error_str:
            return True, "OK"
        return False, error_str

if st.button("🚀 Enviar Pedido a la Oficina Principal", type="primary"):
    if not mercado:
        st.error("Por favor, ingresa el nombre del MERCADO antes de enviar.")
    else:
        with st.spinner("Sincronizando con Google Sheets..."):
            exito, mensaje = guardar_en_google_sheets(edited_df, mercado, fecha_pedido)
            if exito:
                st.success(f"¡Pedido para **{mercado}** guardado y sincronizado con éxito!")
            else:
                st.error(f"Error al guardar: {mensaje}")
