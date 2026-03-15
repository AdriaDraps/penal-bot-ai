"""
prompt.py — Constructor del prompt maestro
Gestiona la construcción del prompt final con todo el contexto
"""

SYSTEM_PROMPT_BASE = """SISTEMA: BOT JURÍDICO PENAL ESPAÑOL
════════════════════════════════════════════════════════════════

ROL
Eres un abogado penalista español senior con 20 años de experiencia en 
litigación penal. Redactas escritos procesales para juzgados y tribunales 
españoles. Tu estilo es técnico, formal, contundente y combativo. 
Nunca cedes en el rigor jurídico.

NORMATIVA QUE MANEJAS
- Constitución Española (CE)
- Código Penal (CP)
- Ley de Enjuiciamiento Criminal (LECrim)
- Ley Orgánica del Poder Judicial (LOPJ)
- Ley Orgánica 4/2015 del Estatuto de la Víctima
- Ley Orgánica 6/1984 de Habeas Corpus
- Reglamento (UE) 2016/679 (RGPD)
- Directivas europeas aplicables
- Jurisprudencia del TS, TC y Audiencias Provinciales

ESTRUCTURA OBLIGATORIA DEL ESCRITO
───────────────────────────────────
JUZGADO/TRIBUNAL [tipo y número]
DE [localidad]
[Tipo de procedimiento y número]

                    AL JUZGADO DE [tipo] / AL TRIBUNAL

[COMPARECENCIA — uno de estos formatos:]

CON PROCURADOR:
Don/Doña [procurador], Procurador de los Tribunales, en nombre y representación 
de Don/Doña [cliente], bajo la dirección letrada de Don/Doña [abogado], 
Letrado del Ilustre Colegio de Abogados de [ciudad], colegiado nº [número], 
ante el Juzgado comparezco y, como mejor proceda en Derecho, DIGO:

SIN PROCURADOR:
Don/Doña [abogado], Letrado del Ilustre Colegio de Abogados de [ciudad], 
colegiado nº [número], en nombre y defensa de Don/Doña [cliente], 
ante el Juzgado comparezco y, como mejor proceda en Derecho, DIGO:

EXPOSICIÓN

HECHOS

PRIMERO.- [Hecho procesal relevante]
SEGUNDO.- [Hecho procesal relevante]
[...]

FUNDAMENTOS DE DERECHO

I.- [Fundamento principal — citar artículo completo en primera mención]
II.- [Fundamento secundario]
III.- [Jurisprudencia — SOLO de la proporcionada en el contexto]
[...]

EN SU VIRTUD,

SOLICITO AL JUZGADO:

Que tenga por presentado este escrito y, previos los trámites oportunos, 
acuerde [petición concreta y detallada].

[Si procede:]
OTROSÍ DIGO: [cuestión secundaria]
OTROSÍ SUPLICO: [petición secundaria]

[Localidad], a [fecha]

Fdo.: [nombre letrado] / [nombre procurador si hay]

REGLAS DE CITAS LEGALES
────────────────────────
Primera mención: citar artículo completo con nombre de ley completo
  Ejemplo: "artículo 588 ter a de la Ley de Enjuiciamiento Criminal"
Siguientes menciones: forma abreviada
  Ejemplo: "art. 588 ter a LECrim"

Abreviaturas estándar:
  CE = Constitución Española
  CP = Código Penal
  LECrim = Ley de Enjuiciamiento Criminal  
  LOPJ = Ley Orgánica del Poder Judicial

REGLAS DE JURISPRUDENCIA
────────────────────────
⚠ CRÍTICO: SOLO citar sentencias presentes en el contexto del sistema.
⚠ Si no hay jurisprudencia disponible en el contexto, NO citar ninguna.
⚠ Formato obligatorio: "STS [número]/[año], de [fecha], Sala de lo Penal ([resumen breve])"

ESTILO
──────
- Tono: técnico, formal, contundente, argumentativo
- Razonamiento: jurídico sólido, sin concesiones
- Estructura: cada fundamento de derecho debe tener desarrollo argumental
- Nivel: propio de un penalista litigante de primera instancia y apelación

RESTRICCIONES ABSOLUTAS
────────────────────────
❌ No inventar sentencias ni referencias jurisprudenciales
❌ No citar artículos que no existan en la normativa
❌ No usar lenguaje coloquial o informal
❌ No simplificar el razonamiento jurídico
❌ No omitir ninguna sección obligatoria de la estructura
❌ El escrito debe estar listo para presentar ante juzgado"""


def construir_prompt_final(
    consulta: str,
    intencion: str,
    historial: list,
    datos_letrado: dict,
    jurisprudencia: list,
    legislacion: list,
    estilo: list,
) -> tuple[str, list]:
    """
    Construye el system prompt y los mensajes para Claude.
    
    Returns:
        Tuple de (system_prompt, messages)
    """
    
    # Construir sección de datos del letrado
    datos_str = _formatear_datos_letrado(datos_letrado)
    
    # Construir sección de jurisprudencia
    jurisp_str = _formatear_jurisprudencia(jurisprudencia)
    
    # Construir sección de legislación
    legis_str = _formatear_legislacion(legislacion)
    
    # Construir sección de estilo
    estilo_str = _formatear_estilo(estilo)

    system_prompt = f"""{SYSTEM_PROMPT_BASE}

════════════════════════════════════════════════════════════════
CONTEXTO DINÁMICO DEL SISTEMA
════════════════════════════════════════════════════════════════

DATOS DEL LETRADO:
{datos_str}

JURISPRUDENCIA DISPONIBLE PARA ESTE ESCRITO:
{jurisp_str}

LEGISLACIÓN RELEVANTE:
{legis_str}

EJEMPLOS DE ESTILO DEL ABOGADO USUARIO:
{estilo_str}
════════════════════════════════════════════════════════════════"""

    # Construir mensajes con historial
    messages = []
    
    for msg in historial[-6:]:  # Últimos 6 turnos para no saturar el contexto
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Añadir consulta actual con instrucción de intención
    instruccion_intencion = _instruccion_por_intencion(intencion)
    messages.append({
        "role": "user",
        "content": f"{instruccion_intencion}\n\n{consulta}"
    })

    return system_prompt, messages


def _formatear_datos_letrado(datos: dict) -> str:
    if not datos:
        return "No configurados. Usar placeholders: [ABOGADO], [COLEGIADO], [COLEGIO], [CLIENTE]"
    
    lineas = []
    if datos.get("abogado"):
        lineas.append(f"Abogado: {datos['abogado']}")
    if datos.get("colegiado"):
        lineas.append(f"Nº Colegiado: {datos['colegiado']}")
    if datos.get("colegio"):
        lineas.append(f"Colegio: {datos['colegio']}")
    if datos.get("procurador") and datos["procurador"].lower() != "ninguno":
        lineas.append(f"Procurador: {datos['procurador']}")
    else:
        lineas.append("Sin procurador (comparecencia directa del letrado)")
    
    return "\n".join(lineas) if lineas else "No configurados"


def _formatear_jurisprudencia(sentencias: list) -> str:
    if not sentencias:
        return "No hay jurisprudencia disponible para esta consulta. NO citar ninguna sentencia."
    
    resultado = []
    for s in sentencias:
        resultado.append(
            f"• {s.get('referencia', 'Sin referencia')} — {s.get('tribunal', '')}\n"
            f"  Fecha: {s.get('fecha', '')}\n"
            f"  Tema: {s.get('tema', '')}\n"
            f"  Extracto: {s.get('texto', '')[:500]}...\n"
        )
    
    return "\n".join(resultado)


def _formatear_legislacion(articulos: list) -> str:
    if not articulos:
        return "Usar la normativa conocida del sistema. Verificar existencia real de los artículos."
    
    resultado = []
    for a in articulos:
        resultado.append(
            f"• {a.get('ley', '')} — Art. {a.get('articulo', '')}\n"
            f"  Texto: {a.get('texto', '')[:300]}...\n"
        )
    
    return "\n".join(resultado)


def _formatear_estilo(ejemplos: list) -> str:
    if not ejemplos:
        return "Usar estilo estándar de abogado penalista español litigante."
    
    resultado = ["Ejemplos de escritos del abogado usuario para referencia de estilo:"]
    for i, ej in enumerate(ejemplos[:2], 1):  # Solo 2 ejemplos para no saturar
        resultado.append(f"\nEjemplo {i}:\n{ej.get('texto', '')[:800]}...")
    
    return "\n".join(resultado)


def _instruccion_por_intencion(intencion: str) -> str:
    instrucciones = {
        "redactar": "TAREA: Redacta un escrito procesal penal completo siguiendo estrictamente la estructura obligatoria.",
        "mejorar": "TAREA: Mejora el siguiente escrito procesal, reforzando los argumentos jurídicos y la redacción técnica.",
        "sugerir": "TAREA: Analiza la situación jurídica y sugiere los mejores argumentos de defensa disponibles con su fundamentación legal.",
        "analizar": "TAREA: Analiza jurídicamente el documento o situación descrita, identificando elementos procesales relevantes.",
    }
    return instrucciones.get(intencion, instrucciones["redactar"])
