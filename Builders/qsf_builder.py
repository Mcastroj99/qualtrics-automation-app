import json
from typing import Dict, Any
from Core.models import SurveySchema, QuestionType


class QSFBuilder:
    """Generador autónomo y ajustado para el esquema estricto de Qualtrics."""

    def __init__(self, template_path: str = None):
        pass

    def build(self, schema: SurveySchema, output_file: str = "Sample_Qualtrics.qsf") -> str:
        survey_id = "SV_012345678912345"
        response_set_id = "RS_012345678912345"
        block_id = "BL_default"

        block_elements = []
        sq_elements = []

        for i, q in enumerate(schema.questions, 1):
            qid = q.qid or f"QID{i}"
            is_req = "ON" if q.validation.is_required else "OFF"
            
            block_elements.append({
                "Type": "Question",
                "QuestionID": qid
            })

            payload: Dict[str, Any] = {
                "QuestionText": q.question_text,
                "DefaultChoices": "False",
                "DataExportTag": q.export_tag or f"Q{i}",
                "QuestionID": qid,
                "QuestionType": q.question_type.value,
                "Selector": q.selector.value,
                "Configuration": {
                    "QuestionDescriptionOption": "UseText"
                },
                "QuestionDescription": q.question_text,
                "Validation": {
                    "Settings": {
                        "ForceResponse": is_req,
                        "ForceResponseType": is_req,
                        "Type": "None"
                    }
                },
                "GradingData": [],
                "Language": [],
                "NextChoiceId": len(q.choices) + 1 if q.choices else 1,
                "NextAnswerId": 1,
                "QuestionJS": ""
            }

            if q.question_type == QuestionType.MC:
                payload["SubSelector"] = "TX"
                payload["Choices"] = {c.choice_id: {"Display": c.text} for c in q.choices}
                payload["ChoiceOrder"] = [c.choice_id for c in q.choices]
            elif q.question_type == QuestionType.TE:
                payload["SubSelector"] = "SL"
                payload["Choices"] = {}
                payload["ChoiceOrder"] = []

            sq_elements.append({
                "SurveyID": survey_id,
                "Element": "SQ",
                "PrimaryAttribute": qid,
                "SecondaryAttribute": q.question_text[:30],
                "TertiaryAttribute": None,
                "Payload": payload
            })

        qsf_data = {
            "SurveyEntry": {
                "SurveyID": survey_id,
                "SurveyName": schema.survey_name or "Encuesta Generada",
                "SurveyStatus": "Inactive",
                "StartDate": "0000-00-00 00:00:00",
                "EndDate": "0000-00-00 00:00:00",
                "LastModified": "2025-01-01 00:00:00",
                "BrandID": "",
                "OwnerID": "",
                "LastAccessed": "0000-00-00 00:00:00",
                "UserLanguage": schema.language or "ES",
                "ActiveResponseSet": response_set_id,
                "SurveyDescription": "",
                "SurveyOwnerID": "",
                "SurveyBrandID": "",
                "Deleted": ""
            },
            "SurveyElements": [
                {
                    "SurveyID": survey_id,
                    "Element": "BL",
                    "PrimaryAttribute": "Survey Blocks",
                    "SecondaryAttribute": None,
                    "TertiaryAttribute": None,
                    "Payload": [
                        {
                            "ID": block_id,
                            "Type": "Default",
                            "Description": "Bloque Principal",
                            "BlockElements": block_elements
                        }
                    ]
                },
                {
                    "SurveyID": survey_id,
                    "Element": "FL",
                    "PrimaryAttribute": "Survey Flow",
                    "SecondaryAttribute": None,
                    "TertiaryAttribute": None,
                    "Payload": {
                        "Type": "Root",
                        "FlowID": "FL_1",
                        "Flow": [
                            {
                                "ID": block_id,
                                "Type": "Block",
                                "FlowID": "FL_2"
                            }
                        ]
                    }
                },
                {
                    "SurveyID": survey_id,
                    "Element": "SO",
                    "PrimaryAttribute": "Survey Options",
                    "SecondaryAttribute": None,
                    "TertiaryAttribute": None,
                    "Payload": {
                        "BackButton": "false",
                        "SaveAndContinue": "true",
                        "SurveyProtection": "PublicSurvey",
                        "BallotBoxStuffingPrevention": "false",
                        "SurveyExpiryDate": "3000-01-01 00:00:00",
                        "NextButton": "  >>  ",
                        "PreviousButton": "  <<  ",
                        "SkinLibrary": "qualtrics",
                        "SkinType": "core",
                        "Skin": "qualtrics",
                        "SurveyLanguage": schema.language or "ES"
                    }
                },
                {
                    "SurveyID": survey_id,
                    "Element": "RS",
                    "PrimaryAttribute": response_set_id,
                    "SecondaryAttribute": None,
                    "TertiaryAttribute": None,
                    "Payload": {
                        "ResponseSetID": response_set_id,
                        "Name": "Default Response Set",
                        "Default": True
                    }
                },
                {
                    "SurveyID": survey_id,
                    "Element": "QC",
                    "PrimaryAttribute": "Survey Question Count",
                    "SecondaryAttribute": str(len(schema.questions)),
                    "TertiaryAttribute": None,
                    "Payload": str(len(schema.questions))
                }
            ] + sq_elements
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(qsf_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Archivo QSF válido generado con éxito: {output_file}")
        return output_file
