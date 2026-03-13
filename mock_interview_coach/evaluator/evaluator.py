"""Evaluator implementation using AWS Bedrock Nova Lite."""

import json
import os
from typing import Optional
import boto3
from dotenv import load_dotenv

from mock_interview_coach.models import (
    Question,
    Evaluation,
    Language,
    EvaluationTimeoutError
)

# Load environment variables
load_dotenv()


class Evaluator:
    """Analyzes user responses and generates feedback using AWS Bedrock Nova Lite."""
    
    def __init__(self):
        """Initialize the Evaluator with AWS Bedrock client."""
        self._bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self._model_id = "us.amazon.nova-2-lite-v1:0"
    
    def evaluate_response(
        self, 
        question: Question, 
        response: str, 
        language: Language
    ) -> Evaluation:
        """Evaluate a user's response to a question.
        
        Args:
            question: The question that was asked
            response: The user's response
            language: Language for feedback
            
        Returns:
            Evaluation with score, concepts analysis, and feedback
            
        Raises:
            EvaluationTimeoutError: If evaluation takes too long
        """
        # Build evaluation prompt
        prompt = self._build_evaluation_prompt(question, response, language)
        
        try:
            # Call Nova Lite for evaluation
            request_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                "inferenceConfig": {
                    "max_new_tokens": 1000,
                    "temperature": 0.7
                }
            }
            
            response_obj = self._bedrock_runtime.invoke_model(
                modelId=self._model_id,
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            response_body = json.loads(response_obj['body'].read())
            output_text = response_body.get('output', {}).get('message', {}).get('content', [{}])[0].get('text', '')
            
            # Parse the evaluation response
            evaluation = self._parse_evaluation_response(output_text, question)
            
            return evaluation
            
        except Exception as e:
            raise EvaluationTimeoutError(f"Evaluation failed: {str(e)}")
    
    def generate_feedback(self, evaluation: Evaluation, language: Language) -> str:
        """Generate feedback text from an evaluation.
        
        Args:
            evaluation: The evaluation result
            language: Language for feedback
            
        Returns:
            Feedback text
        """
        # Feedback is already generated in evaluate_response
        return evaluation.feedback_text
    
    def _build_evaluation_prompt(
        self, 
        question: Question, 
        response: str, 
        language: Language
    ) -> str:
        """Build the evaluation prompt for Nova Lite with detailed structured feedback."""
        if language == Language.ENGLISH:
            return f"""You are an expert technical interviewer evaluating a candidate's response for a {question.role.value} position.

Question: {question.text}

Expected concepts: {', '.join(question.expected_concepts)}

Technical Area: {question.technical_area.value}

Candidate's response: {response}

Please evaluate this response and provide detailed structured feedback:

1. Score (0-100): Based on correctness, completeness, and clarity
2. Correct concepts: Concepts from the expected list that were correctly explained
3. Missing concepts: Important concepts that weren't mentioned
4. Strengths: Specific things the candidate did well (2-4 bullet points)
5. Weaknesses: Areas that need improvement (2-4 bullet points)
6. Recommended topics: 3-5 specific topics to study based on gaps identified

Format your response as JSON:
{{
  "score": <number 0-100>,
  "correct_concepts": [<list of strings>],
  "missing_concepts": [<list of strings>],
  "strengths": [<list of 2-4 specific strengths>],
  "weaknesses": [<list of 2-4 specific weaknesses>],
  "recommended_topics": [<list of 3-5 topics to study>],
  "feedback": "<brief summary feedback>"
}}

Be specific and constructive in your feedback. Focus on technical accuracy and depth of understanding."""
        else:  # Spanish
            return f"""Eres un experto entrevistador técnico evaluando la respuesta de un candidato para una posición de {question.role.value}.

Pregunta: {question.text}

Conceptos esperados: {', '.join(question.expected_concepts)}

Área técnica: {question.technical_area.value}

Respuesta del candidato: {response}

Por favor evalúa esta respuesta y proporciona retroalimentación estructurada detallada:

1. Puntuación (0-100): Basada en corrección, completitud y claridad
2. Conceptos correctos: Conceptos de la lista esperada que fueron explicados correctamente
3. Conceptos faltantes: Conceptos importantes que no se mencionaron
4. Fortalezas: Cosas específicas que el candidato hizo bien (2-4 puntos)
5. Debilidades: Áreas que necesitan mejora (2-4 puntos)
6. Temas recomendados: 3-5 temas específicos para estudiar basados en las brechas identificadas

Formatea tu respuesta como JSON:
{{
  "score": <número 0-100>,
  "correct_concepts": [<lista de strings>],
  "missing_concepts": [<lista de strings>],
  "strengths": [<lista de 2-4 fortalezas específicas>],
  "weaknesses": [<lista de 2-4 debilidades específicas>],
  "recommended_topics": [<lista de 3-5 temas para estudiar>],
  "feedback": "<resumen breve de retroalimentación>"
}}

Sé específico y constructivo en tu retroalimentación. Enfócate en precisión técnica y profundidad de comprensión."""
    
    def _parse_evaluation_response(
        self, 
        response_text: str, 
        question: Question
    ) -> Evaluation:
        """Parse the evaluation response from Nova Lite with structured feedback."""
        try:
            # Try to extract JSON from the response
            # Nova might wrap it in markdown code blocks
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_text = response_text[start:end].strip()
            else:
                json_text = response_text.strip()
            
            data = json.loads(json_text)
            
            # Extract and validate score
            score = int(data.get('score', 50))
            score = max(0, min(100, score))  # Clamp to [0, 100]
            
            return Evaluation(
                score=score,
                correct_concepts=data.get('correct_concepts', []),
                missing_concepts=data.get('missing_concepts', []),
                incorrect_statements=data.get('incorrect_statements', []),
                feedback_text=data.get('feedback', ''),
                technical_area=question.technical_area,
                strengths=data.get('strengths', []),
                weaknesses=data.get('weaknesses', []),
                recommended_topics=data.get('recommended_topics', [])
            )
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # Fallback: create a basic evaluation
            return Evaluation(
                score=50,
                correct_concepts=[],
                missing_concepts=question.expected_concepts,
                incorrect_statements=[],
                feedback_text=f"Unable to parse evaluation response: {str(e)}",
                technical_area=question.technical_area,
                strengths=[],
                weaknesses=["Unable to generate detailed feedback"],
                recommended_topics=question.expected_concepts[:3]
            )
