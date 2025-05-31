# telegram_bot
📸 FotoBot – Bot de Telegram para Gestión Segura de Archivos Personales

FotoBot es un bot de Telegram diseñado para ofrecer a cada usuario un espacio privado donde puede acceder y descargar sus sesiones fotograficas, organizados en carpetas individuales. El acceso está protegido por contraseña y los datos de los usuarios se almacenan de forma segura utilizando una base de datos SQLite y contraseñas encriptadas con SHA-256.

🔐 Características principales

    🔑 Inicio de sesión protegido por contraseña

    📁 Carpetas personales por usuario

    🔄 Visualización de archivos disponibles

    🗜️ Compresión automática de carpetas en ZIP

    🧹 Eliminación automática de mensajes sensibles (como contraseñas)

    🔒 Opción para cerrar sesión con un solo clic

    🗃️ Base de datos SQLite para guardar usuarios de forma segura

    🔐 Contraseñas almacenadas en hash (SHA-256)



🧾 Estructura del sistema

    Cada usuario tiene una carpeta exclusiva dentro del directorio /fotos/.

    Las contraseñas y rutas de carpetas se almacenan en usuarios.db.

    El bot elimina automáticamente mensajes que contienen contraseñas para mayor seguridad.

    Los archivos y carpetas pueden descargarse individualmente o comprimidos en ZIP.



🛠️ Requisitos

    Python 3.10 o superior

    Librerías:

        python-telegram-bot

        python-dotenv

        sqlite3 (viene incluida con Python)

        hashlib (módulo estándar)



🚀 Uso

    Clona o descarga el repositorio.

    Crea un archivo .env en la raíz del proyecto con el siguiente contenido:

    token=TU_TOKEN_DE_BOT_DE_TELEGRAM


    Ejecuta el bot con:

    python itebot.py
    