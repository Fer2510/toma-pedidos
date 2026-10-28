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

# Estilos CSS para ocultar barras e insignias
# Estilos CSS para ocultar barras, insignias y BLOQUEAR el movimiento de columnas en la tabla
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
    
    /* BLOQUEO DE MOVER COLUMNAS EN LA TABLA DATA_EDITOR */
    [data-testid="stDataEditor"] canvas {
        pointer-events: auto;
    }
    /* Inhabilita el arrastre en la cabecera del editor */
    [data-testid="stDataEditor"] div[role="grid"] div[role="columnheader"] {
        pointer-events: none !important;
        user-select: none !important;
    }
    </style>
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
    hide_index=True,
    height=650,
    column_order=("PRODUCTO", "EXISTENCIA", "CAMBIOS", "PEDIDO", "SUGERIDO"),
    disabled=["PRODUCTO"]  # <--- Esto bloquea la columna de productos para que no se mueva ni se edite su texto
)

def generar_pdf(df_enviado, mercado_val, fecha_val, vendedor_val):
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
    
    elements.append(Paragraph("<b>REPORTE DE PEDIDO</b>", title_style))
    elements.append(Paragraph(f"<b>Mercado / Zona:</b> {mercado_val}", normal_style))
    elements.append(Paragraph(f"<b>Fecha:</b> {str(fecha_val)}", normal_style))
    elements.append(Paragraph(f"<b>Vendedor:</b> {vendedor_val}", normal_style))
    elements.append(Spacer(1, 15))
    
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
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f1f8e9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#c8e6c9')),
        ('FONTSIZE', (0,1), (-1,-1), 9)
    ]))
    
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer

def construir_mensaje_whatsapp(mercado_val, fecha_val, vendedor_val, df_enviado):
    df_activos = df_enviado
    
    texto_wsp = f"🛒 *NUEVO PEDIDO*\n" \
                f"📍 *Mercado:* {mercado_val}\n" \
                f"📅 *Fecha:* {str(fecha_val)}\n" \
                f"👤 *Vendedor:* {vendedor_val}\n\n" \
                f"*Detalle de ítems:*\n"
    
    for _, row in df_activos.iterrows():
        texto_wsp += f"• *{row['PRODUCTO']}*\n" \
                     f"  - Existencia: {row['EXISTENCIA']}\n" \
                     f"  - Cambios: {row['CAMBIOS']}\n" \
                     f"  - Pedido: {row['PEDIDO']}\n" \
                     f"  - Sugerido: {row['SUGERIDO']}\n\n"
                     
    return texto_wsp

def convertir_df_a_csv(df):
    return df.to_csv(index=False).encode('utf-8-sig')

def guardar_pdf_en_github(pdf_buffer, nombre_archivo):
    try:
        if "GITHUB_TOKEN" in st.secrets and "GITHUB_REPO" in st.secrets:
            g = Github(st.secrets["GITHUB_TOKEN"])
            repo = g.get_repo(st.secrets["GITHUB_REPO"])
            contenido_bytes = pdf_buffer.getvalue()
            ruta_archivo = f"pdf_guardados/{nombre_archivo}"
            
            repo.create_file(
                path=ruta_archivo,
                message=f"Auto-guardado comprobante {nombre_archivo}",
                content=contenido_bytes,
                branch="main"
            )
            st.success("📁 ¡PDF guardado automáticamente en GitHub con éxito!")
        else:
            st.warning("⚠️ No se encontraron GITHUB_TOKEN o GITHUB_REPO en los secretos de Streamlit.")
    except Exception as e:
        st.error(f"❌ Error al subir a GitHub: {str(e)}")

if st.button("🚀 Enviar Pedido y Generar Comprobantes", type="primary"):
    if not mercado:
        st.error("Por favor, ingresa el nombre del MERCADO antes de enviar.")
    else:
        with st.spinner("Actualizando Google Sheets y generando comprobantes..."):
            try:
                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive.file"
                ]
                creds_dict = dict(st.secrets["gcp_service_account"])
                creds = Credentials.from_service_account_info(creds_dict)
                creds = creds.with_scopes(scopes)
                
                client = gspread.authorize(creds)
                SPREADSHEET_ID = "1ojTp9-fcSIJRUHVlIcL7bQlVSaJ9vauIFYUvpz1lo4w"
                spreadsheet = client.open_by_key(SPREADSHEET_ID)
                sheet = spreadsheet.worksheet("Matriz de Pedidos")
                
                sheet.update_acell('C2', str(mercado))
                sheet.update_acell('C3', str(fecha_pedido))
                
                values_to_update = []
                for index, row in edited_df.iterrows():
                    values_to_update.append([
                        str(row["PRODUCTO"]), 
                        int(row["EXISTENCIA"]), 
                        int(row["CAMBIOS"]), 
                        int(row["PEDIDO"]), 
                        int(row["SUGERIDO"])
                    ])
                
                sheet.update('B6:F50', values_to_update)
                
                st.success("¡Pedido guardado con éxito en Google Sheets!")
                
            except Exception as e:
                if "Response [200]" in str(e):
                    st.success("¡Pedido guardado con éxito en Google Sheets!")
                else:
                    st.error(f"Error al conectar con Google Sheets: {str(e)}")

            vend_clean = vendedor.strip().replace(" ", "_") if vendedor else "SinVendedor"
            merc_clean = mercado.strip().replace(" ", "_")
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_pdf = f"Pedido_{merc_clean}_{vend_clean}_{timestamp_str}.pdf"
            nombre_csv = f"Pedido_{merc_clean}_{vend_clean}_{timestamp_str}.csv"
            
            pdf_buffer = generar_pdf(edited_df, mercado, fecha_pedido, vendedor)
            csv_bytes = convertir_df_a_csv(edited_df)
            
            guardar_pdf_en_github(pdf_buffer, nombre_pdf)
            
            texto_wsp = construir_mensaje_whatsapp(mercado, fecha_pedido, vendedor, edited_df)
            whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(texto_wsp)}"
            
            col_b1, col_b2, col_b3 = st.columns(3)
            
            with col_b1:
                st.download_button(
                    label="📥 Descargar PDF",
                    data=pdf_buffer,
                    file_name=nombre_pdf,
                    mime="application/pdf",
                    use_container_width=True
                )
                
            with col_b2:
                st.download_button(
                    label="📊 Descargar CSV",
                    data=csv_bytes,
                    file_name=nombre_csv,
                    mime="text/csv",
                    use_container_width=True
                )
                
            with col_b3:
                st.link_button(
                    label="💬 Enviar por WhatsApp",
                    url=whatsapp_url,
                    use_container_width=True
                )
