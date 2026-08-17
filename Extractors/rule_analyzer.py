import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from Core.models import SurveySchema, Question, QuestionType, SelectorType, Choice, Validation
except ImportError:
    from Core.models import SurveySchema, Question, QuestionType, SelectorType, Choice, Validation


class RuleSurveyAnalyzer:
    """Procesa el documento soportando introducción formateada en HTML (negritas y saltos de línea), Form Field, Slider, Matrix, MC y TE."""

    def analyze(self, raw_text: str) -> SurveySchema:
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        
        survey_name = "Qualtrics Survey"
        questions = []
        current_q = None
        qid_counter = 1
        intro_lines = []
        parsing_section = None  # 'statements', 'scale', 'answers'

        for line in lines:
            clean_line = line.strip()
            line_lower = clean_line.lower()

            # Detección estricta de inicio de pregunta numerada (ej. "1. ", "2. ", "10. ")
            is_numbered = bool(re.match(r'^\d+[\.\:\)]\s*', clean_line))
            is_metadata = line_lower.startswith("scale:") or line_lower.startswith("statements:") or line_lower.startswith("answer choices:")

            if is_numbered and not is_metadata:
                if current_q:
                    questions.append(current_q)

                m = re.match(r'^(\d+)[\.\:\)]\s*(.*)', clean_line)
                q_rest = m.group(2).strip()

                if "(open text)" in q_rest.lower() or "open text" in q_rest.lower():
                    q_type = QuestionType.TE
                    selector = SelectorType.SL
                elif "(form field)" in q_rest.lower() or "(form)" in q_rest.lower():
                    q_type = QuestionType.TE
                    selector = SelectorType.FORM
                elif "(matrix)" in q_rest.lower():
                    q_type = QuestionType.MATRIX
                    selector = SelectorType.PROFILE
                elif "(scale)" in q_rest.lower():
                    q_type = QuestionType.SLIDER
                    selector = SelectorType.SAHR
                elif "(multiple selection)" in q_rest.lower():
                    q_type = QuestionType.MC
                    selector = SelectorType.MAVR
                else:
                    q_type = QuestionType.MC
                    selector = SelectorType.SAVR

                clean_prompt = re.sub(r'\s*\([^)]*(?:open\s*text|single\s*selection|multiple\s*selection|matrix|form|form\s*field|scale)[^)]*\)', '', q_rest, flags=re.IGNORECASE).strip()

                qid = f"QID{qid_counter}"
                export_tag = f"Q{qid_counter}"
                qid_counter += 1

                current_q = Question(
                    qid=qid,
                    export_tag=export_tag,
                    question_text=clean_prompt,
                    question_type=q_type,
                    selector=selector,
                    choices=[],
                    answers=[],
                    validation=Validation(is_required="[required]" in q_rest.lower())
                )
                parsing_section = None
                continue

            if not current_q:
                intro_lines.append(clean_line)
            else:
                # Lectura de metadatos dentro de la pregunta activa
                if line_lower.startswith("scale:"):
                    parsing_section = "scale"
                    scale_val = re.sub(r'^scale:\s*', '', clean_line, flags=re.IGNORECASE).strip()
                    if "1 - not effective" in scale_val.lower() and "7 - highly effective" in scale_val.lower():
                        current_q.answers = [
                            Choice(choice_id="1", text="1 - Not Effective"),
                            Choice(choice_id="2", text="2"),
                            Choice(choice_id="3", text="3"),
                            Choice(choice_id="4", text="4"),
                            Choice(choice_id="5", text="5"),
                            Choice(choice_id="6", text="6"),
                            Choice(choice_id="7", text="7 - Highly Effective")
                        ]
                    elif scale_val:
                        current_q.answers.append(Choice(choice_id=str(len(current_q.answers) + 1), text=scale_val))

                elif line_lower.startswith("statements:"):
                    parsing_section = "statements"
                    stmt_val = re.sub(r'^statements:\s*', '', clean_line, flags=re.IGNORECASE).strip()
                    if stmt_val:
                        current_q.choices.append(Choice(choice_id=str(len(current_q.choices) + 1), text=stmt_val))

                elif line_lower.startswith("answer choices:"):
                    parsing_section = "answers"
                    ans_val = re.sub(r'^answer choices:\s*', '', clean_line, flags=re.IGNORECASE).strip()
                    if ans_val:
                        if "agree" in ans_val.lower() and "disagree" in ans_val.lower():
                            current_q.answers = [
                                Choice(choice_id="1", text="Agree"),
                                Choice(choice_id="2", text="Disagree"),
                                Choice(choice_id="3", text="I don't know")
                            ]
                        else:
                            current_q.answers.append(Choice(choice_id=str(len(current_q.answers) + 1), text=ans_val))

                else:
                    clean_bullet = re.sub(r'^[•\-\*]\s*', '', clean_line).strip()
                    if parsing_section == "statements":
                        current_q.choices.append(Choice(choice_id=str(len(current_q.choices) + 1), text=clean_bullet))
                    elif parsing_section == "answers" or parsing_section == "scale":
                        current_q.answers.append(Choice(choice_id=str(len(current_q.answers) + 1), text=clean_bullet))
                    elif current_q.selector == SelectorType.FORM or current_q.question_type == QuestionType.MC:
                        current_q.choices.append(Choice(choice_id=str(len(current_q.choices) + 1), text=clean_bullet))

        if current_q:
            questions.append(current_q)

        # Crear bloque inicial de introducción con formato HTML enriquecido (negritas y saltos de párrafo)
        if intro_lines:
            formatted_intro_parts = []
            for idx, line_text in enumerate(intro_lines):
                line_clean = line_text.strip()
                if not line_clean:
                    continue
                # El título principal (línea 0) y subtítulos/encabezados cortos van en negrita
                if idx == 0 or (len(line_clean) < 60 and not line_clean.endswith(".")):
                    formatted_intro_parts.append(f"<b>{line_clean}</b>")
                else:
                    formatted_intro_parts.append(line_clean)

            intro_html = "<br><br>".join(formatted_intro_parts)
            survey_name = intro_lines[0][:60]
            
            intro_q = Question(
                qid="QID_INTRO",
                export_tag="Q1",
                question_text=intro_html,
                question_type=QuestionType.DB,
                selector=SelectorType.TB
            )
            for idx, q in enumerate(questions, start=2):
                q.export_tag = f"Q{idx}"
            questions.insert(0, intro_q)

        return SurveySchema(survey_name=survey_name, questions=questions)