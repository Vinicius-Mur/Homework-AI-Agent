# ==============================================================================
# CÉLULA 3 (SUBSTITUI a Célula 3 e a Célula 4 antigas): MOTOR PEDAGÓGICO + RENDERER
# Pré-requisito: Célula 1 (define PROJECT_PATH, SYSTEM_PATH, SAVE_PATH) e Célula 2 (extract_rag_context).
# Coloque estes 3 arquivos em  <PROJECT_PATH>/System/ :  lesson_schema.py, lessonkit.py, render_lesson.py
# ==============================================================================
import sys, json, time, random, importlib
from typing import List
from google import genai
from google.genai import errors
from google.colab import userdata

if SYSTEM_PATH not in sys.path:
    sys.path.append(SYSTEM_PATH)

import lesson_schema, lessonkit, render_lesson
for _m in (lesson_schema, lessonkit, render_lesson):      # permite editar os .py no Drive sem reiniciar o runtime
    importlib.reload(_m)
from lesson_schema import LessonSchema, LESSON_SYSTEM_INSTRUCTION
from render_lesson import build_advanced_pdf

# ------------------------------------------------------------------ retentativas + fallback de modelo
MODEL_PREFERENCE = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro"]
RETRYABLE = {429, 500, 502, 503, 504}

def _usable_models(client):
    try:
        live = {m.name.replace("models/", "") for m in client.models.list()
                if "generateContent" in (getattr(m, "supported_actions", None) or [])}
    except Exception:
        return MODEL_PREFERENCE
    return [m for m in MODEL_PREFERENCE if m in live] or MODEL_PREFERENCE

def generate_with_fallback(client, prompt, schema, system_instruction, attempts_per_model=4):
    last_error = None
    for model in _usable_models(client):
        for attempt in range(1, attempts_per_model + 1):
            try:
                print(f"🧠 {model} (tentativa {attempt}/{attempts_per_model})...")
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={
                        "system_instruction": system_instruction,
                        "response_mime_type": "application/json",
                        "response_schema": schema,
                        "temperature": 0.3,
                        "max_output_tokens": 8192,
                    },
                )
                return response.text
            except errors.APIError as e:
                last_error = e
                if e.code not in RETRYABLE:
                    raise
                wait = min(2 ** attempt, 30) + random.uniform(0, 1)
                print(f"   ⏳ Erro {e.code}. Nova tentativa em {wait:.0f}s...")
                time.sleep(wait)
        print(f"   ↪ {model} indisponível, trocando de modelo...")
    raise RuntimeError(f"Todos os modelos falharam. Último erro: {last_error}")

# ------------------------------------------------------------------ geração
def generate_modern_homework(target_level: str, grammar_point: str, vocab_list: List[str]) -> str:
    client = genai.Client(api_key=userdata.get("GEMINI_API_KEY"))
    rag = extract_rag_context(target_level)

    prompt = f"""
Create a complete Lesson Pack for CEFR level {target_level}.

INPUTS
Level: {target_level}
Grammar focus (must be used organically, never drilled): {grammar_point}
Target lexical concepts: {', '.join(vocab_list)}

RAG CONTEXT (inspiration only, never copy):
Grammar style: {rag['grammar'][:1000]}
Idioms / expressions: {rag['idioms'][:1000]}
Task inspiration: {rag['exercises'][:1000]}
Writing model: {rag['writing'][:1000]}

Fill every field of the JSON schema and respect all length limits.
"""
    text = generate_with_fallback(client, prompt, LessonSchema,
                                  LESSON_SYSTEM_INSTRUCTION.replace("{level}", target_level))
    try:
        LessonSchema.model_validate_json(text)        # confere se o JSON veio completo
    except Exception as e:
        raise ValueError(f"O modelo devolveu um JSON incompleto ou inválido: {e}")
    return text

print("✅ Motor pronto: schema + renderer + retentativas carregados.")
