import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool
from crewai import LLM  

# 1. Cargar llaves del archivo .env
load_dotenv()

# --- AGREGA ESTAS LÍNEAS DE PRUEBA ---
print(f"Ruta actual de ejecución: {os.getcwd()}")
print(f"¿Existe el archivo .env?: {os.path.exists('.env')}")
print(f"Correo detectado: {os.getenv('MI_CORREO')}")

# 2. Configurar el cerebro (Gemini) y la herramienta de búsqueda
llm_gratis = LLM(
    model="gemini/gemini-2.5-flash",  
    api_key=os.getenv("GEMINI_API_KEY")
)

search_tool = SerperDevTool()

# 3. DEFINICIÓN DE AGENTES
investigador = Agent(
    role='Investigador de Tecnología',
    goal='Buscar las noticias más recientes y relevantes sobre desarrollo de software de hoy.',
    backstory='Eres un experto en rastrear la web, Hacker News y blogs técnicos en busca de lanzamientos y noticias críticas.',
    tools=[search_tool],
    llm=llm_gratis, 
    verbose=True
)

editor = Agent(
    role='Editor Senior de Software',
    goal='Filtrar, traducir y formatear las noticias tecnológicas para un desarrollador.',
    backstory='Eres un Ingeniero de Software experimentado. Sabes distinguir el hype comercial de las noticias que realmente impactan (actualizaciones de frameworks, arquitectura, optimización).',
    llm=llm_gratis,
    verbose=True
)

# 4. DEFINICIÓN DE TAREAS
tarea_busqueda = Task(
    description='Busca las 10 noticias más importantes de hoy sobre ingeniería de software, nuevas herramientas y frameworks. Obtén el título y la URL.',
    expected_output='Una lista con los titulares y sus respectivos enlaces.',
    agent=investigador
)

tarea_edicion = Task(
    description='Recibe las noticias del investigador. Filtrar y deja solo las 5 más relevantes. Traduce los titulares al español, añade un mini resumen de una línea en español y dale formato HTML limpio y estético para un correo.',
    expected_output='Un bloque de código HTML limpio con el boletín listo.',
    agent=editor
)

# 5. CREAR LA TRIPULACIÓN
boletin_crew = Crew(
    agents=[investigador, editor],
    tasks=[tarea_busqueda, tarea_edicion],
    process=Process.sequential 
)

# 6. FUNCIÓN PARA ENVIAR EL CORREO VIA SMTP
def enviar_boletin_por_correo(contenido_html):
    remitente = os.getenv("MI_CORREO")
    password = os.getenv("MI_APP_PASSWORD")
    destinatario = os.getenv("MI_CORREO") # Te lo envías a ti mismo
    
    if not remitente or not password:
        print("❌ Error: Credenciales de correo no encontradas en el archivo .env")
        return

    print("📧 Preparando el envío del correo...")
    
    # Crear el mensaje
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "📰 Tech Daily: Tu dosis diaria de desarrollo"
    msg['From'] = remitente
    msg['To'] = destinatario
    
    # Inyectar el HTML generado por el agente
    msg.attach(MIMEText(contenido_html, 'html'))
    
    try:
        # Conexión al servidor SMTP de Gmail (Puerto 587 para TLS)
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls() # Cifrado seguro
            server.login(remitente, password)
            server.sendmail(remitente, destinatario, msg.as_string())
        print("🚀 ¡Boletín enviado con éxito a tu bandeja de entrada!")
    except Exception as e:
        print(f"❌ No se pudo enviar el correo: {e}")

# EJECUTAR EL FLUJO
if __name__ == "__main__":
    print("🤖 ¡Iniciando el agente recolector de noticias!")
    try:
        # El agente genera el HTML
        resultado_agente = boletin_crew.kickoff()
        
        # CrewAI devuelve un objeto interno, lo convertimos a string puro
        contenido_html = str(resultado_agente)
        
        # Enviamos el resultado por correo
        enviar_boletin_por_correo(contenido_html)
        
    except Exception as e:
        print(f"Ocurrió un problema durante la ejecución: {e}")