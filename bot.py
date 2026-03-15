"""
bot.py — Gestión principal del bot de Telegram
Bot jurídico penal español
"""

import logging
from telegram import Update, constants
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)
from config import TELEGRAM_TOKEN
from claude import generar_escrito
from session_manager import SessionManager
from router import detectar_intencion

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

session_manager = SessionManager()

BIENVENIDA = """
⚖️ *Bot Jurídico Penal Español*

Soy tu asistente especializado en derecho penal. Puedo ayudarte a:

• *Redactar* escritos procesales penales
• *Mejorar* escritos existentes
• *Sugerir* argumentos jurídicos

*Ejemplos de uso:*
— "Redacta un escrito solicitando el cotejo de teléfonos móviles"
— "Mejora este escrito: [pega tu escrito]"
— "Sugiere argumentos para alegar nulidad de una intervención telefónica"

¿En qué puedo ayudarte?
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /start"""
    user_id = update.effective_user.id
    session_manager.crear_sesion(user_id)
    await update.message.reply_text(
        BIENVENIDA,
        parse_mode=constants.ParseMode.MARKDOWN,
    )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /ayuda"""
    texto = """
*Comandos disponibles:*

/start — Iniciar el bot
/ayuda — Ver esta ayuda
/nueva — Iniciar nueva consulta (limpia el historial)
/datos — Configurar datos del escrito (abogado, procurador, etc.)

*Tipos de solicitudes:*
— Redactar escritos procesales
— Mejorar escritos existentes  
— Sugerir argumentos jurídicos
— Analizar diligencias

*Consejo:* Cuanta más información me des sobre el caso, 
mejor será el escrito generado.
    """
    await update.message.reply_text(texto, parse_mode=constants.ParseMode.MARKDOWN)

async def nueva_sesion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /nueva — limpia el historial"""
    user_id = update.effective_user.id
    session_manager.limpiar_sesion(user_id)
    await update.message.reply_text(
        "✅ Sesión reiniciada. ¿Cuál es tu nueva consulta?"
    )

async def configurar_datos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /datos — configurar datos del letrado"""
    user_id = update.effective_user.id
    texto = """
*Configuración de datos del escrito*

Envíame los datos en este formato:

```
ABOGADO: Nombre completo
COLEGIADO: Número de colegiado
COLEGIO: Ciudad del colegio
PROCURADOR: Nombre (o "ninguno")
```

Estos datos se usarán automáticamente en todos tus escritos.
    """
    await update.message.reply_text(texto, parse_mode=constants.ParseMode.MARKDOWN)
    context.user_data["esperando_datos"] = True

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja mensajes de texto del usuario"""
    user_id = update.effective_user.id
    mensaje = update.message.text

    # Si el usuario está configurando datos del letrado
    if context.user_data.get("esperando_datos"):
        _procesar_datos_letrado(user_id, mensaje, context)
        await update.message.reply_text(
            "✅ Datos guardados correctamente. Ya puedes hacer tu consulta."
        )
        return

    # Indicador de "escribiendo..."
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=constants.ChatAction.TYPING,
    )

    # Detectar intención del usuario
    intencion = detectar_intencion(mensaje)
    logger.info(f"Usuario {user_id} — Intención detectada: {intencion}")

    # Obtener historial de sesión
    historial = session_manager.obtener_historial(user_id)
    datos_letrado = session_manager.obtener_datos_letrado(user_id)

    try:
        # Enviar mensaje de espera para escritos largos
        msg_espera = await update.message.reply_text(
            "⚖️ Analizando tu solicitud y redactando el escrito...\n"
            "_Esto puede tardar unos segundos._",
            parse_mode=constants.ParseMode.MARKDOWN,
        )

        # Generar respuesta con Claude
        respuesta = await generar_escrito(
            consulta=mensaje,
            intencion=intencion,
            historial=historial,
            datos_letrado=datos_letrado,
        )

        # Actualizar historial
        session_manager.actualizar_historial(user_id, mensaje, respuesta)

        # Eliminar mensaje de espera
        await msg_espera.delete()

        # Enviar respuesta (Telegram tiene límite de 4096 caracteres)
        await _enviar_respuesta_larga(update, respuesta)

    except Exception as e:
        logger.error(f"Error generando escrito: {e}")
        await update.message.reply_text(
            "❌ Ha ocurrido un error al generar el escrito. "
            "Por favor, inténtalo de nuevo o simplifica tu consulta."
        )

async def _enviar_respuesta_larga(update: Update, texto: str) -> None:
    """Divide respuestas largas en múltiples mensajes"""
    LIMITE = 4000  # Margen de seguridad bajo el límite de Telegram
    
    if len(texto) <= LIMITE:
        await update.message.reply_text(texto)
        return

    # Dividir por párrafos respetando la estructura del escrito
    partes = []
    parte_actual = ""
    
    for linea in texto.split("\n"):
        if len(parte_actual) + len(linea) + 1 > LIMITE:
            partes.append(parte_actual)
            parte_actual = linea + "\n"
        else:
            parte_actual += linea + "\n"
    
    if parte_actual:
        partes.append(parte_actual)

    total = len(partes)
    for i, parte in enumerate(partes, 1):
        prefijo = f"[{i}/{total}]\n" if total > 1 else ""
        await update.message.reply_text(prefijo + parte)

def _procesar_datos_letrado(user_id: int, mensaje: str, context) -> None:
    """Extrae y guarda los datos del letrado del mensaje"""
    datos = {}
    for linea in mensaje.split("\n"):
        if ":" in linea:
            clave, _, valor = linea.partition(":")
            clave = clave.strip().upper()
            valor = valor.strip()
            if clave in ("ABOGADO", "COLEGIADO", "COLEGIO", "PROCURADOR"):
                datos[clave.lower()] = valor
    
    session_manager.guardar_datos_letrado(user_id, datos)
    context.user_data["esperando_datos"] = False

def main() -> None:
    """Punto de entrada principal"""
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CommandHandler("nueva", nueva_sesion))
    app.add_handler(CommandHandler("datos", configurar_datos))

    # Mensajes de texto
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    logger.info("Bot jurídico iniciado. Esperando mensajes...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
