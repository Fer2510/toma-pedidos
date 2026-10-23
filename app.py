import streamlit as st
import pandas as pd
from datetime import datetime

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
st.markdown("Deslice o complete los campos para cada producto:")

# Crear un DataFrame interactivo para que el usuario ingrese los datos
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

# Mostrar tabla editable en la web
edited_df = st.data_editor(
    df_input,
    num_rows="fixed",
    use_container_width=True,
    hide_index=True
)

# Botón para enviar pedido
if st.button("🚀 Enviar Pedido a la Oficina Principal", type="primary"):
    if not mercado:
        st.error("Por favor, ingresa el nombre del MERCADO antes de enviar.")
    else:
        # Aquí se procesa y se envía a Google Sheets / CSV
        st.success(f"¡Pedido para **{mercado}** registrado con éxito!")
        
        # Mostrar resumen de lo que se envió con valores mayores a 0
        df_enviar = edited_df[(edited_df["EXISTENCIA"] > 0) | (edited_df["CAMBIOS"] > 0) | (edited_df["PEDIDO"] > 0) | (edited_df["SUGERIDO"] > 0)]
        
        st.write("Resumen de productos con movimiento:")
        st.dataframe(df_enviar)
        
        # Opcional: Descargar CSV localmente como respaldo
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar respaldo CSV",
            data=csv,
            file_name=f"pedido_{mercado}_{fecha_pedido}.csv",
            mime='text/csv',
        )
