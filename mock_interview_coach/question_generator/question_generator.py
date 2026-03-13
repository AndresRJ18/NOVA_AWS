"""Question Generator implementation."""

from typing import Optional, List, Dict
import random
import json
import boto3
import os
from dotenv import load_dotenv

from mock_interview_coach.models import (
    Role, 
    Level, 
    Language, 
    Question, 
    TechnicalArea,
    QuestionGenerationError
)

# Load environment variables
load_dotenv()


class QuestionGenerator:
    """Selects appropriate questions based on role, level, and language.
    
    Supports both static question bank and dynamic AI-generated questions.
    """
    
    def __init__(self, use_dynamic_generation: bool = False):
        """Initialize the Question Generator with question bank.
        
        Args:
            use_dynamic_generation: If True, use Bedrock to generate questions dynamically
        """
        self._question_bank: Dict[tuple, List[Question]] = self._build_question_bank()
        self._demo_sequences: Dict[tuple, List[Question]] = self._build_demo_sequences()
        
        # Session configuration
        self._role: Optional[Role] = None
        self._level: Optional[Level] = None
        self._language: Optional[Language] = None
        self._demo_mode: bool = False
        self._use_dynamic_generation: bool = use_dynamic_generation
        
        # Session state
        self._available_questions: List[Question] = []
        self._current_index: int = 0
        self._asked_question_ids: set = set()
        
        # Bedrock client for dynamic generation
        if use_dynamic_generation:
            self._bedrock_runtime = boto3.client(
                'bedrock-runtime',
                region_name=os.getenv('AWS_REGION', 'us-east-1'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            self._model_id = "us.amazon.nova-2-lite-v1:0"
    
    def configure(
        self, 
        role: Role, 
        level: Level, 
        language: Language, 
        demo_mode: bool = False
    ) -> None:
        """Configure the generator for a session.
        
        Args:
            role: Technical role
            level: Experience level
            language: Interview language
            demo_mode: Whether to use demo mode with predefined questions
        """
        self._role = role
        self._level = level
        self._language = language
        self._demo_mode = demo_mode
        
        # Get questions for this configuration
        config_key = (role, level, language)
        
        if demo_mode:
            # Use predefined demo sequence
            if config_key not in self._demo_sequences:
                raise QuestionGenerationError(
                    f"No demo sequence available for {role.value}, {level.value}, {language.value}"
                )
            self._available_questions = self._demo_sequences[config_key].copy()
        else:
            # Use question bank
            if config_key not in self._question_bank:
                raise QuestionGenerationError(
                    f"No questions available for {role.value}, {level.value}, {language.value}"
                )
            # Shuffle questions for variety (not in demo mode)
            self._available_questions = self._question_bank[config_key].copy()
            random.shuffle(self._available_questions)
        
        self._current_index = 0
    
    def get_next_question(self) -> Optional[Question]:
        """Get the next question.
        
        Returns:
            Next question or None if no more questions
        """
        if self._current_index >= len(self._available_questions):
            return None
        
        question = self._available_questions[self._current_index]
        self._current_index += 1
        return question
    
    def generate_dynamic_question(
        self,
        difficulty_hint: str = "same",
        weak_areas: Optional[List[TechnicalArea]] = None,
        previous_questions: Optional[List[Question]] = None
    ) -> Question:
        """Generate a new question dynamically using AI.
        
        Args:
            difficulty_hint: "easier", "same", or "harder"
            weak_areas: Technical areas where candidate is struggling
            previous_questions: Previously asked questions to avoid repetition
            
        Returns:
            Dynamically generated question
            
        Raises:
            QuestionGenerationError: If generation fails
        """
        if not self._use_dynamic_generation:
            raise QuestionGenerationError("Dynamic generation not enabled")
        
        if not self._role or not self._level or not self._language:
            raise QuestionGenerationError("Generator not configured")
        
        # Build generation prompt
        prompt = self._build_generation_prompt(
            difficulty_hint,
            weak_areas,
            previous_questions
        )
        
        try:
            # Call Bedrock to generate question
            request_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                "inferenceConfig": {
                    "max_new_tokens": 800,
                    "temperature": 0.8
                }
            }
            
            response = self._bedrock_runtime.invoke_model(
                modelId=self._model_id,
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            output_text = response_body.get('output', {}).get('message', {}).get('content', [{}])[0].get('text', '')
            
            # Parse the generated question
            question = self._parse_generated_question(output_text)
            
            # Track asked questions
            self._asked_question_ids.add(question.id)
            
            return question
            
        except Exception as e:
            raise QuestionGenerationError(f"Failed to generate question: {str(e)}")
    
    def _build_generation_prompt(
        self,
        difficulty_hint: str,
        weak_areas: Optional[List[TechnicalArea]],
        previous_questions: Optional[List[Question]]
    ) -> str:
        """Build prompt for dynamic question generation."""
        
        # Determine difficulty level
        if difficulty_hint == "harder":
            target_level = "mid-level" if self._level == Level.JUNIOR else "senior"
        elif difficulty_hint == "easier":
            target_level = "junior"
        else:
            target_level = self._level.value
        
        # Focus areas
        focus_text = ""
        if weak_areas:
            areas_str = ", ".join([area.value for area in weak_areas])
            focus_text = f"\nFocus on these weak areas: {areas_str}"
        
        # Previous questions context
        prev_text = ""
        if previous_questions:
            prev_topics = [q.text[:100] for q in previous_questions[-3:]]
            prev_text = f"\nAvoid repeating these recent topics: {'; '.join(prev_topics)}"
        
        if self._language == Language.ENGLISH:
            return f"""You are an expert technical interviewer creating interview questions for a {self._role.value} position.

Generate ONE technical interview question with the following requirements:

Role: {self._role.value}
Level: {target_level}
Language: English{focus_text}{prev_text}

The question should:
1. Be specific and technical
2. Test practical knowledge
3. Be answerable in 2-3 minutes
4. Have 3-5 key concepts that should be mentioned

Format your response as JSON:
{{
  "question_text": "<the interview question>",
  "technical_area": "<one of: cloud_architecture, networking, security, containerization, infrastructure_as_code, monitoring, ci_cd>",
  "expected_concepts": ["<concept1>", "<concept2>", "<concept3>", ...]
}}

Generate a unique, relevant question now."""
        else:  # Spanish
            return f"""Eres un experto entrevistador técnico creando preguntas de entrevista para una posición de {self._role.value}.

Genera UNA pregunta técnica de entrevista con los siguientes requisitos:

Rol: {self._role.value}
Nivel: {target_level}
Idioma: Español{focus_text}{prev_text}

La pregunta debe:
1. Ser específica y técnica
2. Evaluar conocimiento práctico
3. Ser respondible en 2-3 minutos
4. Tener 3-5 conceptos clave que deberían mencionarse

Formatea tu respuesta como JSON:
{{
  "question_text": "<la pregunta de entrevista>",
  "technical_area": "<uno de: cloud_architecture, networking, security, containerization, infrastructure_as_code, monitoring, ci_cd>",
  "expected_concepts": ["<concepto1>", "<concepto2>", "<concepto3>", ...]
}}

Genera una pregunta única y relevante ahora."""
    
    def _parse_generated_question(self, response_text: str) -> Question:
        """Parse AI-generated question response."""
        try:
            # Extract JSON from response
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
            
            # Map technical area string to enum
            area_map = {
                "cloud_architecture": TechnicalArea.CLOUD_ARCHITECTURE,
                "networking": TechnicalArea.NETWORKING,
                "security": TechnicalArea.SECURITY,
                "containerization": TechnicalArea.CONTAINERIZATION,
                "infrastructure_as_code": TechnicalArea.INFRASTRUCTURE_AS_CODE,
                "monitoring": TechnicalArea.MONITORING,
                "ci_cd": TechnicalArea.CI_CD
            }
            
            technical_area = area_map.get(
                data.get('technical_area', 'cloud_architecture').lower(),
                TechnicalArea.CLOUD_ARCHITECTURE
            )
            
            # Generate unique ID
            question_id = f"dynamic_{self._role.value}_{self._level.value}_{len(self._asked_question_ids)}"
            
            return Question(
                id=question_id,
                text=data.get('question_text', ''),
                role=self._role,
                level=self._level,
                language=self._language,
                technical_area=technical_area,
                expected_concepts=data.get('expected_concepts', [])
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            raise QuestionGenerationError(f"Failed to parse generated question: {str(e)}")
    
    def get_question_count(self) -> int:
        """Get the total number of questions available.
        
        Returns:
            Question count
        """
        return len(self._available_questions)
    
    def reset(self) -> None:
        """Reset the generator state."""
        self._current_index = 0
        if not self._demo_mode and self._available_questions:
            # Re-shuffle for non-demo mode
            random.shuffle(self._available_questions)
    
    def _build_question_bank(self) -> Dict[tuple, List[Question]]:
        """Build the question bank organized by role, level, and language.
        
        Returns:
            Dictionary mapping (role, level, language) to list of questions
        """
        bank = {}
        
        # Cloud Engineer Junior - English
        bank[(Role.CLOUD_ENGINEER, Level.JUNIOR, Language.ENGLISH)] = [
            Question(
                id="ce_jr_en_001",
                text="What is cloud computing and what are its main benefits?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["on-demand resources", "scalability", "pay-as-you-go", "elasticity"]
            ),
            Question(
                id="ce_jr_en_002",
                text="Can you explain the difference between IaaS, PaaS, and SaaS?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["Infrastructure as a Service", "Platform as a Service", "Software as a Service", "abstraction levels"]
            ),
            Question(
                id="ce_jr_en_003",
                text="What is a VPC and why would you use one?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.NETWORKING,
                expected_concepts=["Virtual Private Cloud", "network isolation", "subnets", "security"]
            ),
            Question(
                id="ce_jr_en_004",
                text="Explain the difference between a security group and a network ACL in AWS.",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.SECURITY,
                expected_concepts=["stateful vs stateless", "instance level vs subnet level", "allow rules", "deny rules"]
            ),
            Question(
                id="ce_jr_en_005",
                text="What is Docker and what problem does it solve?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.CONTAINERIZATION,
                expected_concepts=["containerization", "portability", "consistency", "isolation"]
            ),
            Question(
                id="ce_jr_en_006",
                text="What is the difference between horizontal and vertical scaling?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["scale out vs scale up", "adding instances", "increasing resources", "load distribution"]
            ),
            Question(
                id="ce_jr_en_007",
                text="What is an S3 bucket and what are some common use cases?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["object storage", "static website hosting", "backup", "data lake"]
            ),
            Question(
                id="ce_jr_en_008",
                text="What is CloudWatch and how would you use it?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.MONITORING,
                expected_concepts=["monitoring", "metrics", "logs", "alarms", "dashboards"]
            ),
            Question(
                id="ce_jr_en_009",
                text="What is Infrastructure as Code and why is it important?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.INFRASTRUCTURE_AS_CODE,
                expected_concepts=["automation", "version control", "reproducibility", "consistency"]
            ),
            Question(
                id="ce_jr_en_010",
                text="Can you explain what an EC2 instance is and name a few instance types?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["virtual machine", "compute resource", "t2", "m5", "c5", "instance families"]
            ),
            Question(
                id="ce_jr_en_011",
                text="What is a load balancer and why would you use one?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.NETWORKING,
                expected_concepts=["traffic distribution", "high availability", "health checks", "ALB", "NLB"]
            ),
            Question(
                id="ce_jr_en_012",
                text="Explain the concept of auto-scaling in cloud computing.",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["automatic scaling", "metrics-based", "cost optimization", "elasticity"]
            ),
            Question(
                id="ce_jr_en_013",
                text="What is the difference between RDS and DynamoDB?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["relational database", "NoSQL", "SQL", "key-value store", "use cases"]
            ),
            Question(
                id="ce_jr_en_014",
                text="What is IAM and why is it important in AWS?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.SECURITY,
                expected_concepts=["Identity and Access Management", "users", "roles", "policies", "permissions"]
            ),
            Question(
                id="ce_jr_en_015",
                text="Can you explain what a CDN is and its benefits?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.NETWORKING,
                expected_concepts=["Content Delivery Network", "edge locations", "latency reduction", "caching"]
            ),
            Question(
                id="ce_jr_en_016",
                text="What is the difference between a public and private subnet?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.NETWORKING,
                expected_concepts=["internet gateway", "NAT gateway", "routing", "security"]
            ),
            Question(
                id="ce_jr_en_017",
                text="What is Lambda and what are serverless functions?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["serverless", "event-driven", "pay per execution", "no server management"]
            ),
            Question(
                id="ce_jr_en_018",
                text="Explain what a snapshot is and when you would use it.",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["backup", "point-in-time copy", "EBS", "disaster recovery"]
            ),
            Question(
                id="ce_jr_en_019",
                text="What is the difference between EBS and EFS?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["block storage", "file storage", "single instance", "multiple instances", "shared storage"]
            ),
            Question(
                id="ce_jr_en_020",
                text="What is Route 53 and what does it do?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.NETWORKING,
                expected_concepts=["DNS", "domain name system", "routing policies", "health checks"]
            ),
            Question(
                id="ce_jr_en_021",
                text="Can you explain what regions and availability zones are?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["geographic locations", "data centers", "high availability", "fault tolerance"]
            ),
            Question(
                id="ce_jr_en_022",
                text="What is CloudFormation and how does it help?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.INFRASTRUCTURE_AS_CODE,
                expected_concepts=["IaC", "templates", "stacks", "automation", "declarative"]
            ),
            Question(
                id="ce_jr_en_023",
                text="What is the principle of least privilege in security?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.SECURITY,
                expected_concepts=["minimal permissions", "access control", "security best practice", "IAM policies"]
            ),
            Question(
                id="ce_jr_en_024",
                text="Explain what a container orchestration platform is.",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.CONTAINERIZATION,
                expected_concepts=["Kubernetes", "ECS", "container management", "scaling", "deployment"]
            ),
            Question(
                id="ce_jr_en_025",
                text="What is the difference between stateful and stateless applications?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["session data", "scalability", "state management", "distributed systems"]
            ),
            Question(
                id="ce_jr_en_026",
                text="What is API Gateway and what problem does it solve?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["API management", "REST", "authentication", "rate limiting", "routing"]
            ),
            Question(
                id="ce_jr_en_027",
                text="Can you explain what encryption at rest and in transit means?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.SECURITY,
                expected_concepts=["data encryption", "SSL/TLS", "stored data", "transmitted data", "KMS"]
            ),
            Question(
                id="ce_jr_en_028",
                text="What is a bastion host and when would you use one?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.SECURITY,
                expected_concepts=["jump server", "secure access", "private resources", "SSH"]
            ),
            Question(
                id="ce_jr_en_029",
                text="Explain what blue-green deployment is.",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.CI_CD,
                expected_concepts=["deployment strategy", "zero downtime", "rollback", "two environments"]
            ),
            Question(
                id="ce_jr_en_030",
                text="What is the difference between CloudWatch Logs and CloudTrail?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.MONITORING,
                expected_concepts=["application logs", "API calls", "audit trail", "monitoring vs auditing"]
            ),
        ]
        
        # Cloud Engineer Junior - Spanish
        bank[(Role.CLOUD_ENGINEER, Level.JUNIOR, Language.SPANISH)] = [
            Question(
                id="ce_jr_es_001",
                text="¿Qué es la computación en la nube y cuáles son sus principales beneficios?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["recursos bajo demanda", "escalabilidad", "pago por uso", "elasticidad"]
            ),
            Question(
                id="ce_jr_es_002",
                text="¿Puedes explicar la diferencia entre IaaS, PaaS y SaaS?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["Infraestructura como Servicio", "Plataforma como Servicio", "Software como Servicio", "niveles de abstracción"]
            ),
            Question(
                id="ce_jr_es_003",
                text="¿Qué es una VPC y por qué la usarías?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.NETWORKING,
                expected_concepts=["Nube Privada Virtual", "aislamiento de red", "subredes", "seguridad"]
            ),
            Question(
                id="ce_jr_es_004",
                text="Explica la diferencia entre un grupo de seguridad y una ACL de red en AWS.",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.SECURITY,
                expected_concepts=["con estado vs sin estado", "nivel de instancia vs nivel de subred", "reglas de permiso", "reglas de denegación"]
            ),
            Question(
                id="ce_jr_es_005",
                text="¿Qué es Docker y qué problema resuelve?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.CONTAINERIZATION,
                expected_concepts=["contenedorización", "portabilidad", "consistencia", "aislamiento"]
            ),
            Question(
                id="ce_jr_es_006",
                text="¿Cuál es la diferencia entre escalado horizontal y vertical?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["escalar hacia afuera vs escalar hacia arriba", "agregar instancias", "aumentar recursos", "distribución de carga"]
            ),
            Question(
                id="ce_jr_es_007",
                text="¿Qué es un bucket de S3 y cuáles son algunos casos de uso comunes?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["almacenamiento de objetos", "hosting de sitios estáticos", "respaldo", "lago de datos"]
            ),
            Question(
                id="ce_jr_es_008",
                text="¿Qué es CloudWatch y cómo lo usarías?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.MONITORING,
                expected_concepts=["monitoreo", "métricas", "logs", "alarmas", "dashboards"]
            ),
            Question(
                id="ce_jr_es_009",
                text="¿Qué es Infraestructura como Código y por qué es importante?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.INFRASTRUCTURE_AS_CODE,
                expected_concepts=["automatización", "control de versiones", "reproducibilidad", "consistencia"]
            ),
            Question(
                id="ce_jr_es_010",
                text="¿Puedes explicar qué es una instancia EC2 y nombrar algunos tipos de instancia?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["máquina virtual", "recurso de cómputo", "t2", "m5", "c5", "familias de instancias"]
            ),
            Question(
                id="ce_jr_es_011",
                text="¿Qué es un balanceador de carga y por qué lo usarías?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.NETWORKING,
                expected_concepts=["distribución de tráfico", "alta disponibilidad", "health checks", "ALB", "NLB"]
            ),
            Question(
                id="ce_jr_es_012",
                text="Explica el concepto de auto-escalado en computación en la nube.",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["escalado automático", "basado en métricas", "optimización de costos", "elasticidad"]
            ),
            Question(
                id="ce_jr_es_013",
                text="¿Cuál es la diferencia entre RDS y DynamoDB?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["base de datos relacional", "NoSQL", "SQL", "almacén clave-valor", "casos de uso"]
            ),
            Question(
                id="ce_jr_es_014",
                text="¿Qué es IAM y por qué es importante en AWS?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.SECURITY,
                expected_concepts=["Gestión de Identidad y Acceso", "usuarios", "roles", "políticas", "permisos"]
            ),
            Question(
                id="ce_jr_es_015",
                text="¿Puedes explicar qué es un CDN y sus beneficios?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.NETWORKING,
                expected_concepts=["Red de Distribución de Contenido", "ubicaciones edge", "reducción de latencia", "caché"]
            ),
            Question(
                id="ce_jr_es_016",
                text="¿Cuál es la diferencia entre una subred pública y privada?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.NETWORKING,
                expected_concepts=["internet gateway", "NAT gateway", "enrutamiento", "seguridad"]
            ),
            Question(
                id="ce_jr_es_017",
                text="¿Qué es Lambda y qué son las funciones serverless?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["sin servidor", "basado en eventos", "pago por ejecución", "sin gestión de servidores"]
            ),
            Question(
                id="ce_jr_es_018",
                text="Explica qué es un snapshot y cuándo lo usarías.",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["respaldo", "copia en un punto en el tiempo", "EBS", "recuperación ante desastres"]
            ),
            Question(
                id="ce_jr_es_019",
                text="¿Cuál es la diferencia entre EBS y EFS?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["almacenamiento de bloques", "almacenamiento de archivos", "instancia única", "múltiples instancias", "almacenamiento compartido"]
            ),
            Question(
                id="ce_jr_es_020",
                text="¿Qué es Route 53 y qué hace?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.NETWORKING,
                expected_concepts=["DNS", "sistema de nombres de dominio", "políticas de enrutamiento", "health checks"]
            ),
            Question(
                id="ce_jr_es_021",
                text="¿Puedes explicar qué son las regiones y zonas de disponibilidad?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["ubicaciones geográficas", "centros de datos", "alta disponibilidad", "tolerancia a fallos"]
            ),
            Question(
                id="ce_jr_es_022",
                text="¿Qué es CloudFormation y cómo ayuda?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.INFRASTRUCTURE_AS_CODE,
                expected_concepts=["IaC", "plantillas", "stacks", "automatización", "declarativo"]
            ),
            Question(
                id="ce_jr_es_023",
                text="¿Qué es el principio de mínimo privilegio en seguridad?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.SECURITY,
                expected_concepts=["permisos mínimos", "control de acceso", "mejor práctica de seguridad", "políticas IAM"]
            ),
            Question(
                id="ce_jr_es_024",
                text="Explica qué es una plataforma de orquestación de contenedores.",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.CONTAINERIZATION,
                expected_concepts=["Kubernetes", "ECS", "gestión de contenedores", "escalado", "despliegue"]
            ),
            Question(
                id="ce_jr_es_025",
                text="¿Cuál es la diferencia entre aplicaciones con estado y sin estado?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["datos de sesión", "escalabilidad", "gestión de estado", "sistemas distribuidos"]
            ),
            Question(
                id="ce_jr_es_026",
                text="¿Qué es API Gateway y qué problema resuelve?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["gestión de API", "REST", "autenticación", "limitación de tasa", "enrutamiento"]
            ),
            Question(
                id="ce_jr_es_027",
                text="¿Puedes explicar qué significa cifrado en reposo y en tránsito?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.SECURITY,
                expected_concepts=["cifrado de datos", "SSL/TLS", "datos almacenados", "datos transmitidos", "KMS"]
            ),
            Question(
                id="ce_jr_es_028",
                text="¿Qué es un bastion host y cuándo lo usarías?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.SECURITY,
                expected_concepts=["servidor de salto", "acceso seguro", "recursos privados", "SSH"]
            ),
            Question(
                id="ce_jr_es_029",
                text="Explica qué es el despliegue blue-green.",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.CI_CD,
                expected_concepts=["estrategia de despliegue", "cero tiempo de inactividad", "rollback", "dos entornos"]
            ),
            Question(
                id="ce_jr_es_030",
                text="¿Cuál es la diferencia entre CloudWatch Logs y CloudTrail?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.MONITORING,
                expected_concepts=["logs de aplicación", "llamadas API", "registro de auditoría", "monitoreo vs auditoría"]
            ),
        ]
        
        return bank
    
    def _build_demo_sequences(self) -> Dict[tuple, List[Question]]:
        """Build predefined demo sequences for deterministic testing.
        
        Returns:
            Dictionary mapping (role, level, language) to demo question sequences
        """
        sequences = {}
        
        # Cloud Engineer Junior - English (Demo)
        sequences[(Role.CLOUD_ENGINEER, Level.JUNIOR, Language.ENGLISH)] = [
            Question(
                id="ce_jr_en_demo_001",
                text="What is cloud computing and what are its main benefits?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["on-demand resources", "scalability", "pay-as-you-go", "elasticity"]
            ),
            Question(
                id="ce_jr_en_demo_002",
                text="Can you explain the difference between IaaS, PaaS, and SaaS?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["Infrastructure as a Service", "Platform as a Service", "Software as a Service", "abstraction levels"]
            ),
            Question(
                id="ce_jr_en_demo_003",
                text="What is a VPC and why would you use one?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.NETWORKING,
                expected_concepts=["Virtual Private Cloud", "network isolation", "subnets", "security"]
            ),
            Question(
                id="ce_jr_en_demo_004",
                text="Explain the difference between a security group and a network ACL in AWS.",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.SECURITY,
                expected_concepts=["stateful vs stateless", "instance level vs subnet level", "allow rules", "deny rules"]
            ),
            Question(
                id="ce_jr_en_demo_005",
                text="What is Docker and what problem does it solve?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.ENGLISH,
                technical_area=TechnicalArea.CONTAINERIZATION,
                expected_concepts=["containerization", "portability", "consistency", "isolation"]
            ),
        ]
        
        # Cloud Engineer Junior - Spanish (Demo)
        sequences[(Role.CLOUD_ENGINEER, Level.JUNIOR, Language.SPANISH)] = [
            Question(
                id="ce_jr_es_demo_001",
                text="¿Qué es la computación en la nube y cuáles son sus principales beneficios?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["recursos bajo demanda", "escalabilidad", "pago por uso", "elasticidad"]
            ),
            Question(
                id="ce_jr_es_demo_002",
                text="¿Puedes explicar la diferencia entre IaaS, PaaS y SaaS?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
                expected_concepts=["Infraestructura como Servicio", "Plataforma como Servicio", "Software como Servicio", "niveles de abstracción"]
            ),
            Question(
                id="ce_jr_es_demo_003",
                text="¿Qué es una VPC y por qué la usarías?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.NETWORKING,
                expected_concepts=["Nube Privada Virtual", "aislamiento de red", "subredes", "seguridad"]
            ),
            Question(
                id="ce_jr_es_demo_004",
                text="Explica la diferencia entre un grupo de seguridad y una ACL de red en AWS.",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.SECURITY,
                expected_concepts=["con estado vs sin estado", "nivel de instancia vs nivel de subred", "reglas de permiso", "reglas de denegación"]
            ),
            Question(
                id="ce_jr_es_demo_005",
                text="¿Qué es Docker y qué problema resuelve?",
                role=Role.CLOUD_ENGINEER,
                level=Level.JUNIOR,
                language=Language.SPANISH,
                technical_area=TechnicalArea.CONTAINERIZATION,
                expected_concepts=["contenedorización", "portabilidad", "consistencia", "aislamiento"]
            ),
        ]
        
        return sequences
