"""
session_manager.py — Gestión de sesiones por usuario de Telegram
"""

from datetime import datetime, timedelta
from typing import Optional
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Cache en memoria para sesiones activas (evitar queries constantes)
_cache_sesiones: dict = {}
_cache_datos_letrado: dict = {}


class SessionManager:
    
    MAX_HISTORIAL = 10  # Máximo de turnos a mantener
    TTL_HORAS = 24      # Tiempo de vida de la sesión

    def crear_sesion(self, user_id: int) -> None:
        """Crea o reinicia una sesión para el usuario"""
        _cache_sesiones[user_id] = []
        # Preservar datos del letrado entre sesiones
        
    def limpiar_sesion(self, user_id: int) -> None:
        """Limpia el historial de conversación"""
        _cache_sesiones[user_id] = []

    def obtener_historial(self, user_id: int) -> list:
        """Obtiene el historial de conversación del usuario"""
        return _cache_sesiones.get(user_id, [])

    def actualizar_historial(self, user_id: int, consulta: str, respuesta: str) -> None:
        """Añade un turno al historial"""
        if user_id not in _cache_sesiones:
            _cache_sesiones[user_id] = []
        
        _cache_sesiones[user_id].append({"role": "user", "content": consulta})
        _cache_sesiones[user_id].append({"role": "assistant", "content": respuesta})
        
        # Mantener solo los últimos N turnos
        if len(_cache_sesiones[user_id]) > self.MAX_HISTORIAL * 2:
            _cache_sesiones[user_id] = _cache_sesiones[user_id][-(self.MAX_HISTORIAL * 2):]

    def guardar_datos_letrado(self, user_id: int, datos: dict) -> None:
        """Guarda los datos del letrado (persisten entre sesiones)"""
        _cache_datos_letrado[user_id] = datos
        # También persistir en Supabase
        try:
            supabase.table("usuarios").upsert({
                "telegram_id": user_id,
                "datos_letrado": datos,
                "actualizado_en": datetime.now().isoformat(),
            }).execute()
        except Exception:
            pass  # Fallo silencioso — el cache en memoria sirve como backup

    def obtener_datos_letrado(self, user_id: int) -> dict:
        """Obtiene los datos del letrado"""
        if user_id in _cache_datos_letrado:
            return _cache_datos_letrado[user_id]
        
        # Intentar recuperar de Supabase
        try:
            resultado = supabase.table("usuarios")\
                .select("datos_letrado")\
                .eq("telegram_id", user_id)\
                .single()\
                .execute()
            
            if resultado.data:
                datos = resultado.data.get("datos_letrado", {})
                _cache_datos_letrado[user_id] = datos
                return datos
        except Exception:
            pass
        
        return {}
