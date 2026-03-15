"""
claude.py — Conexión con la API de Claude
Gestiona la generación de escritos procesales
"""

import asyncio
import anthropic
from config import CLAUDE_API_KEY, CLAUDE_MODEL
from prompt import construir_prompt_final
from retriever import buscar_jurisprudencia, buscar_legislacion, buscar_estilo
from validator import validar_escrito

client = anthropic.AsyncAnthropic(api_key=CLAUDE_API_KEY)


async def generar_escrito(
    consulta: str,
    intencion: str,
    historial: list,
    datos_letrado: dict,
) -> str:
    """
    Genera un escrito procesal penal usando Claude.
    
    Args:
        consulta: Solicitud del usuario
        intencion: Tipo de tarea (redactar/mejorar/sugerir)
        historial: Historial de mensajes anteriores
        datos_letrado: Datos del abogado/procurador
    
    Returns:
        Escrito generado como string
    """
    
    # 1. Recuperar contexto jurídico relevante
    jurisprudencia = await buscar_jurisprudencia(consulta)
    legislacion = await buscar_legislacion(consulta)
    estilo = await buscar_estilo()

    # 2. Construir prompt final con todo el contexto
    system_prompt, messages = construir_prompt_final(
        consulta=consulta,
        intencion=intencion,
        historial=historial,
        datos_letrado=datos_letrado,
        jurisprudencia=jurisprudencia,
        legislacion=legislacion,
        estilo=estilo,
    )

    # 3. Llamar a Claude
    try:
        response = await client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=8192,
            system=system_prompt,
            messages=messages,
        )
        
        escrito = response.content[0].text

        # 4. Validar estructura del escrito
        advertencias = validar_escrito(escrito, intencion)
        
        if advertencias:
            escrito += "\n\n---\n⚠️ *Notas del sistema:*\n"
            for adv in advertencias:
                escrito += f"• {adv}\n"

        return escrito

    except anthropic.APIError as e:
        raise Exception(f"Error en la API de Claude: {e}")
    except Exception as e:
        raise Exception(f"Error inesperado: {e}")


async def mejorar_escrito(escrito_original: str, instrucciones: str = "") -> str:
    """
    Mejora un escrito existente.
    
    Args:
        escrito_original: Texto del escrito a mejorar
        instrucciones: Instrucciones específicas de mejora
    
    Returns:
        Escrito mejorado
    """
    system_prompt = """Eres un abogado penalista español experto. 
    Tu tarea es mejorar el escrito procesal que se te proporciona, 
    manteniendo su estructura pero reforzando los argumentos jurídicos,
    mejorando la redacción y añadiendo fundamentos de derecho más sólidos."""

    prompt_usuario = f"""Mejora el siguiente escrito procesal penal:

{escrito_original}

{"Instrucciones específicas: " + instrucciones if instrucciones else ""}

Mantén la estructura procesal y mejora el rigor jurídico."""

    response = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt_usuario}],
    )

    return response.content[0].text


async def sugerir_argumentos(descripcion_caso: str) -> str:
    """
    Sugiere argumentos jurídicos para un caso.
    
    Args:
        descripcion_caso: Descripción del caso
    
    Returns:
        Lista de argumentos jurídicos sugeridos
    """
    system_prompt = """Eres un abogado penalista español experto en estrategia procesal.
    Analiza el caso descrito y sugiere los mejores argumentos jurídicos disponibles,
    indicando la normativa y jurisprudencia aplicable."""

    response = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": descripcion_caso}],
    )

    return response.content[0].text
