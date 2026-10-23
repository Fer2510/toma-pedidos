import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# Configuración de la página
st.set_page_config(page_title="Toma de Pedidos - Oficina Principal", layout="wide")

st.title("🛒 Sistema de Toma de Pedidos")
st.markdown("Ingrese el mercado y complete las cantidades para cada producto.")

# Datos del encabezado
col1, col2 = st.columns(2)
with col1:
    mercado = st.text_input("MERCADO / ZONA:", placeholder="Ej. Mercado Central / Cliente X")
with col2:
    fecha_pedido = st.date_input("FECHA:", value=datetime.now())

# Lista completa de los 45 productos
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

# Crear un DataFrame interactivo
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

# Función optimizada para guardar en Google Sheets de forma silenciosa
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
        sheet = spreadsheet.get_worksheet(0)
        
        # Escribir mercado y fecha
        sheet.update_acell('C2', mercado_val)
        sheet.update_acell('C3', str(fecha_val))
        
        # Preparar filas y enviar en bloque
        filas_a_guardar = []
        for index, row in df_enviado.iterrows():
            filas_a_guardar.append([
                str(row["PRODUCTO"]), 
                int(row["EXISTENCIA"]), 
                int(row["CAMBIOS"]), 
                int(row["PEDIDO"]), 
                int(row["SUGERIDO"])
            ])
        
        rango_destino = f'B6:F{5 + len(filas_a_guardar)}'
        sheet.update(rango_destino, filas_a_guardar)
        return True
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return False

# Botón para enviar pedido
if st.button("🚀 Enviar Pedido a la Oficina Principal", type="primary"):
    if not mercado:
        st.error("Por favor, ingresa el nombre del MERCADO antes de enviar.")
    else:
        with st.spinner("Enviando pedido a la nube..."):
            exito = guardar_en_google_sheets(edited_df, mercado, fecha_pedido)
            if exito:
                st.success(f"¡Pedido para **{mercado}** guardado con éxito en la hoja de cálculo de la oficina principal!")
