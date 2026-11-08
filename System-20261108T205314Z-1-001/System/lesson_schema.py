"""
lesson_schema.py - Pydantic schema + system instruction for the Lesson Pack agent.

Rules that keep Gemini structured output stable:
  * no defaults, no Optional: every field is required (the model may return "" or [] when not needed)
  * student-facing fields are in English, teacher-facing fields (teacher_*) in PT-BR
  * every field maps to a block of the PDF (see render_lesson.py)
"""
from typing import List
from pydantic import BaseModel, Field


# ------------------------------------------------------------------ 01 INPUT
class Highlight(BaseModel):
    text: str = Field(description="EXACT substring that appears in comprehensible_input_text (same spelling and capitalisation).")
    kind: str = Field(description="'vocab' for new words/chunks, 'verb' for the target grammar verb forms, 'exception' for irregular forms.")

class WordBankItem(BaseModel):
    word: str = Field(description="Word or lexical chunk taken from the input text.")
    meaning: str = Field(description="Very short meaning in simple English (max 8 words). Add a false-friend alert for Portuguese speakers when relevant, e.g. 'parents != parentes'.")

class GistQuestion(BaseModel):
    question: str
    options: List[str] = Field(description="Exactly 3 options, WITHOUT letters (no 'a)').")
    answer: str = Field(description="The correct option, copied exactly from options.")

class TrueFalse(BaseModel):
    statement: str
    answer: bool

# ------------------------------------------------------------------ 02 SHADOWING
class DialogueLine(BaseModel):
    speaker: str = Field(description="First name of the speaker.")
    line: str = Field(description="One short, natural line (max 14 words).")
    stress_words: List[str] = Field(description="The 2-4 words of this line that carry the sentence stress, exactly as written in 'line'.")
    intonation: str = Field(description="'rise' for yes/no questions and 'fall' for statements and wh-questions.")

class PronunciationFocus(BaseModel):
    title: str = Field(description="Short title, e.g. 'Stress in compound nouns'. Empty string if none.")
    rule: str = Field(description="One-sentence rule in simple English.")
    examples: List[str] = Field(description="3-5 examples, written so the stressed syllable is in CAPS, e.g. 'BOYfriend'.")
    common_slip: str = Field(description="One common pronunciation mistake of Portuguese speakers for this point. Empty string if none.")

# ------------------------------------------------------------------ 03 TBLT
class TBLTTask(BaseModel):
    title: str = Field(description="Task title, e.g. 'Mission: Fix the missed flight'.")
    outcome: str = Field(description="Concrete outcome the students produce, one sentence.")
    role_problem: str = Field(description="Role the student plays AND the real problem to solve (2-3 sentences).")
    pre_task: str = Field(description="Pre-task instruction (1 sentence).")
    task: str = Field(description="Main task instruction (1-2 sentences).")
    planning: str = Field(description="Planning instruction (1 sentence).")
    report: str = Field(description="Report instruction (1 sentence).")
    task_prompts: List[str] = Field(description="6-8 short prompts students work through (questions to ask, situations to handle).")
    useful_language: List[str] = Field(description="4 model questions or chunks that use the target grammar naturally.")

class LanguageRow(BaseModel):
    col1: str
    col2: str
    col3: str
    is_exception: bool = Field(description="True if this row is an irregular form or an exception.")

class ErrorFix(BaseModel):
    wrong: str
    right: str

class LanguageFocus(BaseModel):
    title: str = Field(description="Short title, e.g. 'Present continuous'. Empty string to skip this block.")
    formula: str = Field(description="One-line formula with an example, e.g. 'Subject + am/is/are + verb-ing'.")
    column_headers: List[str] = Field(description="Exactly 3 short column headers for the table.")
    rows: List[LanguageRow] = Field(description="3-5 rows.")
    errors: List[ErrorFix] = Field(description="3-4 typical learner errors with the corrected sentence.")

# ------------------------------------------------------------------ 04 RECONFIGURATION
class ShuffleItem(BaseModel):
    intent_hint: str = Field(description="Communicative intention in simple English, e.g. 'Ask politely to change your flight.'")
    blocks: List[str] = Field(description="3-5 meaning blocks in scrambled order (not single words).")
    answer: str = Field(description="The correct sentence.")

class TransformItem(BaseModel):
    original: str
    answer: str

class Reconfiguration(BaseModel):
    shuffle_instruction: str = Field(description="One sentence telling students to rebuild the sentences from the blocks.")
    shuffle_items: List[ShuffleItem] = Field(description="4-5 items.")
    transform_instruction: str = Field(description="One sentence, e.g. 'Rewrite each sentence about Rita. Start with She.' Empty string to skip.")
    transform_items: List[TransformItem] = Field(description="0-5 items. Empty list to skip.")

# ------------------------------------------------------------------ CHECK + TEACHER
class CheckItem(BaseModel):
    prompt: str
    options: List[str] = Field(description="2-3 options WITHOUT letters, or an empty list for an open answer.")
    answer: str

class MFP(BaseModel):
    meaning: str = Field(description="PT-BR, max 45 words.")
    form: str = Field(description="PT-BR, max 45 words.")
    pronunciation: str = Field(description="PT-BR, max 45 words.")

class Problem(BaseModel):
    problem: str = Field(description="PT-BR: an anticipated learner problem.")
    solution: str = Field(description="PT-BR: what the teacher does.")


# ------------------------------------------------------------------ MAIN
class LessonSchema(BaseModel):
    lesson_title: str
    cefr_level: str = Field(description="A1 or A2.")
    focus_summary: str = Field(description="Max 8 words, e.g. 'present continuous - airport language'.")
    main_aim: str = Field(description="'By the end of the lesson, students can ...' (one sentence, English).")
    objectives: List[str] = Field(description="Exactly 4 measurable sub-objectives in English, starting with a verb.")

    teacher_lead_in: str = Field(description="PT-BR, max 70 words: lead-in and how to run the reading.")
    comprehensible_input_text: str = Field(description="A graded text or e-mail (i+1), 110-160 words, paragraphs separated by a blank line. Must contain the target grammar and vocabulary naturally.")
    highlights: List[Highlight] = Field(description="8-14 highlights over the input text.")
    word_bank: List[WordBankItem] = Field(description="5-7 items.")
    gist_questions: List[GistQuestion] = Field(description="Exactly 2.")
    true_false: List[TrueFalse] = Field(description="Exactly 4, with a mix of true and false.")

    teacher_shadowing_note: str = Field(description="PT-BR, max 60 words: how to run the shadowing and what to listen for.")
    shadowing_dialogue: List[DialogueLine] = Field(description="6-8 lines between two speakers. It also models the TBLT task.")
    pronunciation_focus: PronunciationFocus

    teacher_tblt_note: str = Field(description="PT-BR, max 60 words: how to run the task cycle and what errors to note.")
    tblt_task: TBLTTask
    language_focus: LanguageFocus

    teacher_reconfiguration_note: str = Field(description="PT-BR, max 50 words.")
    reconfiguration: Reconfiguration

    check_items: List[CheckItem] = Field(description="Exactly 5 items: 3 closed, 1 question-formation, 1 open writing item.")
    can_do: List[str] = Field(description="Exactly 3 'I can ...' statements in English (without the words 'I can').")

    mfp: MFP
    anticipated_problems: List[Problem] = Field(description="3-4 items.")
    pedagogical_rationale: str = Field(description="PT-BR, max 70 words: how text, task and reconfiguration make the student use the target grammar organically.")


LESSON_SYSTEM_INSTRUCTION = """
You are a state-of-the-art ELT Pedagogical Architect (CELTA/DELTA level), rooted in Modern Communicative
Language Teaching, TBLT and Krashen's Comprehensible Input.

ABSOLUTE RULES
1. No gap-fills, no translation tasks, no passive grammar drills. Students must USE the structure to solve a problem.
2. Vocabulary is taught as lexical chunks (meaning blocks), never as isolated lists.
3. Language level: strictly CEFR {level}. Short sentences, high-frequency words, natural register.
4. Student-facing fields are in English. Fields starting with teacher_, plus mfp, anticipated_problems and
   pedagogical_rationale, are in Brazilian Portuguese (PT-BR).
5. Respect every length limit in the schema: the layout is fixed and long text breaks the page.
6. Use the RAG context only as inspiration for topics, style and vocabulary. Never copy it verbatim.
7. All content must be original, internally consistent (answers must match the texts) and age-appropriate.
"""
