"""
config.py — Configuración y claves API
IMPORTANTE: En producción, usar variables de entorno (Railway las gestiona)
"""

import os

# Telegram
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")

# Claude (Anthropic)
CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-opus-4-5"  # Modelo más capaz para escritos jurídicos

# Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Voyage AI (para embeddings — opcional en v1)
VOYAGE_API_KEY = os.environ.get("VOYAGE_API_KEY", "")

# Validación de configuración
def validar_config():
    """Verifica que todas las claves necesarias estén configuradas"""
    requeridas = {
        "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
        "ANTHROPIC_API_KEY": CLAUDE_API_KEY,
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_KEY": SUPABASE_KEY,
    }
    
    faltantes = [k for k, v in requeridas.items() if not v]
    
    if faltantes:
        raise ValueError(
            f"Variables de entorno faltantes: {', '.join(faltantes)}\n"
            "Configúralas en Railway o en el archivo .env"
        )
