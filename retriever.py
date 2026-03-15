"""
retriever.py — Búsqueda semántica en Supabase
Recupera jurisprudencia y legislación relevante para cada consulta
"""

import asyncio
from typing import Optional
import anthropic
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, CLAUDE_API_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
embedding_client = anthropic.AsyncAnthropic(api_key=CLAUDE_API_KEY)


async def buscar_jurisprudencia(consulta: str, limite: int = 5) -> list:
    """
    Busca jurisprudencia relevante usando búsqueda semántica (pgvector).
    
    Args:
        consulta: Texto de la consulta del usuario
        limite: Número máximo de resultados
    
    Returns:
        Lista de sentencias relevantes
    """
    try:
        # Generar embedding de la consulta
        embedding = await _generar_embedding(consulta)
        
        if embedding:
            # Búsqueda semántica con pgvector
            resultado = supabase.rpc(
                "buscar_jurisprudencia_semantica",
                {
                    "query_embedding": embedding,
                    "similarity_threshold": 0.7,
                    "match_count": limite,
                }
            ).execute()
            
            if resultado.data:
                return resultado.data
        
        # Fallback: búsqueda por texto completo
        return _buscar_jurisprudencia_texto(consulta, limite)

    except Exception as e:
        print(f"Error buscando jurisprudencia: {e}")
        return _buscar_jurisprudencia_texto(consulta, limite)


def _buscar_jurisprudencia_texto(consulta: str, limite: int = 5) -> list:
    """Búsqueda por texto completo como fallback"""
    try:
        # Extraer términos clave para búsqueda
        terminos = _extraer_terminos_clave(consulta)
        
        resultado = supabase.table("jurisprudencia")\
            .select("id, tribunal, referencia, fecha, texto, tema")\
            .text_search("texto", terminos)\
            .limit(limite)\
            .execute()
        
        return resultado.data if resultado.data else []
    except Exception as e:
        print(f"Error en búsqueda de texto: {e}")
        return []


async def buscar_legislacion(consulta: str, limite: int = 10) -> list:
    """
    Busca artículos legislativos relevantes.
    
    Args:
        consulta: Texto de la consulta del usuario
        limite: Número máximo de resultados
    
    Returns:
        Lista de artículos relevantes
    """
    try:
        embedding = await _generar_embedding(consulta)
        
        if embedding:
            resultado = supabase.rpc(
                "buscar_legislacion_semantica",
                {
                    "query_embedding": embedding,
                    "similarity_threshold": 0.65,
                    "match_count": limite,
                }
            ).execute()
            
            if resultado.data:
                return resultado.data
        
        # Fallback
        return _buscar_legislacion_texto(consulta, limite)

    except Exception as e:
        print(f"Error buscando legislación: {e}")
        return _buscar_legislacion_texto(consulta, limite)


def _buscar_legislacion_texto(consulta: str, limite: int = 10) -> list:
    """Búsqueda de legislación por texto"""
    try:
        terminos = _extraer_terminos_clave(consulta)
        resultado = supabase.table("legislacion")\
            .select("id, ley, articulo, texto")\
            .text_search("texto", terminos)\
            .limit(limite)\
            .execute()
        
        return resultado.data if resultado.data else []
    except Exception as e:
        print(f"Error buscando legislación texto: {e}")
        return []


async def buscar_estilo(limite: int = 2) -> list:
    """
    Recupera ejemplos de escritos del abogado para referencia de estilo.
    
    Args:
        limite: Número de ejemplos a recuperar
    
    Returns:
        Lista de ejemplos de escritos
    """
    try:
        resultado = supabase.table("estilo_escritos")\
            .select("texto, tipo")\
            .limit(limite)\
            .execute()
        
        return resultado.data if resultado.data else []
    except Exception as e:
        print(f"Error recuperando estilo: {e}")
        return []


async def indexar_jurisprudencia(sentencia: dict) -> bool:
    """
    Indexa una nueva sentencia con embedding para búsqueda semántica.
    
    Args:
        sentencia: Diccionario con datos de la sentencia
    
    Returns:
        True si se indexó correctamente
    """
    try:
        texto_completo = f"{sentencia.get('tema', '')} {sentencia.get('texto', '')}"
        embedding = await _generar_embedding(texto_completo)
        
        if embedding:
            sentencia["embedding"] = embedding
        
        supabase.table("jurisprudencia").insert(sentencia).execute()
        return True
    except Exception as e:
        print(f"Error indexando sentencia: {e}")
        return False


async def _generar_embedding(texto: str) -> Optional[list]:
    """
    Genera un embedding vectorial del texto usando la API.
    Nota: Claude no tiene API de embeddings directamente;
    usar OpenAI o Voyage AI para embeddings, o pgvector con FTS.
    
    Por ahora retorna None para usar búsqueda por texto.
    """
    # TODO: Integrar API de embeddings (Voyage AI recomendado para documentos legales)
    # voyage_client = voyageai.Client(api_key=VOYAGE_API_KEY)
    # result = voyage_client.embed([texto], model="voyage-law-2")
    # return result.embeddings[0]
    return None


def _extraer_terminos_clave(consulta: str) -> str:
    """
    Extrae términos jurídicos clave para búsqueda por texto.
    """
    # Términos comunes a ignorar
    stopwords_juridicas = {
        "escrito", "redactar", "solicitar", "pedir", "juzgado", 
        "tribunal", "por", "que", "el", "la", "los", "las",
        "un", "una", "de", "del", "al", "con", "para", "sobre"
    }
    
    palabras = consulta.lower().split()
    terminos = [p for p in palabras if len(p) > 3 and p not in stopwords_juridicas]
    
    return " | ".join(terminos[:5]) if terminos else consulta[:100]
