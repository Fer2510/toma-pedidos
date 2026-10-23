import json # Asegúrate de importar json si no lo tienes

# Función para guardar en Google Sheets
def guardar_en_google_sheets(df_enviado, mercado_val, fecha_val):
    try:
        scope = ["https://www.spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Leemos el secreto como un diccionario directo o JSON
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        spreadsheet = client.open("Consolidado_Pedidos_Google_Forms")
        sheet = spreadsheet.get_worksheet(0)
        
        sheet.update('C2', [[mercado_val]])
        sheet.update('C3', [[str(fecha_val)]])
        
        filas_a_guardar = []
        for index, row in df_enviado.iterrows():
            filas_a_guardar.append([
                row["PRODUCTO"], 
                int(row["EXISTENCIA"]), 
                int(row["CAMBIOS"]), 
                int(row["PEDIDO"]), 
                int(row["SUGERIDO"])
            ])
        
        sheet.update(f'B6:F{5+len(filas_a_guardar)}', filas_a_guardar)
        return True
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return False
