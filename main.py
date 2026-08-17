import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from Extractors.doc_parser import DocumentParser
from Extractors.rule_analyzer import RuleSurveyAnalyzer
from Builders.txt_builder import AdvancedTXTBuilder
from Validators.question_reviewer import QuestionReviewer


def run_pipeline(input_file_path: str = "Sample.docx", output_file_path: str = "Sample_Qualtrics.txt"):
    print(f"📖 1/4 Leyendo documento: {input_file_path}...")
    raw_text = DocumentParser.extract_text(input_file_path)
    print(f"   Texto extraído correctamente ({len(raw_text)} caracteres).")

    print("\n⚙️ 2/4 Analizando estructura de la encuesta...")
    analyzer = RuleSurveyAnalyzer()
    survey_schema = analyzer.analyze(raw_text)
    print(f"   Encuesta extraída: '{survey_schema.survey_name}' con {len(survey_schema.questions)} preguntas.")

    print("\n🔍 3/4 Revisando y corrigiendo TODO el contenido en inglés (Títulos, Textos, Enunciados, Opciones y Escalas)...")
    reviewer = QuestionReviewer(use_ai=False, auto_fix=True)
    report = reviewer.review_survey(survey_schema)
    
    if report.questions_with_issues > 0:
        print(f"   ⚠️ Se corrigieron {report.questions_with_issues} elementos con observaciones:")
        for rev in report.reviews:
            if rev.has_issues:
                print(f"     • [{rev.qid}] Original: '{rev.original_text}'")
                if rev.grammar_issues:
                    print(f"       - Correcciones: {', '.join(rev.grammar_issues)}")
                if rev.design_suggestions:
                    print(f"       - Sugerencias metodológicas: {', '.join(rev.design_suggestions)}")
    else:
        print("   ✅ No se detectaron errores en el contenido.")

    print("\n⚙️ 4/4 Generando archivo en Formato Avanzado (.txt) para Qualtrics...")
    builder = AdvancedTXTBuilder()
    builder.build(schema=survey_schema, output_file=output_file_path)

    print(f"\n🎉 ¡Proceso completado con éxito! Archivo generado: {output_file_path}")


if __name__ == "__main__":
    documento_prueba = "Sample.docx"
    if os.path.exists(documento_prueba):
        run_pipeline(input_file_path=documento_prueba)
    else:
        print(f"⚠️ Por favor guarda tu documento con el nombre '{documento_prueba}' en la raíz del proyecto para ejecutar.")