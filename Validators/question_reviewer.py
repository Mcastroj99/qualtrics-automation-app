import os
import re
import sys
from typing import List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from Core.models import SurveySchema, Question, QuestionReview, SurveyReviewReport, QuestionType
except ImportError:
    from Core.models import SurveySchema, Question, QuestionReview, SurveyReviewReport, QuestionType


class QuestionReviewer:
    """Corrige errores ortográficos y de mayúsculas preservando la pregunta original."""

    def __init__(self, use_ai: bool = False, api_key: Optional[str] = None, auto_fix: bool = True):
        self.use_ai = use_ai
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.auto_fix = auto_fix

    def review_survey(self, schema: SurveySchema) -> SurveyReviewReport:
        reviews: List[QuestionReview] = []
        issues_count = 0

        for q in schema.questions:
            review = self._review_question_rules(q)
            if review.has_issues:
                issues_count += 1
            reviews.append(review)

        return SurveyReviewReport(
            survey_name=schema.survey_name,
            total_questions=len(schema.questions),
            questions_with_issues=issues_count,
            reviews=reviews
        )

    def _fix_typos_only(self, text: str) -> str:
        if not text:
            return text
        
        text = text.strip()

        typo_map = {
            r'\bimovation\b': 'Innovation',
            r'\binnovationn\b': 'Innovation',
            r'\bteh\b': 'the',
            r'\brecieve\b': 'receive',
            r'\bseperate\b': 'separate',
            r'\buntill\b': 'until',
            r'\brefering\b': 'referring',
            r'\boptionnal\b': 'optional',
            r'\bconatct\b': 'contact'
        }

        for pattern, replacement in typo_map.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        text = re.sub(r'\s{2,}', ' ', text)

        if len(text) > 1 and text[0].islower() and text[1].isupper():
            text = text.capitalize()

        return text

    def _review_question_rules(self, q: Question) -> QuestionReview:
        grammar_issues = []
        original_prompt = q.question_text
        corrected_prompt = self._fix_typos_only(original_prompt)

        if original_prompt != corrected_prompt:
            grammar_issues.append(f"Fixed typo: '{original_prompt}' -> '{corrected_prompt}'")

        for choice in q.choices:
            orig_c = choice.text
            fixed_c = self._fix_typos_only(orig_c)
            if orig_c != fixed_c:
                grammar_issues.append(f"Fixed choice: '{orig_c}' -> '{fixed_c}'")
                if self.auto_fix:
                    choice.text = fixed_c

        for ans in q.answers:
            orig_a = ans.text
            fixed_a = self._fix_typos_only(orig_a)
            if orig_a != fixed_a:
                grammar_issues.append(f"Fixed scale answer: '{orig_a}' -> '{fixed_a}'")
                if self.auto_fix:
                    ans.text = fixed_a

        has_issues = len(grammar_issues) > 0

        if self.auto_fix:
            q.question_text = corrected_prompt

        return QuestionReview(
            qid=q.qid,
            original_text=original_prompt,
            has_issues=has_issues,
            grammar_issues=grammar_issues,
            design_suggestions=[],
            suggested_text=corrected_prompt
        )