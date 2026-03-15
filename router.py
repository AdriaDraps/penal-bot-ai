"""
router.py — Detecta la intención del usuario
"""

def detectar_intencion(mensaje: str) -> str:
    """
    Detecta qué tipo de tarea quiere realizar el usuario.
    
    Returns:
        'redactar' | 'mejorar' | 'sugerir' | 'analizar'
    """
    mensaje_lower = mensaje.lower()
    
    # Palabras clave por intención
    palabras_redactar = [
        "redacta", "escribe", "elabora", "prepara", "haz un escrito",
        "solicita", "presenta", "interpone", "formula"
    ]
    palabras_mejorar = [
        "mejora", "revisa", "corrige", "refuerza", "modifica",
        "añade argumentos", "refina", "pulir"
    ]
    palabras_sugerir = [
        "sugiere", "argumentos", "estrategia", "cómo defiendo",
        "qué alego", "qué puedo hacer", "opciones"
    ]
    palabras_analizar = [
        "analiza", "examina", "estudia", "qué opinas", "valora",
        "atestado", "denuncia", "acusación"
    ]
    
    for palabra in palabras_mejorar:
        if palabra in mensaje_lower:
            return "mejorar"
    
    for palabra in palabras_sugerir:
        if palabra in mensaje_lower:
            return "sugerir"
    
    for palabra in palabras_analizar:
        if palabra in mensaje_lower:
            return "analizar"
    
    # Por defecto: redactar
    return "redactar"
