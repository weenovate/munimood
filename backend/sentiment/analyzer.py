"""
Motor de análisis de sentimientos.
Modo local  : léxico español embebido + pysentimiento (si está instalado)
Modo AI     : OpenAI / Anthropic Claude / Google Gemini (configurado en app_config)
"""
import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Léxico base en español para redes sociales municipales
# ------------------------------------------------------------------
POSITIVE_WORDS = {
    "excelente","increíble","genial","fantástico","maravilloso","perfecto","bueno","buenísimo",
    "bien","mejor","bravo","aplausos","feliz","felicito","felicitaciones","gracias","agradecido",
    "agradecida","satisfecho","satisfecha","contento","contenta","alegre","orgulloso","orgullosa",
    "encantado","encantada","me gusta","apruebo","apoyo","apoya","adelante","avance","avanza",
    "progreso","mejora","logro","éxito","exitoso","eficiente","responsable","transparente",
    "honesto","comprometido","gestionó","resolvió","solucionó","arregló","construyó","inauguró",
    "habilitó","mejoró","invirtió","acertado","correcto","justo","necesario","importante",
    "útil","beneficioso","positivo","confío","creo","creemos","confiamos","sigan","continúen",
    "gracias intendente","buen trabajo","muy bien","excelente gestión","bravo","muy bueno",
    "recomiendo","dale","vamos","así se hace","eso es","todo bien","de acuerdo","muy buena",
    "muy buen","admiro","valoro","lindo","hermoso","bonito","necesitábamos","lo necesitábamos",
    "por fin","al fin","al fin!","gracias a dios","qué bueno","qué lindo","qué bien",
    "estoy feliz","estamos contentos","nos alegramos","se agradece","muy agradecido",
    "progresamos","crecemos","avanzamos","¡bravo","bien hecho","bien hecha","obra necesaria",
    "gran inversión","gran trabajo","gran gestión",
}

NEGATIVE_WORDS = {
    "malo","malísimo","pésimo","terrible","horrible","desastre","fracaso","vergüenza",
    "basura","asco","porquería","inaceptable","indignante","corrupción","corrupto","corrupta",
    "ladrón","ladrones","roban","robo","inútil","incapaz","mentira","mienten","miente",
    "negligencia","negligente","abandono","abandonado","deterioro","deteriorado","roto",
    "rota","falta","faltan","no hay","nunca","jamás","siempre igual","siempre lo mismo",
    "no funciona","no sirve","no trabajan","no hacen nada","no resuelven","no cumplen",
    "prometieron y no","promesas vacías","decepcionante","decepción","decepcionado",
    "decepcionada","enojado","enojada","indignado","indignada","harto","harta","cansado",
    "cansada","defraudado","defraudada","no confío","no confio","no creo","desconfío",
    "peligroso","peligro","inseguro","inseguridad","descuido","descuidado","sucio",
    "suciedad","feo","horrible","barrio olvidado","zona abandonada","nadie hace nada",
    "hacen lo que quieren","irregularidad","irregular","ilegal","ilegalmente","sin permiso",
    "problema","problemas","queja","quejas","reclamo","reclamos","denuncio","denuncia",
    "mucho tiempo","años esperando","cuándo van a","cuándo van","cuándo arreglan",
    "qué vergüenza","qué asco","qué malo","qué pena","lamentable","penoso","triste",
    "tristeza","me duele","nos duele","nos perjudica","perjudicial","dañino","daño",
    "destrozo","destrozaron","rompieron","a dónde va la plata","dónde está la plata",
    "estamos peor","cada vez peor","empeora","empeoró","deuda","falta de","falta de respeto",
}

INTENSIFIERS = {
    "muy","mucho","demasiado","bastante","extremadamente","increíblemente","super","súper",
    "re ","re-","totalmente","absolutamente","completamente","enormemente",
}

NEGATORS = {
    "no","nunca","jamás","tampoco","ni","sin","nada","nadie",
}

# Palabras clave que mapean texto a ejes temáticos
TOPIC_KEYWORDS = {
    "Economía": [
        "precio","precios","inflación","costo","costos","tarifa","tarifas","impuesto","impuestos",
        "tasa","tasas","subsidio","subsidios","empleo","trabajo","desempleo","salario","salarios",
        "sueldo","sueldos","comercio","negocio","empresa","empresas","economía","económico",
        "presupuesto","inversión","gasto","deuda","crédito","banco","financiero","moneda",
        "dinero","plata","pesos","dólares",
    ],
    "Desarrollo": [
        "desarrollo","crecimiento","innovación","tecnología","industria","parque industrial",
        "zona franca","polo tecnológico","startup","emprendimiento","emprendedor","digital",
        "conectividad","internet","wifi","acceso","plan","proyecto","planificación",
    ],
    "Seguridad": [
        "seguridad","policía","policia","delito","robo","robaron","asalto","asaltaron",
        "crimen","violencia","violento","peligroso","peligro","inseguridad","droga","drogas",
        "narco","cámara","cámaras","patrullaje","guardia","vigilancia","emergencia",
        "bomberos","incendio","accidente",
    ],
    "Obras Públicas": [
        "obra","obras","calle","calles","ruta","asfalto","pavimento","bache","baches",
        "veredas","vereda","cloacas","cloaca","agua","luz","alumbrado","semáforo","puente",
        "edificio","infraestructura","construcción","renovación","plaza","parque","espacio público",
        "contenedor","residuos","basura","recolección","limpieza",
    ],
    "Educación": [
        "educación","escuela","colegio","escuelas","colegios","maestro","maestra","docente",
        "docentes","alumno","alumnos","estudiante","estudiantes","aula","aulas","clase","clases",
        "materia","materias","universidad","facultad","instituto","jardín","jardines",
        "biblioteca","becas","beca","capacitación","formación",
    ],
    "Salud": [
        "salud","hospital","hospitales","clínica","clínicas","médico","médicos","doctor",
        "enfermero","enfermera","ambulancia","guardia","turno","turnos","vacuna","vacunación",
        "remedio","medicamento","obra social","cobertura","urgencia","emergencia",
        "centro de salud","caps","consultorio",
    ],
    "Turismo": [
        "turismo","turista","turistas","hotel","hoteles","hostel","restaurante","gastronomía",
        "atracción","atracciones","monumento","museos","museo","circuito","excursión",
        "temporada","temporada alta","verano","playa","río","lago","sierras","montaña",
        "paseo","paseantes","viaje","viajeros",
    ],
    "Medio Ambiente": [
        "medio ambiente","ambiente","ecología","ecológico","contaminación","contaminado",
        "árbol","árboles","verde","naturaleza","residuo","residuos","reciclaje","reciclar",
        "plástico","basural","vertedero","río","lago","agua","aire","smog","emisión",
        "sustentable","sostenible","renovable","solar","eólico","energía limpia",
    ],
    "Entretenimiento": [
        "entretenimiento","cultura","cultural","evento","eventos","festival","recital",
        "concierto","teatro","cine","deporte","deportes","fútbol","tenis","natación",
        "gimnasio","recreación","carnaval","fiesta","fiestas","celebración","show",
        "espectáculo","actividad","actividades","ocio","libre","fin de semana",
    ],
}


def _normalize(text: str) -> str:
    text = text.lower()
    replacements = {
        "á":"a","é":"e","í":"i","ó":"o","ú":"u","ü":"u","ñ":"n",
        "à":"a","è":"e","ì":"i","ò":"o","ù":"u",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    text = re.sub(r"[^\w\s]", " ", text)
    return text


def classify_topic(text: str) -> str | None:
    """Devuelve el nombre del eje más probable o None si no aplica."""
    normalized = _normalize(text)
    words = set(normalized.split())
    scores = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in normalized)
        if score > 0:
            scores[topic] = score
    if not scores:
        return None
    return max(scores, key=scores.get)


# ------------------------------------------------------------------
# Analizadores
# ------------------------------------------------------------------

def _local_lexicon(text: str) -> Tuple[str, float]:
    """Análisis léxico simple para español. Retorna (sentiment, score -1..1)."""
    normalized = _normalize(text)
    words = normalized.split()
    score = 0.0
    negate = False

    for i, word in enumerate(words):
        if word in NEGATORS:
            negate = True
            continue

        weight = 1.0
        if i > 0 and words[i - 1] in INTENSIFIERS:
            weight = 1.5

        if word in POSITIVE_WORDS:
            score += weight if not negate else -weight
        elif word in NEGATIVE_WORDS:
            score -= weight if not negate else weight

        if word not in NEGATORS:
            negate = False

    if score > 0.3:
        return "positive", min(score / 5, 1.0)
    if score < -0.3:
        return "negative", max(score / 5, -1.0)
    return "neutral", 0.0


def _pysentimiento_analyze(text: str) -> Tuple[str, float]:
    """Usa pysentimiento si está disponible."""
    try:
        from pysentimiento import create_analyzer
        analyzer = _get_pysentimiento_analyzer()
        result = analyzer.predict(text[:512])
        label = result.output.lower()
        score_map = {"pos": 1.0, "neg": -1.0, "neu": 0.0}
        sentiment_map = {"pos": "positive", "neg": "negative", "neu": "neutral"}
        return sentiment_map.get(label, "neutral"), score_map.get(label, 0.0)
    except Exception as e:
        logger.debug("pysentimiento no disponible: %s — usando léxico", e)
        return _local_lexicon(text)


_pysentimiento_instance = None


def _get_pysentimiento_analyzer():
    global _pysentimiento_instance
    if _pysentimiento_instance is None:
        from pysentimiento import create_analyzer
        _pysentimiento_instance = create_analyzer(task="sentiment", lang="es")
    return _pysentimiento_instance


def _openai_analyze(text: str, api_key: str, model: str = "gpt-3.5-turbo") -> Tuple[str, float]:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model or "gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Sos un analizador de sentimientos para comentarios en redes sociales en español "
                        "sobre gestión municipal argentina. Clasificá el texto como POSITIVO, NEGATIVO o NEUTRAL. "
                        "Respondé únicamente con una de esas tres palabras en mayúsculas."
                    ),
                },
                {"role": "user", "content": text[:1000]},
            ],
            max_tokens=10,
            temperature=0,
        )
        label = response.choices[0].message.content.strip().upper()
        if "POSITIVO" in label:
            return "positive", 0.9
        if "NEGATIVO" in label:
            return "negative", -0.9
        return "neutral", 0.0
    except Exception as e:
        logger.warning("OpenAI error: %s — fallback a léxico", e)
        return _local_lexicon(text)


def _claude_analyze(text: str, api_key: str, model: str = "claude-haiku-4-5-20251001") -> Tuple[str, float]:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model or "claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Analizá el sentimiento del siguiente comentario de redes sociales en español "
                        "sobre gestión municipal argentina. Respondé únicamente con: POSITIVO, NEGATIVO o NEUTRAL.\n\n"
                        f"Comentario: {text[:1000]}"
                    ),
                }
            ],
        )
        label = message.content[0].text.strip().upper()
        if "POSITIVO" in label:
            return "positive", 0.9
        if "NEGATIVO" in label:
            return "negative", -0.9
        return "neutral", 0.0
    except Exception as e:
        logger.warning("Claude error: %s — fallback a léxico", e)
        return _local_lexicon(text)


def _gemini_analyze(text: str, api_key: str, model: str = "gemini-pro") -> Tuple[str, float]:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        m = genai.GenerativeModel(model or "gemini-pro")
        prompt = (
            "Analizá el sentimiento del siguiente comentario de redes sociales en español "
            "sobre gestión municipal argentina. Respondé únicamente con: POSITIVO, NEGATIVO o NEUTRAL.\n\n"
            f"Comentario: {text[:1000]}"
        )
        response = m.generate_content(prompt)
        label = response.text.strip().upper()
        if "POSITIVO" in label:
            return "positive", 0.9
        if "NEGATIVO" in label:
            return "negative", -0.9
        return "neutral", 0.0
    except Exception as e:
        logger.warning("Gemini error: %s — fallback a léxico", e)
        return _local_lexicon(text)


# ------------------------------------------------------------------
# Función principal
# ------------------------------------------------------------------

def analyze_sentiment(
    text: str,
    engine: str = "local",
    api_key: str = "",
    model: str = "",
) -> Tuple[str, float]:
    """
    Analiza el sentimiento de un texto.
    engine: 'local' | 'pysentimiento' | 'openai' | 'claude' | 'gemini'
    Retorna (sentiment: 'positive'|'negative'|'neutral', score: float)
    """
    if not text or not text.strip():
        return "neutral", 0.0

    if engine == "openai" and api_key:
        return _openai_analyze(text, api_key, model)
    if engine == "claude" and api_key:
        return _claude_analyze(text, api_key, model)
    if engine == "gemini" and api_key:
        return _gemini_analyze(text, api_key, model)
    if engine == "pysentimiento":
        return _pysentimiento_analyze(text)

    # Por defecto: léxico local
    return _local_lexicon(text)
