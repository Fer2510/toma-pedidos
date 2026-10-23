import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

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

# Función para generar el PDF en memoria
def generar_pdf(df_enviado, mercado_val, fecha_val):
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
    
    elements.append(Paragraph("<b>REPORTE DE PEDIDO - OFICINA PRINCIPAL</b>", title_style))
    elements.append(Paragraph(f"<b>Mercado / Zona:</b> {mercado_val}", normal_style))
    elements.append(Paragraph(f"<b>Fecha:</b> {str(fecha_val)}", normal_style))
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
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f1f8e9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#c8e6c9')),
        ('FONTSIZE', (0,1), (-1,-1), 9),
    ]))
    
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# Función mejorada con captura exacta de error para Drive
def subir_pdf_a_drive(pdf_buffer, nombre_archivo, creds):
    try:
        drive_service = build('drive', 'v3', credentials=creds)
        
        ID_CARPETA_DESTINO = "162rUBUDTFb04W4GJR-dDdX5-6M8w62jJ" 
        
        file_metadata = {
            'name': nombre_archivo,
            'mimeType': 'application/pdf',
            'parents': [ID_CARPETA_DESTINO]
        }
        
        media = MediaIoBaseUpload(pdf_buffer, mimetype='application/pdf', resumable=True)
        
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        return file.get('webViewLink'), None
    except Exception as e:
        return None, str(e)

if st.button("🚀 Enviar Pedido, Actualizar Hoja y Subir a Drive", type="primary"):
    if not mercado:
        st.error("Por favor, ingresa el nombre del MERCADO antes de enviar.")
    else:
        with st.spinner("Procesando y sincronizando con Google Cloud..."):
            try:
                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
                creds_dict = dict(st.secrets["gcp_service_account"])
                creds = Credentials.from_service_account_info(creds_dict)
                creds = creds.with_scopes(scopes)
                
                # 1. Actualizar Google Sheets
                client = gspread.authorize(creds)
                spreadsheet = client.open("Consolidado_Pedidos_Google_Forms")
                sheet = spreadsheet.worksheet("Matriz de Pedidos")
                
                sheet.update_cell(2, 3, str(mercado))
                sheet.update_cell(3, 3, str(fecha_pedido))
                
                for index, row in edited_df.iterrows():
                    fila = 6 + index
                    sheet.update(f'B{fila}:F{fila}', [[
                        str(row["PRODUCTO"]), 
                        int(row["EXISTENCIA"]), 
                        int(row["CAMBIOS"]), 
                        int(row["PEDIDO"]), 
                        int(row["SUGERIDO"])
                    ]])
                
# 2. Generar y subir el PDF automáticamente a Google Drive
                pdf_buffer = generar_pdf(edited_df, mercado, fecha_pedido)
                nombre_pdf = f"Pedido_{mercado}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                link_drive, error_drive = subir_pdf_a_drive(pdf_buffer, nombre_pdf, creds)
                
                st.success(f"¡Pedido para **{mercado}** guardado con éxito en la hoja de cálculo!")
                
                if link_drive:
                    st.markdown(f"📄 **PDF guardado en Google Drive correctamente.** [Ver documento en Drive]({link_drive})")
                else:
                    st.error(f"Detalle al subir a Drive: {error_drive}")
                
                # Botón de respaldo para descarga local
                pdf_buffer.seek(0)
                st.download_button(
                    label="📥 Descargar copia local del PDF",
                    data=pdf_buffer,
                    file_name=nombre_pdf,
                    mime="application/pdf"
                )
                
            except Exception as e:
                error_str = str(e)
                if "200" in error_str:
                    st.success(f"¡Pedido para **{mercado}** guardado con éxito en Google Sheets!")
                    pdf_buffer = generar_pdf(edited_df, mercado, fecha_pedido)
                    nombre_pdf = f"Pedido_{mercado}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    link_drive = subir_pdf_a_drive(pdf_buffer, nombre_pdf, creds)
                    if link_drive:
                        st.markdown(f"📄 **PDF guardado en Google Drive correctamente.** [Ver documento en Drive]({link_drive})")
                else:
                    st.error(f"Error al procesar: {error_str}")
