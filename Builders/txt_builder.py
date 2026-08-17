import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from Core.models import SurveySchema, QuestionType, SelectorType
except ImportError:
    from Core.models import SurveySchema, QuestionType, SelectorType


class AdvancedTXTBuilder:
    """Genera archivos .txt formateados para Qualtrics con soporte correcto de Matrix, SingleLine TE, Sliders y Form Field."""

    def build(self, schema: SurveySchema, output_file: str = "Sample_Qualtrics.txt") -> str:
        lines = ["[[AdvancedFormat]]", ""]

        if schema.survey_name:
            lines.append(f"[[Block:{schema.survey_name}]]")
            lines.append("")

        for i, q in enumerate(schema.questions, 1):
            qid = q.export_tag or f"Q{i}"
            prompt = q.question_text
            if prompt and not prompt.endswith(("?", ":", ".")):
                prompt += "?"

            if q.question_type == QuestionType.DB:
                lines.append("[[Question:Text]]")
            elif q.question_type == QuestionType.TE and q.selector == SelectorType.FORM:
                lines.append("[[Question:TE:Form]]")
            elif q.question_type == QuestionType.TE:
                lines.append("[[Question:TE:SingleLine]]")
            elif q.question_type == QuestionType.MATRIX or (q.question_type == QuestionType.SLIDER and len(q.choices) > 0):
                lines.append("[[Question:Matrix]]")
            elif q.question_type == QuestionType.SLIDER and len(q.choices) == 0:
                lines.append("[[Question:MC:SingleAnswer:Horizontal]]")
            elif q.is_multiple_answer or q.selector == SelectorType.MAVR:
                lines.append("[[Question:MC:MultipleAnswer]]")
            else:
                lines.append("[[Question:MC]]")

            lines.append(f"[[ID:{qid}]]")
            lines.append(prompt)

            # Form Field
            if q.selector == SelectorType.FORM and q.choices:
                lines.append("[[Choices]]")
                for c in q.choices:
                    lines.append(c.text)

            # Matrix Table / Escala con Afirmaciones
            elif q.question_type == QuestionType.MATRIX or (q.question_type == QuestionType.SLIDER and len(q.choices) > 0):
                if q.choices:
                    lines.append("[[Choices]]")
                    for c in q.choices:
                        lines.append(c.text)
                if q.answers:
                    lines.append("[[Answers]]")
                    for a in q.answers:
                        lines.append(a.text)

            # Escala Horizontal sin Afirmaciones
            elif q.answers:
                lines.append("[[Choices]]")
                for a in q.answers:
                    lines.append(a.text)

            # Opción Múltiple Estándar
            elif q.choices:
                lines.append("[[Choices]]")
                for c in q.choices:
                    lines.append(c.text)

            lines.append("")

        content = "\n".join(lines)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ Archivo TXT generado con éxito: {output_file}")
        return output_file