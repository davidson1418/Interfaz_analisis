import tkinter as tk
import customtkinter as ctk
import pandas as pd
from tkinter import messagebox
from PIL import Image, ImageTk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from fpdf import FPDF
import folium
import webbrowser
import os
import subprocess

# Configuración de estilo
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Credenciales de prueba
auth_users = {"admin": "1234", "usuario": "clave"}

# Splash de carga
def show_splash():
    """Display a temporary splash screen while the app loads."""
    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.geometry("400x400+450+150")
    splash.configure(bg="black")
    try:
        img = Image.open("logo_autodema.png").resize((250,250))
        tkimg = ImageTk.PhotoImage(img)
        lbl = tk.Label(splash, image=tkimg, bg="black")
        lbl.image = tkimg
        lbl.pack(pady=20)
    except:
        pass
    lbl_text = tk.Label(splash, text="Cargando aplicación...", fg="white", bg="black", font=("Arial",14))
    lbl_text.pack()
    splash.after(3000, splash.destroy)
    splash.mainloop()

class App:
    def __init__(self, csv_path="simulacion.csv"):
        """Load data from *csv_path* and launch the login window."""
        # Carga y validación de datos
        try:
            self.df = pd.read_csv(csv_path, encoding='latin-1')
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer '{csv_path}': {e}")
            return
        cols = ['Especie cultivada','Variedad','Edad promedio (años)',
                'Uso de fertilizantes','Latitud','Longitud','Altitud (msnm)',
                'Area cultivada (ha)','Produccion anual (toneladas)','ID Parcela']
        missing = [c for c in cols if c not in self.df.columns]
        if missing:
            messagebox.showerror("Error", f"Faltan columnas: {missing}")
            return
        self.especies = sorted(self.df['Especie cultivada'].dropna().unique())
        show_splash()
        self.show_login()

    def show_login(self):
        """Display the login form for the user."""
        win = ctk.CTk()
        win.title("Login")
        win.geometry("300x200")
        ctk.CTkLabel(win, text="Usuario:").pack(pady=(20,5))
        self.user = ctk.CTkEntry(win)
        self.user.pack(pady=5)
        ctk.CTkLabel(win, text="Clave:").pack(pady=5)
        self.pwd = ctk.CTkEntry(win, show="*")
        self.pwd.pack(pady=5)
        ctk.CTkButton(win, text="Ingresar", command=lambda:self.check_login(win)).pack(pady=20)
        win.mainloop()

    def check_login(self, win):
        """Validate credentials and open the main window if correct."""
        if auth_users.get(self.user.get()) == self.pwd.get():
            win.destroy()
            self.show_main()
        else:
            messagebox.showerror("Acceso denegado", "Usuario o clave incorrectos.")

    def show_main(self):
        """Create the main interface used to filter and visualize data."""
        self.main = ctk.CTk()
        self.main.title("Consulta de Cultivos")
        self.main.geometry("800x800")
        # Combobox especie
        ctk.CTkLabel(self.main, text="Seleccione especie:").pack(pady=(20,5))
        self.cmb_e = ctk.CTkComboBox(self.main, values=["Todas"]+self.especies, command=self.update_vars)
        self.cmb_e.set("Todas")
        self.cmb_e.pack(pady=5)
        # Combobox variedad
        ctk.CTkLabel(self.main, text="Seleccione variedad:").pack(pady=(10,5))
        allv = sorted(self.df['Variedad'].dropna().unique())
        self.cmb_v = ctk.CTkComboBox(self.main, values=["Todas"]+allv)
        self.cmb_v.set("Todas")
        self.cmb_v.pack(pady=5)
        # Botones
        ctk.CTkButton(self.main, text="Consulta", command=self.mostrar_consulta).pack(pady=10)
        ops = [("Ver Edad",self.grafico_edad), ("Ver Fertilizantes",self.grafico_fertilizantes),
               ("Ver Area/Produccion",self.datos_area), ("Ver Mapa",self.ver_mapa),
               ("Crear PDF",self.crear_pdf)]
        for txt, fn in ops:
            ctk.CTkButton(self.main, text=txt, command=fn).pack(pady=5)
        self.lbl_info = ctk.CTkLabel(self.main, text="", anchor='w', justify='left')
        self.lbl_info.pack(pady=10,padx=20,fill='both')
        self.main.mainloop()

    def update_vars(self, esp):
        """Update variety options when the species combobox changes."""
        if esp=="Todas":
            vals = sorted(self.df['Variedad'].dropna().unique())
        else:
            vals = sorted(self.df.loc[self.df['Especie cultivada']==esp,'Variedad'].dropna().unique())
        self.cmb_v.configure(values=["Todas"]+vals)
        self.cmb_v.set("Todas")

    def filtro(self):
        """Return the DataFrame filtered by the current selections."""
        df = self.df.copy()
        e,v = self.cmb_e.get(), self.cmb_v.get()
        if e!="Todas": df = df[df['Especie cultivada']==e]
        if v!="Todas": df = df[df['Variedad']==v]
        self.df_consulta = df
        return df

    def show_matplotlib_plot(self, fig, title):
        """Display *fig* in a pop-up window with *title*."""
        win = ctk.CTkToplevel()
        win.title(title)
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def mostrar_consulta(self):
        """Generate summary charts and text for the filtered records."""
        df = self.filtro()
        if df.empty:
            self.lbl_info.configure(text="Sin datos.")
            return
        # Gráfico de barras area por parcela
        fig = Figure(figsize=(6,4))
        ax = fig.add_subplot(111)
        ax.bar(df['ID Parcela'], df['Area cultivada (ha)'], color='skyblue')
        ax.set_title('Area cultivada por parcela')
        ax.set_xlabel('ID Parcela')
        ax.set_ylabel('Area (ha)')
        fig.tight_layout()
        fig.savefig('consulta.png')
        self.show_matplotlib_plot(fig, 'Grafico Consulta')
        # Resumen
        area = df['Area cultivada (ha)'].sum()
        prod = df['Produccion anual (toneladas)'].sum()
        fert = df['Uso de fertilizantes'].value_counts().to_dict()
        txt = f"Hectareas cultivadas: {area:.2f} ha\n"+f"Produccion anual: {prod:.2f} ton\n"+f"Fertilizantes usados: {fert}"
        self.lbl_info.configure(text=txt)

    def grafico_edad(self):
        """Show a histogram of tree ages for the filtered data."""
        df = self.filtro()
        if df.empty:
            messagebox.showinfo("Info","Sin datos de edad.")
            return
        fig = Figure(figsize=(6,4))
        ax = fig.add_subplot(111)
        ax.hist(df['Edad promedio (años)'].dropna(), bins=10, color='lightgreen', edgecolor='black')
        ax.set_title('Distribucion de edades')
        ax.set_xlabel('Edad (años)')
        ax.set_ylabel('Frecuencia')
        fig.tight_layout()
        fig.savefig('edad.png')
        self.show_matplotlib_plot(fig, 'Grafico Edad')

    def grafico_fertilizantes(self):
        """Display a pie chart of fertilizer usage."""
        df = self.filtro()
        if df.empty:
            messagebox.showinfo("Info","Sin datos de fertilizantes.")
            return
        cnt = df['Uso de fertilizantes'].value_counts()
        fig = Figure(figsize=(6,4))
        ax = fig.add_subplot(111)
        ax.pie(cnt.values, labels=cnt.index, autopct='%1.1f%%')
        ax.set_title('Uso de fertilizantes')
        fig.tight_layout()
        fig.savefig('fert.png')
        self.show_matplotlib_plot(fig, 'Grafico Fertilizantes')

    def datos_area(self):
        """Plot total cultivated area versus annual production."""
        df = self.filtro()
        if df.empty:
            messagebox.showinfo("Info","Sin datos area/produccion.")
            return
        area = df['Area cultivada (ha)'].sum()
        prod = df['Produccion anual (toneladas)'].sum()
        fig = Figure(figsize=(6,4))
        ax = fig.add_subplot(111)
        ax.bar(['Area (ha)','Produccion (t)'], [area, prod], color=['orange','purple'])
        ax.set_title('Area vs Produccion')
        ax.set_ylabel('Valor')
        fig.tight_layout()
        fig.savefig('area.png')
        self.show_matplotlib_plot(fig, 'Grafico Area vs Produccion')

    def ver_mapa(self):
        """Open an interactive map showing plot locations."""
        df = self.filtro()
        mapa = folium.Map(location=[-16.27,-72.15], zoom_start=12)
        for _,r in df.iterrows():
            folium.Marker([r['Latitud'],r['Longitud']], popup=f"{r['ID Parcela']} - {r['Especie cultivada']}").add_to(mapa)
        mapa.save('mapa.html')
        webbrowser.open('mapa.html')
        try:
            subprocess.run(['wkhtmltoimage', 'mapa.html', 'mapa.png'], check=True)
        except FileNotFoundError:
            messagebox.showwarning('wkhtmltoimage',
                                   'wkhtmltoimage no est\xC3\xA1 instalado. El mapa no se export\xC3\xB3 a imagen.')
            return
        except subprocess.CalledProcessError:
            messagebox.showwarning('wkhtmltoimage',
                                   'No se pudo convertir mapa.html a imagen.')
            return
        img = Image.open('mapa.png')
        tkimg = ImageTk.PhotoImage(img.resize((600,400)))
        win = ctk.CTkToplevel()
        win.title('Mapa Zona')
        lbl = ctk.CTkLabel(win, image=tkimg, text='')
        lbl.image = tkimg
        lbl.pack(padx=10, pady=10)

    def crear_pdf(self):
        """Generate a consolidated PDF report of the current query."""
        df = getattr(self,'df_consulta',pd.DataFrame())
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial','B',14)
        pdf.cell(0,10,'Reporte Consolidado',ln=1)
        pdf.set_font('Arial','',12)
        pdf.cell(0,8,f"Especie: {self.cmb_e.get()}, Variedad: {self.cmb_v.get()}",ln=1)
        # Grafico consulta
        if os.path.exists('consulta.png'): pdf.ln(5); pdf.image('consulta.png',w=160)
        # Tabla parcelas
        df_tab = df[['ID Parcela','Latitud','Longitud','Altitud (msnm)']].dropna()
        if not df_tab.empty:
            pdf.ln(5); pdf.set_font('Arial','B',12)
            for col in ['ID Parcela','Latitud','Longitud','Altitud (msnm)']: pdf.cell(40,8,col,1)
            pdf.ln(); pdf.set_font('Arial','',10)
            for _,row in df_tab.iterrows():
                pdf.cell(40,6,str(row['ID Parcela']),1); pdf.cell(40,6,f"{row['Latitud']:.6f}",1)
                pdf.cell(40,6,f"{row['Longitud']:.6f}",1); pdf.cell(40,6,str(row['Altitud (msnm)']),1); pdf.ln()
        # Otras imagenes
        for img in ['edad.png','fert.png','area.png','mapa.png']:
            if os.path.exists(img): pdf.ln(5); pdf.image(img,w=160)
        pdf.output('reporte_consolidado.pdf')
        webbrowser.open('reporte_consolidado.pdf')

if __name__=='__main__':
    App()
