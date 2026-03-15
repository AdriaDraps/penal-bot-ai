-- ============================================================
-- SCHEMA DE BASE DE DATOS — BOT JURÍDICO PENAL
-- Ejecutar en Supabase SQL Editor
-- ============================================================

-- Extensión para búsqueda semántica (embeddings)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- TABLA: jurisprudencia
-- ============================================================
CREATE TABLE IF NOT EXISTS jurisprudencia (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tribunal    TEXT NOT NULL,           -- 'TS', 'TC', 'AP Madrid', etc.
    referencia  TEXT NOT NULL UNIQUE,    -- 'STS 123/2023'
    fecha       DATE,
    texto       TEXT NOT NULL,
    tema        TEXT,                    -- 'nulidad prueba', 'presunción inocencia', etc.
    embedding   vector(1536),            -- Para búsqueda semántica (futuro)
    creado_en   TIMESTAMP DEFAULT NOW()
);

-- Índice para búsqueda por texto completo
CREATE INDEX IF NOT EXISTS jurisprudencia_texto_idx 
    ON jurisprudencia USING gin(to_tsvector('spanish', texto));

-- Índice para búsqueda semántica
CREATE INDEX IF NOT EXISTS jurisprudencia_embedding_idx 
    ON jurisprudencia USING ivfflat (embedding vector_cosine_ops);

-- ============================================================
-- TABLA: legislacion
-- ============================================================
CREATE TABLE IF NOT EXISTS legislacion (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ley         TEXT NOT NULL,           -- 'LECrim', 'CP', 'CE', etc.
    articulo    TEXT NOT NULL,           -- '588 ter a'
    texto       TEXT NOT NULL,
    embedding   vector(1536),
    creado_en   TIMESTAMP DEFAULT NOW(),
    UNIQUE(ley, articulo)
);

CREATE INDEX IF NOT EXISTS legislacion_texto_idx 
    ON legislacion USING gin(to_tsvector('spanish', texto));

-- ============================================================
-- TABLA: estilo_escritos
-- ============================================================
CREATE TABLE IF NOT EXISTS estilo_escritos (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo        TEXT,                    -- 'recurso', 'diligencias', 'habeas_corpus', etc.
    texto       TEXT NOT NULL,
    creado_en   TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLA: usuarios (datos de letrados)
-- ============================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id     BIGINT UNIQUE NOT NULL,
    datos_letrado   JSONB DEFAULT '{}',
    creado_en       TIMESTAMP DEFAULT NOW(),
    actualizado_en  TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- FUNCIÓN: búsqueda semántica de jurisprudencia
-- (Activar cuando se implementen embeddings)
-- ============================================================
CREATE OR REPLACE FUNCTION buscar_jurisprudencia_semantica(
    query_embedding vector(1536),
    similarity_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    tribunal TEXT,
    referencia TEXT,
    fecha DATE,
    texto TEXT,
    tema TEXT,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        j.id,
        j.tribunal,
        j.referencia,
        j.fecha,
        j.texto,
        j.tema,
        1 - (j.embedding <=> query_embedding) AS similarity
    FROM jurisprudencia j
    WHERE j.embedding IS NOT NULL
        AND 1 - (j.embedding <=> query_embedding) > similarity_threshold
    ORDER BY j.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================================
-- DATOS DE EJEMPLO — jurisprudencia
-- ============================================================
INSERT INTO jurisprudencia (tribunal, referencia, fecha, texto, tema) VALUES
(
    'Tribunal Supremo, Sala de lo Penal',
    'STS 432/2023',
    '2023-05-15',
    'La intervención de comunicaciones telefónicas requiere autorización judicial motivada que justifique su necesidad, proporcionalidad e idoneidad. La resolución judicial ha de contener los elementos fácticos y jurídicos que permitan concluir que existe una sospecha fundada de comisión de un hecho delictivo grave.',
    'intervención telefónica, proporcionalidad, autorización judicial'
),
(
    'Tribunal Constitucional',
    'STC 145/2014',
    '2014-09-22',
    'El derecho al secreto de las comunicaciones protegido en el artículo 18.3 CE garantiza a las personas la confidencialidad de sus comunicaciones, frente a cualquier forma de interceptación o escucha por terceros, incluidos los poderes públicos.',
    'secreto comunicaciones, derechos fundamentales, art. 18.3 CE'
),
(
    'Audiencia Provincial de Madrid, Sección 2ª',
    'SAP Madrid 156/2022',
    '2022-03-10',
    'La práctica de diligencias de cotejo y análisis de dispositivos móviles requiere autorización judicial específica que delimite el alcance de la intervención, el período temporal objeto de análisis y los datos concretos a examinar, respetando el principio de proporcionalidad.',
    'cotejo teléfonos, diligencias de instrucción, proporcionalidad'
);

-- ============================================================
-- DATOS DE EJEMPLO — legislacion
-- ============================================================
INSERT INTO legislacion (ley, articulo, texto) VALUES
(
    'LECrim',
    '588 ter a',
    'Las medidas de investigación tecnológica reguladas en este capítulo solo podrán ser autorizadas cuando la investigación tenga por objeto alguno de los siguientes delitos: a) Delitos dolosos castigados con pena con límite máximo de, al menos, tres años de prisión...'
),
(
    'LECrim',
    '588 ter j',
    'El juez o tribunal podrá acordar, a instancia de parte, la aportación de datos electrónicos que se encuentren en poder del prestador de servicios, siempre que ello sea posible y no constituya una carga desproporcionada.'
),
(
    'CE',
    '18.3',
    'Se garantiza el secreto de las comunicaciones y, en especial, de las postales, telegráficas y telefónicas, salvo resolución judicial.'
);

-- ============================================================
-- VERIFICACIÓN
-- ============================================================
SELECT 'Jurisprudencia' AS tabla, COUNT(*) FROM jurisprudencia
UNION ALL
SELECT 'Legislación', COUNT(*) FROM legislacion
UNION ALL  
SELECT 'Estilo escritos', COUNT(*) FROM estilo_escritos
UNION ALL
SELECT 'Usuarios', COUNT(*) FROM usuarios;
