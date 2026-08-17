from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    MC = "MC"          # Multiple Choice
    TE = "TE"          # Text Entry
    SLIDER = "Slider"  # Slider / Scale
    MATRIX = "Matrix"  # Matrix Table
    DB = "DB"          # Text / Graphic (Descriptive Block)


class SelectorType(str, Enum):
    SAVR = "SAVR"        # Single Answer Vertical
    MAVR = "MAVR"        # Multiple Answer Vertical
    SAHR = "SAHR"        # Single Answer Horizontal
    SL = "SL"            # Single Line (Open Text)
    ML = "ML"            # Multi-line / Essay
    FORM = "FORM"        # Form Field
    HSLIDER = "HSLIDER"  # Horizontal Slider
    TB = "TB"            # Text Block
    PROFILE = "Profile"  # Matrix Table


class Choice(BaseModel):
    choice_id: str = Field(..., description="ID interno")
    text: str = Field(..., description="Texto visible")


class Validation(BaseModel):
    is_required: bool = Field(default=False)


class Question(BaseModel):
    qid: str
    export_tag: Optional[str] = None
    question_text: str
    question_type: QuestionType
    selector: SelectorType = SelectorType.SAVR
    is_multiple_answer: bool = False
    slider_min: int = 1
    slider_max: int = 7
    labels: Dict[str, str] = Field(default_factory=dict)
    choices: List[Choice] = Field(default_factory=list)      # Filas / Afirmaciones / Opciones
    answers: List[Choice] = Field(default_factory=list)      # Columnas / Puntos de Escala para Matriz
    validation: Validation = Field(default_factory=Validation)


class QuestionReview(BaseModel):
    qid: str
    original_text: str
    has_issues: bool
    grammar_issues: List[str] = Field(default_factory=list)
    design_suggestions: List[str] = Field(default_factory=list)
    suggested_text: str


class SurveyReviewReport(BaseModel):
    survey_name: str
    total_questions: int
    questions_with_issues: int
    reviews: List[QuestionReview] = Field(default_factory=list)


class SurveySchema(BaseModel):
    survey_name: str = Field(default="Encuesta Generada")
    language: str = Field(default="EN")
    questions: List[Question] = Field(default_factory=list)