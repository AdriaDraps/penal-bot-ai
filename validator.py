"""
validator.py — Valida la estructura del escrito generado
"""

def validar_escrito(escrito: str, intencion: str) -> list:
    """
    Verifica que el escrito tiene la estructura correcta.
    
    Returns:
        Lista de advertencias (vacía si todo está bien)
    """
    if intencion not in ("redactar", "mejorar"):
        return []
    
    advertencias = []
    
    secciones_obligatorias = {
        "AL TRIBUNAL": "Falta cabecera 'AL TRIBUNAL'",
        "HECHOS": "Falta sección de HECHOS",
        "FUNDAMENTOS DE DERECHO": "Falta sección de FUNDAMENTOS DE DERECHO",
        "SOLICITO": "Falta sección de SOLICITO",
    }
    
    for seccion, mensaje in secciones_obligatorias.items():
        if seccion not in escrito.upper():
            advertencias.append(f"⚠️ {mensaje}")
    
    # Verificar que no se inventó jurisprudencia obvia
    frases_sospechosas = [
        "STS 123/", "STC 456/", "SAP Madrid 789/",  # Referencias genéricas
    ]
    for frase in frases_sospechosas:
        if frase in escrito:
            advertencias.append("⚠️ Revisar referencias jurisprudenciales antes de presentar")
    
    return advertencias
