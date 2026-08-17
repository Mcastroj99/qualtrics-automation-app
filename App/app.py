import os
import sys
import importlib

# Asegura que la raíz del proyecto esté en sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import streamlit as st

# Importación directa de modelos estáticos
from Core.models import SurveySchema, Question, Choice, Validation, QuestionType, SelectorType
from Core.scales import PREDEFINED_SCALES

# Importación y reload exclusivamente de extractor, validador y generadores
import Extractors.doc_parser
import Extractors.rule_analyzer
import Validators.question_reviewer
import Builders.txt_builder
import Builders.docx_builder

importlib.reload(Extractors.doc_parser)
importlib.reload(Extractors.rule_analyzer)
importlib.reload(Validators.question_reviewer)
importlib.reload(Builders.txt_builder)
importlib.reload(Builders.docx_builder)

from Extractors.doc_parser import DocumentParser
from Extractors.rule_analyzer import RuleSurveyAnalyzer
from Validators.question_reviewer import QuestionReviewer
from Builders.txt_builder import AdvancedTXTBuilder
from Builders.docx_builder import DocxBuilder

st.set_page_config(page_title="Qualtrics Survey Automator", page_icon="📑", layout="wide")

st.title("📑 Qualtrics Survey Automation Platform")
st.markdown("Build, edit, and convert survey specifications into **Qualtrics Advanced TXT** and **Standard Word (.docx)** seamlessly.")

st.sidebar.header("⚙️ Quality Engine Settings")
use_ai = st.sidebar.checkbox("Use OpenAI GPT-4o for Quality Review", value=False)
auto_fix = st.sidebar.checkbox("Auto-correct Typos & Formatting", value=True)

# Pestañas principales
tab_editor, tab_upload = st.tabs(["📝 Page View Interactive Builder", "📄 Upload Existing Document"])

# ==============================================================================
# TAB 1: PAGE VIEW INTERACTIVE BUILDER (ESTADO INICIAL LIMPIO)
# ==============================================================================
with tab_editor:
    st.subheader("📝 Live Survey Builder & Page View Editor")

    # Inicialización limpia de la lista de preguntas (sin datos duros de pruebas)
    if "survey_questions" not in st.session_state:
        st.session_state.survey_questions = []

    survey_title = st.text_input("Survey Title", value="", placeholder="Enter your survey title here...")

    st.markdown("---")
    st.markdown("### 🔍 Page View Survey Items")

    if not st.session_state.survey_questions:
        st.info("💡 Your survey is currently empty. Click **'➕ Add New Question Item'** below to begin building your survey.")

    # Renderizado interactivo en fila (In-Line Page View)
    questions_to_delete = []

    for idx, q in enumerate(st.session_state.survey_questions):
        with st.expander(f"📌 Item {idx + 1} [{q.question_type.value}] - {q.question_text[:50] if q.question_text else 'Untitled'}", expanded=True):
            col_id, col_prompt, col_type, col_act = st.columns([1, 4, 2, 1])

            with col_id:
                st.write(f"**Tag:** `{q.export_tag}`")

            with col_prompt:
                q.question_text = st.text_input("Question Text", value=q.question_text, key=f"prompt_{idx}", placeholder="Enter question text...")

            with col_type:
                type_opts = [
                    "Text / Graphic (Intro)",
                    "Open Text (Single Line)",
                    "Form Field",
                    "Multiple Choice (Single)",
                    "Multiple Choice (Multiple)",
                    "Matrix Table",
                    "Rating Scale / Slider"
                ]
                curr_type_idx = 0
                if q.question_type == QuestionType.TE and q.selector == SelectorType.SL:
                    curr_type_idx = 1
                elif q.question_type == QuestionType.TE and q.selector == SelectorType.FORM:
                    curr_type_idx = 2
                elif q.question_type == QuestionType.MC and q.selector == SelectorType.SAVR:
                    curr_type_idx = 3
                elif q.question_type == QuestionType.MC and q.selector == SelectorType.MAVR:
                    curr_type_idx = 4
                elif q.question_type == QuestionType.MATRIX:
                    curr_type_idx = 5
                elif q.question_type == QuestionType.SLIDER:
                    curr_type_idx = 6

                selected_type = st.selectbox("Type", type_opts, index=curr_type_idx, key=f"type_{idx}")

                # Actualizar tipo de objeto
                if selected_type == "Text / Graphic (Intro)":
                    q.question_type, q.selector = QuestionType.DB, SelectorType.TB
                elif selected_type == "Open Text (Single Line)":
                    q.question_type, q.selector = QuestionType.TE, SelectorType.SL
                elif selected_type == "Form Field":
                    q.question_type, q.selector = QuestionType.TE, SelectorType.FORM
                elif selected_type == "Multiple Choice (Single)":
                    q.question_type, q.selector = QuestionType.MC, SelectorType.SAVR
                elif selected_type == "Multiple Choice (Multiple)":
                    q.question_type, q.selector, q.is_multiple_answer = QuestionType.MC, SelectorType.MAVR, True
                elif selected_type == "Matrix Table":
                    q.question_type, q.selector = QuestionType.MATRIX, SelectorType.PROFILE
                elif selected_type == "Rating Scale / Slider":
                    q.question_type, q.selector = QuestionType.SLIDER, SelectorType.SAHR

            with col_act:
                if st.button("🗑️ Delete", key=f"del_{idx}"):
                    questions_to_delete.append(idx)

            # Zona de Opciones, Escalas y Afirmaciones
            if q.question_type in [QuestionType.MATRIX, QuestionType.SLIDER]:
                col_stmts, col_scale = st.columns(2)
                with col_stmts:
                    curr_stmts = "\n".join([c.text for c in q.choices])
                    new_stmts = st.text_area("Statements / Rows (One per line)", value=curr_stmts, key=f"stmts_{idx}", placeholder="Statement 1\nStatement 2")
                    q.choices = [Choice(choice_id=str(i), text=s.strip()) for i, s in enumerate(new_stmts.split("\n"), 1) if s.strip()]

                with col_scale:
                    scale_name = st.selectbox("Select Corporate Scale", list(PREDEFINED_SCALES.keys()), index=0, key=f"scale_sel_{idx}")
                    if scale_name != "Custom / Manual":
                        preset_points = PREDEFINED_SCALES[scale_name]
                        q.answers = [Choice(choice_id=str(i), text=p) for i, p in enumerate(preset_points, 1)]
                        st.caption("Active Scale Points: " + ", ".join(preset_points))
                    else:
                        curr_ans = "\n".join([a.text for a in q.answers])
                        new_ans = st.text_area("Custom Scale Points (One per line)", value=curr_ans, key=f"cust_ans_{idx}", placeholder="Point 1\nPoint 2")
                        q.answers = [Choice(choice_id=str(i), text=a.strip()) for i, a in enumerate(new_ans.split("\n"), 1) if a.strip()]

            elif q.question_type == QuestionType.MC or q.selector == SelectorType.FORM:
                curr_choices = "\n".join([c.text for c in q.choices])
                new_choices = st.text_area("Choices / Sub-fields (One per line)", value=curr_choices, key=f"choices_{idx}", placeholder="Option 1\nOption 2")
                q.choices = [Choice(choice_id=str(i), text=c.strip()) for i, c in enumerate(new_choices.split("\n"), 1) if c.strip()]

    # Eliminar marcadas
    if questions_to_delete:
        for i in sorted(questions_to_delete, reverse=True):
            st.session_state.survey_questions.pop(i)
        st.rerun()

    # Controles para añadir nuevas preguntas o limpiar
    col_add, col_clr = st.columns([3, 1])
    with col_add:
        if st.button("➕ Add New Question Item", type="secondary"):
            new_cnt = len(st.session_state.survey_questions) + 1
            st.session_state.survey_questions.append(
                Question(
                    qid=f"QID{new_cnt}",
                    export_tag=f"Q{new_cnt}",
                    question_text="",
                    question_type=QuestionType.TE,
                    selector=SelectorType.SL
                )
            )
            st.rerun()

    with col_clr:
        if st.button("🗑️ Clear All Items", use_container_width=True):
            st.session_state.survey_questions = []
            st.rerun()

    st.markdown("---")

    # Botón Principal Submit
    if st.button("🚀 Submit & Process Survey Files", type="primary", use_container_width=True):
        if not st.session_state.survey_questions:
            st.warning("Please add at least one question item before submitting.")
        else:
            validated_questions = []
            for q in st.session_state.survey_questions:
                if isinstance(q, Question):
                    validated_questions.append(q)
                elif isinstance(q, dict):
                    validated_questions.append(Question(**q))
                else:
                    validated_questions.append(Question(**q.model_dump()))

            schema_active = SurveySchema(survey_name=survey_title or "Generated Survey", questions=validated_questions)

            # 1. Calidad y Revisión
            reviewer = QuestionReviewer(use_ai=use_ai, auto_fix=auto_fix)
            report = reviewer.review_survey(schema_active)

            # 2. Generación de Archivos
            out_txt = os.path.join(BASE_DIR, "Sample_Qualtrics.txt")
            out_docx = os.path.join(BASE_DIR, "Sample.docx")

            txt_builder = AdvancedTXTBuilder()
            txt_builder.build(schema=schema_active, output_file=out_txt)

            docx_builder = DocxBuilder()
            docx_builder.build(schema=schema_active, output_file=out_docx)

            st.success("🎉 Survey processed and files generated successfully!")

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                with open(out_txt, "rb") as f:
                    st.download_button("📥 Download Qualtrics File (Sample_Qualtrics.txt)", data=f, file_name="Sample_Qualtrics.txt", mime="text/plain", use_container_width=True)
            with col_d2:
                with open(out_docx, "rb") as f:
                    st.download_button("📄 Download Master Word Spec (Sample.docx)", data=f, file_name="Sample.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)

# ==============================================================================
# TAB 2: CARGA DE DOCUMENTOS
# ==============================================================================
with tab_upload:
    st.subheader("📄 Process Existing Document File")
    uploaded_file = st.file_uploader("Upload Survey Document", type=["docx", "pdf", "txt"], key="doc_up")

    if uploaded_file is not None:
        temp_input_path = os.path.join(BASE_DIR, f"temp_{uploaded_file.name}")
        out_txt = os.path.join(BASE_DIR, "Sample_Qualtrics.txt")

        with open(temp_input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.info(f"📁 Loaded file: **{uploaded_file.name}**")

        if st.button("⚡ Process Uploaded File", type="primary", key="btn_up_proc"):
            with st.spinner("Extracting text and generating files..."):
                raw_text = DocumentParser.extract_text(temp_input_path)
                analyzer = RuleSurveyAnalyzer()
                survey_schema = analyzer.analyze(raw_text)

                reviewer = QuestionReviewer(use_ai=use_ai, auto_fix=auto_fix)
                report = reviewer.review_survey(survey_schema)

                txt_builder = AdvancedTXTBuilder()
                txt_builder.build(schema=survey_schema, output_file=out_txt)

            st.success("🎉 File converted successfully!")
            with open(out_txt, "rb") as f:
                st.download_button("📥 Download Qualtrics TXT File", data=f, file_name="Sample_Qualtrics.txt", mime="text/plain", use_container_width=True)

            if os.path.exists(temp_input_path):
                os.remove(temp_input_path)