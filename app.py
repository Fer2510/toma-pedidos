import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
import urllib.parse
from github import Github

st.set_page_config(page_title="Toma de Pedidos - Oficina Principal", layout="wide")

# Estilos CSS y JavaScript para ocultar elementos superiores, menús e insignias flotantes
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp > header {display: none;}
    [data-testid='stToolbar'] {visibility: hidden; display: none;}
    [data-testid='stDecoration'] {display: none;}
    [data-testid='stStatusWidget'] {visibility: hidden;}
    div[class*='viewerBadge'] {display: none !important;}
    .viewerBadge_container__1QSob {display: none !important;}
    a[href*="streamlit.io/cloud"] {display: none !important;}
    </style>
    
    <script>
    const observer = new MutationObserver((mutations) => {
        document.querySelectorAll('a, div, span, button').forEach(el => {
            if (el.innerText && el.innerText.includes('Manage app')) {
                let target = el.closest('div[style*="position: fixed"]') || el.parentElement;
                if (target) {
                    target.style.display = 'none';
                    target.remove();
                }
            }
        });
    });
    observer.observe(document.body, { childList: true, subtree: true });
    </script>
""", unsafe_allow_html=True)

st.title("🛒 Sistema de Toma de Pedidos")
st.markdown("Ingrese el mercado y complete las cantidades para cada producto.")

col1, col2, col3 = st.columns(3)
with col1:
    mercado = st.text_input("MERCADO / ZONA:", placeholder="Ej. Mercado Central / Cliente X")
with col2:
    fecha_pedido = st.date_input("FECHA:", value=datetime.now())
with col3:
    vendedor = st.text_input("VENDEDOR:", placeholder="Ej. Pedro Perez")

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

# Inicializar el correlativo en la sesión de Streamlit si no existe
if 'numero_secuencial' not in st.session_state:
    st.session_state['numero_secuencial'] = 4  # Ajustado para continuar en 5 en el primer envío

# Función para generar el PDF en memoria
def generar_pdf(df_enviado, mercado_val, fecha_val, vendedor_val, nro_pedido):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1b5e20'),
        alignment=1,
        spaceAfter=15
    )
    
    normal_style = styles['Normal']
    
    elements.append(Paragraph(f"<b>REPORTE DE PEDIDO N° {nro_pedido:04d}</b>", title_style))
    elements.append(Paragraph(f"<b>Mercado / Zona:</b> {mercado_val}", normal_style))
    elements.append(Paragraph(f"<b>Fecha:</b> {str(fecha_val)}", normal_style))
    elements.append(Paragraph(f"<b>Vendedor:</b> {vendedor_val}", normal_style))
    elements.append(Spacer(1, 15))
    
    df_filtrado = df_enviado[
        (df_enviado["EXISTENCIA"] > 0) | 
        (df_enviado["CAMBIOS"] > 0) | 
        (df_enviado["PEDIDO"] > 0) | 
        (df_enviado["SUGERIDO"] > 0)
    ]
    
    if df_filtrado.empty:
        df_filtrado = df_enviado
        
    table_data = [["PRODUCTO", "EXISTENCIA", "CAMBIOS", "PEDIDO", "SUGERIDO"]]
    for _, row in df_filtrado.iterrows():
        table_data.append([
            str(row["PRODUCTO"]),
            str(row["EXISTENCIA"]),
            str(row["CAMBIOS"]),
            str(row["PEDIDO"]),
            str(row["SUGERIDO"])
        ])
        
    t = Table(table_data, colWidths=[200, 70, 70, 70, 70])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2e7d32')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (0,1), (0,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), '
