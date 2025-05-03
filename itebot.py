
#TOKEN = "7042424790:AAH6_LDnvaaTu-bNO2cE2cBPjb91IFb3nNk"  # token real aquí  alinfoto


# Importamos los módulos necesarios
import zipfile  # Para crear archivos ZIP
import io       # Para manejar datos en memoria como archivos
import os       # Para interactuar con el sistema de archivos
import shutil   # Para operaciones con archivos y directorios
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup  # Componentes de la API de Telegram
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes  # Extensiones para manejar eventos de Telegram

# Token del bot de Telegram
TOKEN = "7042424790:AAH6_LDnvaaTu-bNO2cE2cBPjb91IFb3nNk"  # 🔐 ¡Debes proteger este token!

# Carpeta base donde se almacenarán los archivos de los usuarios
BASE_PATH = "fotos"
# Archivo donde se guardan los datos de los usuarios registrados
USUARIOS_FILE = "usuarios.txt"

# --- FUNCIONES DE USUARIOS ---

# Carga los usuarios guardados en el archivo de texto
def cargar_usuarios():
    usuarios = {}
    if os.path.exists(USUARIOS_FILE):  # Verifica si existe el archivo
        with open(USUARIOS_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(":")  # Divide línea por ":"
                if len(parts) == 3:
                    user_id, clave, carpeta = parts
                    usuarios[int(user_id)] = {"clave": clave, "carpeta": carpeta}
    return usuarios

# Guarda un nuevo usuario en el archivo
def guardar_usuario(user_id, clave, carpeta):
    with open(USUARIOS_FILE, "a") as f:
        f.write(f"{user_id}:{clave}:{carpeta}\n")

# Diccionario global con los usuarios cargados
USUARIOS = cargar_usuarios()

# --- FUNCIÓN: MOSTRAR MENÚ DE ARCHIVOS ---

# Muestra el menú de archivos disponibles en la carpeta del usuario
async def mostrar_menu_archivos(user_id, context, chat_id):
    carpeta = USUARIOS[user_id]["carpeta"]
    carpeta_path = os.path.join(BASE_PATH, carpeta)

    if not os.path.exists(carpeta_path):  # Si la carpeta no existe
        await context.bot.send_message(chat_id=chat_id, text="⚠️ No se encontró tu carpeta.")
        return

    archivos = os.listdir(carpeta_path)  # Lista los archivos
    if not archivos:
        await context.bot.send_message(chat_id=chat_id, text="📂 Tu carpeta está vacía.")
        return

    # Crea botones para cada archivo
    keyboard = [[InlineKeyboardButton(f"📁 {archivo}", callback_data=f"{carpeta}|{archivo}")] for archivo in archivos]
    keyboard.append([InlineKeyboardButton("🔒 Cerrar sesión", callback_data="cerrar_sesion")])

    # Envía el menú con botones
    await context.bot.send_message(
        chat_id=chat_id,
        text="Selecciona un archivo para descargar:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# --- HANDLER: INICIO /start ---

# Maneja el comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in USUARIOS:  # Si el usuario es nuevo
        await update.message.reply_text("👋 Bienvenido. Ingresa el *nombre que deseas para tu carpeta:*", parse_mode="Markdown")
        context.user_data["nuevo_registro"] = True
        return

    if not context.user_data.get("logueado"):  # Si no está logueado aún
        await update.message.reply_text("🔐 Por favor, ingresa tu contraseña para acceder.")
        context.user_data["esperando_password"] = True
        return

    # Ya está registrado y logueado
    await mostrar_menu_archivos(user_id, context, update.effective_chat.id)

# --- HANDLER: RESPUESTAS DE TEXTO ---

# Procesa mensajes de texto del usuario
async def procesar_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    texto = update.message.text.strip()

    # Si está creando nueva cuenta
    if context.user_data.get("nuevo_registro"):
        context.user_data["nombre_carpeta"] = texto
        await update.message.reply_text("🛡️ Ahora escribe la contraseña que deseas para esta carpeta:")
        context.user_data["esperando_clave_nueva"] = True
        context.user_data["nuevo_registro"] = False
        return

    # Si está esperando la clave para registrar la nueva cuenta
    elif context.user_data.get("esperando_clave_nueva"):
        nombre_carpeta = context.user_data["nombre_carpeta"]
        clave = texto

        # Guardamos el nuevo usuario
        USUARIOS[user_id] = {"clave": clave, "carpeta": nombre_carpeta}
        guardar_usuario(user_id, clave, nombre_carpeta)

        carpeta_path = os.path.join(BASE_PATH, nombre_carpeta)
        os.makedirs(carpeta_path, exist_ok=True)  # Crea la carpeta si no existe

        await update.message.reply_text("✅ Registro exitoso. Mostrando archivos...")
        context.user_data.clear()
        context.user_data["logueado"] = True
        await mostrar_menu_archivos(user_id, context, update.effective_chat.id)
        return

    # Si está ingresando la clave para iniciar sesión
    elif context.user_data.get("esperando_password"):
        clave_correcta = USUARIOS[user_id]["clave"]
        if texto == clave_correcta:
            context.user_data["logueado"] = True
            await update.message.reply_text("✅ Contraseña correcta. Mostrando archivos...")
            await mostrar_menu_archivos(user_id, context, update.effective_chat.id)
        else:
            await update.message.reply_text("❌ Contraseña incorrecta.")
        context.user_data["esperando_password"] = False
        return

# --- HANDLER: SELECCIÓN DE ARCHIVOS / CERRAR SESIÓN ---

# Maneja los botones de selección (callback queries)
async def manejar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cerrar_sesion":  # Si se presionó "Cerrar sesión"
        context.user_data.clear()
        await query.edit_message_text("🔒 Has cerrado sesión. Usa /start para iniciar sesión de nuevo.")
        return

    # Se presionó un archivo o carpeta
    carpeta, archivo = query.data.split("|")
    archivo_path = os.path.join(BASE_PATH, carpeta, archivo)

    if not os.path.exists(archivo_path):  # Verifica que el archivo exista
        await query.edit_message_text("❌ Archivo no encontrado.")
        return

    if os.path.isdir(archivo_path):  # Si es una carpeta, la comprime en ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(archivo_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, archivo_path)
                    zipf.write(full_path, arcname)
        zip_buffer.seek(0)

        await context.bot.send_document(
            chat_id=query.from_user.id,
            document=zip_buffer,
            filename=f"{archivo}.zip"
        )
        await query.edit_message_text(f"📦 Carpeta *{archivo}* enviada como ZIP.", parse_mode="Markdown")
    else:  # Si es un archivo normal, lo envía directamente
        with open(archivo_path, "rb") as f:
            await context.bot.send_document(chat_id=query.from_user.id, document=f)
        await query.edit_message_text(f"📄 Archivo *{archivo}* enviado.", parse_mode="Markdown")

# --- MAIN ---

# Punto de entrada del bot
if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()  # Crea la aplicación del bot

    # Registramos los handlers para comandos, botones y texto
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(manejar_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_texto))

    print("🤖 Bot corriendo...")
    app.run_polling()  # Inicia el bot en modo escucha continua