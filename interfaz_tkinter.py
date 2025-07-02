import customtkinter as ctk
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import folium
import os
import webbrowser
from PIL import Image, ImageTk
from tkinter import messagebox

# Configuración de la app en modo oscuro y moderno
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

usuarios = {"admin": "1234", "usuario": "clave"}

try:
    df = pd.read_csv("simulacion.csv")
    especies = sorted(df['Especie cultivada'].dropna().unique())
    variedades_por_especie = {
        esp: sorted(
            df[df['Especie cultivada'] == esp]['Variedad'].dropna().unique()
        )
        for esp in especies
    }
except FileNotFoundError:
    messagebox.showerror(
        "Error", "El archivo 'simulacion.csv' no se encuentra."
    )
    exit()

def login():
    usuario = entry_usuario.get()
    clave = entry_clave.get()
    if usuario in usuarios and usuarios[usuario] == clave:
        login_window.destroy()
        abrir_principal()
    else:
        messagebox.showerror("Acceso denegado", "Usuario o clave incorrectos.")

def abrir_principal():
    def actualizar_variedades(event=None):
        especie = cmb_especie.get()
        if especie == "Todas":
            variedades = ["Todas"] + sorted(df['Variedad'].dropna().unique())
        else:
            variedades = ["Todas"] + variedades_por_especie.get(especie, [])
        cmb_variedad.configure(values=variedades)
        cmb_variedad.set("Todas")

    def consultar():
        especie = cmb_especie.get()
        variedad = cmb_variedad.get()
        resultados = df.copy()
        if especie != "Todas":
            resultados = resultados[resultados['Especie cultivada'] == especie]
        if variedad != "Todas":
            resultados = resultados[resultados['Variedad'] == variedad]

        resumen = {
            'num_arboles': int(resultados['Número de árboles'].sum()),
            'area_cultivada': resultados['Área cultivada (ha)'].sum(),
            'produccion': resultados['Producción anual (toneladas)'].sum(),
            'fertilizantes': resultados['Uso de fertilizantes'].value_counts().to_dict(),
            'parcelas': resultados[['ID Parcela', 'Latitud', 'Longitud']].dropna().values.tolist()
        }

        lbl_resultado.configure(text=f"Número de árboles: {resumen['num_arboles']}\nÁrea cultivada: {resumen['area_cultivada']:.2f} ha\nProducción anual: {resumen['produccion']:.2f} ton\nFertilizantes: {resumen['fertilizantes']}")

        def ver_grafico_edad(preview=True):
            fig = px.histogram(resultados, x='Edad promedio (años)', nbins=10, title='Distribución de edades')
            fig.write_image("grafico_edad.png")
            if preview:
                mostrar_imagen("grafico_edad.png", "Gráfico de Edades")

        def ver_grafico_fertilizantes(preview=True):
            fig = px.pie(resultados, names='Uso de fertilizantes', title='Uso de fertilizantes')
            fig.write_image("grafico_fertilizantes.png")
            if preview:
                mostrar_imagen("grafico_fertilizantes.png", "Gráfico de Fertilizantes")

        def ver_mapa():
            mapa = folium.Map(location=[-16.27, -72.15], zoom_start=12)
            for _, row in resultados.iterrows():
                if row['Latitud'] != 0 and row['Longitud'] != 0:
                    folium.Marker([row['Latitud'], row['Longitud']], popup=f"{row['ID Parcela']} - {row['Especie cultivada']} - {row['Variedad']}").add_to(mapa)
            mapa.save("mapa.html")
            webbrowser.open("mapa.html")
            # Generar imagen del mapa para el PDF
            os.system("wkhtmltoimage mapa.html mapa.png")

        def generar_pdf():
            # Generar gráficos sin mostrar ventanas
            ver_grafico_edad(preview=False)
            ver_grafico_fertilizantes(preview=False)

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'Reporte de Parcelas', ln=1)
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 10, f'Especie: {especie}', ln=1)
            pdf.cell(0, 10, f'Variedad: {variedad}', ln=1)
            pdf.cell(0, 10, f'Número de árboles: {resumen["num_arboles"]}', ln=1)
            pdf.cell(0, 10, f'Área cultivada: {resumen["area_cultivada"]:.2f} ha', ln=1)
            pdf.cell(0, 10, f'Producción anual: {resumen["produccion"]:.2f} ton', ln=1)
            pdf.cell(0, 10, 'Fertilizantes:', ln=1)
            for k, v in resumen['fertilizantes'].items():
                pdf.cell(0, 10, f'{k}: {v}', ln=1)

            pdf.ln(5)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'Parcelas:', ln=1)
            pdf.set_font('Arial', '', 10)
            pdf.cell(60, 10, 'ID Parcela', 1)
            pdf.cell(60, 10, 'Latitud', 1)
            pdf.cell(60, 10, 'Longitud', 1)
            pdf.ln()
            for parc in resumen['parcelas']:
                pdf.cell(60, 10, str(parc[0]), 1)
                pdf.cell(60, 10, str(parc[1]), 1)
                pdf.cell(60, 10, str(parc[2]), 1)
                pdf.ln()

            # Insertar siempre los gráficos generados
            pdf.image("grafico_edad.png", w=100)
            pdf.image("grafico_fertilizantes.png", w=100)
            if os.path.exists("mapa.png"):
                pdf.image("mapa.png", w=180)

            pdf.output("reporte.pdf")
            os.startfile("reporte.pdf")

        btn_grafico_edad.configure(command=ver_grafico_edad)
        btn_grafico_fertilizantes.configure(command=ver_grafico_fertilizantes)
        btn_mapa.configure(command=ver_mapa)
        btn_pdf.configure(command=generar_pdf)

    def mostrar_imagen(path, titulo):
        ventana = ctk.CTkToplevel()
        ventana.title(titulo)
        img = Image.open(path)
        img = img.resize((600, 400))
        img_tk = ImageTk.PhotoImage(img)
        label = ctk.CTkLabel(ventana, image=img_tk, text="")
        label.image = img_tk
        label.pack(padx=10, pady=10)

    app = ctk.CTk()
    app.title("Consulta de Cultivos - Modern UI")
    app.geometry("700x600")

    ctk.CTkLabel(app, text="Consulta de Cultivos", font=("Arial", 24)).pack(pady=10)

    cmb_especie = ctk.CTkComboBox(app, values=["Todas"] + especies, width=250)
    cmb_especie.set("Todas")
    cmb_especie.pack(pady=5)
    cmb_especie.bind("<<ComboboxSelected>>", actualizar_variedades)

    cmb_variedad = ctk.CTkComboBox(app, values=["Todas"], width=250)
    cmb_variedad.set("Todas")
    cmb_variedad.pack(pady=5)
    actualizar_variedades()

    ctk.CTkButton(app, text="Consultar", command=consultar).pack(pady=10)

    lbl_resultado = ctk.CTkLabel(app, text="Resultados aparecerán aquí", wraplength=600, justify="left")
    lbl_resultado.pack(pady=10)

    btn_grafico_edad = ctk.CTkButton(app, text="Ver gráfico de edades")
    btn_grafico_edad.pack(pady=5)

    btn_grafico_fertilizantes = ctk.CTkButton(app, text="Ver gráfico de fertilizantes")
    btn_grafico_fertilizantes.pack(pady=5)

    btn_mapa = ctk.CTkButton(app, text="Ver mapa de parcelas")
    btn_mapa.pack(pady=5)

    btn_pdf = ctk.CTkButton(app, text="Generar PDF")
    btn_pdf.pack(pady=10)

    app.mainloop()

# Login UI
login_window = ctk.CTk()
login_window.title("Login - Consulta de Cultivos")
login_window.geometry("300x220")

ctk.CTkLabel(login_window, text="Usuario:").pack(pady=5)
entry_usuario = ctk.CTkEntry(login_window)
entry_usuario.pack(pady=5)

ctk.CTkLabel(login_window, text="Clave:").pack(pady=5)
entry_clave = ctk.CTkEntry(login_window, show="*")
entry_clave.pack(pady=5)

ctk.CTkButton(login_window, text="Iniciar sesión", command=login).pack(pady=15)

login_window.mainloop()
