# --- IMPORTS ---
import zipfile
import io
import os
import shutil
import hashlib
import sqlite3
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURACIÓN ---
load_dotenv()
Token_telegram = os.environ['token']
BASE_PATH = "fotos"
DB_FILE = "usuarios.db"

# --- FUNCIONES DE SEGURIDAD (ENCRIPTACIÓN) ---

def encriptar_clave(clave):
    return hashlib.sha256(clave.encode()).hexdigest()

def verificar_clave(clave_ingresada, hash_guardado):
    return encriptar_clave(clave_ingresada) == hash_guardado

# --- BASE DE DATOS: INICIALIZAR Y GESTIONAR USUARIOS ---

def inicializar_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY,
            clave TEXT NOT NULL,
            carpeta TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def cargar_usuarios():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios")
    filas = cursor.fetchall()
    conn.close()
    return {fila[0]: {"clave": fila[1], "carpeta": fila[2]} for fila in filas}

def guardar_usuario(user_id, clave_hash, carpeta):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO usuarios (id, clave, carpeta) VALUES (?, ?, ?)", (user_id, clave_hash, carpeta))
    conn.commit()
    conn.close()

# Carga los usuarios existentes al iniciar
USUARIOS = cargar_usuarios()

# --- MOSTRAR ARCHIVOS (Actualizado para mostrar siempre botón de cerrar sesión) ---

async def mostrar_menu_archivos(user_id, context, chat_id):
    carpeta = USUARIOS[user_id]["carpeta"]
    carpeta_path = os.path.join(BASE_PATH, carpeta)

    texto_mensaje = "Selecciona un archivo para descargar:"
    keyboard = []

    # Si la carpeta no existe
    if not os.path.exists(carpeta_path):
        texto_mensaje = "⚠️ No se encontró tu carpeta. Puedes cerrar sesión."
    
    else:
        archivos = os.listdir(carpeta_path)
        if archivos:
            keyboard = [[InlineKeyboardButton(f"📁 {archivo}", callback_data=f"{carpeta}|{archivo}")] for archivo in archivos]
        else:
            texto_mensaje = "📂 Tu carpeta está vacía. Puedes cerrar sesión."

    # Agregar siempre el botón de cerrar sesión
    keyboard.append([InlineKeyboardButton("🔒 Cerrar sesión", callback_data="cerrar_sesion")])

    await context.bot.send_message(
        chat_id=chat_id,
        text=texto_mensaje,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# --- /start ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in USUARIOS:
        await update.message.reply_text("👋 Bienvenido. Ingresa el *nombre que deseas para tu carpeta:*", parse_mode="Markdown")
        context.user_data["nuevo_registro"] = True
        return

    if not context.user_data.get("logueado"):
        await update.message.reply_text("🔐 Por favor, ingresa tu contraseña para acceder.")
        context.user_data["esperando_password"] = True
        return

    await mostrar_menu_archivos(user_id, context, update.effective_chat.id)

# --- MENSAJES DE TEXTO ---

async def procesar_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    texto = update.message.text.strip()

    # NUEVA CUENTA
    if context.user_data.get("nuevo_registro"):
        context.user_data["nombre_carpeta"] = texto
        await update.message.reply_text("🛡️ Ahora escribe la contraseña que deseas para esta carpeta:")
        context.user_data["esperando_clave_nueva"] = True
        context.user_data["nuevo_registro"] = False
        return

    # REGISTRO DE CLAVE NUEVA
    elif context.user_data.get("esperando_clave_nueva"):
        await update.message.delete()

        nombre_carpeta = context.user_data["nombre_carpeta"]
        clave = texto
        clave_hash = encriptar_clave(clave)

        USUARIOS[user_id] = {"clave": clave_hash, "carpeta": nombre_carpeta}
        guardar_usuario(user_id, clave_hash, nombre_carpeta)

        carpeta_path = os.path.join(BASE_PATH, nombre_carpeta)
        os.makedirs(carpeta_path, exist_ok=True)

        await update.message.reply_text("✅ Registro exitoso. Mostrando archivos...")
        context.user_data.clear()
        context.user_data["logueado"] = True
        await mostrar_menu_archivos(user_id, context, update.effective_chat.id)
        return

    # INICIO DE SESIÓN
    elif context.user_data.get("esperando_password"):
        await update.message.delete()

        clave_correcta_hash = USUARIOS[user_id]["clave"]
        if verificar_clave(texto, clave_correcta_hash):
            context.user_data["logueado"] = True
            await update.message.reply_text("✅ Contraseña correcta. Mostrando archivos...")
            await mostrar_menu_archivos(user_id, context, update.effective_chat.id)
        else:
            await update.message.reply_text("❌ Contraseña incorrecta.")
        context.user_data["esperando_password"] = False
        return

# --- CALLBACKS (botones) ---

async def manejar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cerrar_sesion":
        context.user_data.clear()
        await query.edit_message_text("🔒 Has cerrado sesión. Usa /start para iniciar sesión de nuevo.")
        return

    carpeta, archivo = query.data.split("|")
    archivo_path = os.path.join(BASE_PATH, carpeta, archivo)

    if not os.path.exists(archivo_path):
        await query.edit_message_text("❌ Archivo no encontrado.")
        return

    if os.path.isdir(archivo_path):
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
    else:
        with open(archivo_path, "rb") as f:
            await context.bot.send_document(chat_id=query.from_user.id, document=f)
        await query.edit_message_text(f"📄 Archivo *{archivo}* enviado.", parse_mode="Markdown")

# --- MAIN ---

if __name__ == '__main__':
    inicializar_db()

    app = Application.builder().token(Token_telegram).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(manejar_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_texto))

    print("🤖 Bot corriendo...")
    app.run_polling()
