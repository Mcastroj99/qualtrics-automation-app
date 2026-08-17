import os
from openai import OpenAI
from Core.models import SurveySchema


class SurveyAIAnalyzer:
    def __init__(self, api_key: str = None, model: str = "gpt-4o"):
        # Toma la API key del argumento o de la variable de entorno OPENAI_API_KEY
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("No se encontró una API Key de OpenAI. Por favor proporciónala o configúrala en el entorno.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model

    def analyze_text(self, survey_text: str) -> SurveySchema:
        """
        Analiza el texto de una encuesta y utiliza Structured Outputs de OpenAI
        para convertirlo directamente en un objeto SurveySchema validado por Pydantic.
        """
        system_prompt = (
            "Eres un experto arquitecto de encuestas de Qualtrics. "
            "Tu tarea es analizar el texto proporcionado, identificar todas las preguntas, "
            "sus opciones de respuesta, el tipo de pregunta (MC para Opción Múltiple, TE para Texto Abierto) "
            "y si la pregunta es obligatoria o no. "
            "Asigna identificadores de pregunta correlativos (QID1, QID2, etc.)."
        )

        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": survey_text}
            ],
            response_format=SurveySchema,
        )

        return response.choices[0].message.parsed
