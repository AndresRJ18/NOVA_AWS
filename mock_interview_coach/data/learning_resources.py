"""Learning resource database for Mock Interview Coach."""

from typing import Dict, List
from mock_interview_coach.models import Resource, ResourceType, Language, TechnicalArea


# Learning resources organized by technical area and language
LEARNING_RESOURCES: Dict[TechnicalArea, Dict[Language, List[Resource]]] = {
    TechnicalArea.CLOUD_ARCHITECTURE: {
        Language.ENGLISH: [
            Resource(
                title="AWS Cloud Practitioner Essentials",
                url="https://aws.amazon.com/training/digital/aws-cloud-practitioner-essentials/",
                type=ResourceType.TUTORIAL,
                language=Language.ENGLISH,
                is_free=True,
                description="Free AWS training covering cloud computing fundamentals"
            ),
            Resource(
                title="Google Cloud Architecture Framework",
                url="https://cloud.google.com/architecture/framework",
                type=ResourceType.DOCUMENTATION,
                language=Language.ENGLISH,
                is_free=True,
                description="Best practices for cloud architecture design"
            ),
            Resource(
                title="Cloud Computing Concepts on Coursera",
                url="https://www.coursera.org/learn/cloud-computing",
                type=ResourceType.TUTORIAL,
                language=Language.ENGLISH,
                is_free=True,
                description="University course on cloud computing fundamentals"
            ),
            Resource(
                title="AWS Well-Architected Framework",
                url="https://aws.amazon.com/architecture/well-architected/",
                type=ResourceType.DOCUMENTATION,
                language=Language.ENGLISH,
                is_free=True,
                description="AWS best practices for building cloud applications"
            ),
        ],
        Language.SPANISH: [
            Resource(
                title="Fundamentos de AWS Cloud Practitioner",
                url="https://aws.amazon.com/es/training/digital/aws-cloud-practitioner-essentials/",
                type=ResourceType.TUTORIAL,
                language=Language.SPANISH,
                is_free=True,
                description="Capacitación gratuita de AWS sobre fundamentos de computación en la nube"
            ),
            Resource(
                title="Introducción a la Computación en la Nube - Google",
                url="https://cloud.google.com/learn/what-is-cloud-computing?hl=es",
                type=ResourceType.DOCUMENTATION,
                language=Language.SPANISH,
                is_free=True,
                description="Documentación de Google Cloud sobre conceptos básicos"
            ),
            Resource(
                title="Arquitectura en la Nube - AWS",
                url="https://aws.amazon.com/es/architecture/",
                type=ResourceType.DOCUMENTATION,
                language=Language.SPANISH,
                is_free=True,
                description="Guías de arquitectura y mejores prácticas de AWS"
            ),
        ],
    },
    TechnicalArea.NETWORKING: {
        Language.ENGLISH: [
            Resource(
                title="AWS VPC Documentation",
                url="https://docs.aws.amazon.com/vpc/",
                type=ResourceType.DOCUMENTATION,
                language=Language.ENGLISH,
                is_free=True,
                description="Official AWS VPC documentation and tutorials"
            ),
            Resource(
                title="Networking Fundamentals for Cloud",
                url="https://www.cloudflare.com/learning/network-layer/what-is-the-network-layer/",
                type=ResourceType.TUTORIAL,
                language=Language.ENGLISH,
                is_free=True,
                description="Cloud networking concepts explained"
            ),
            Resource(
                title="VPC Hands-on Labs",
                url="https://aws.amazon.com/getting-started/hands-on/",
                type=ResourceType.PRACTICE,
                language=Language.ENGLISH,
                is_free=True,
                description="Practical exercises for AWS VPC configuration"
            ),
        ],
        Language.SPANISH: [
            Resource(
                title="Documentación de AWS VPC",
                url="https://docs.aws.amazon.com/es_es/vpc/",
                type=ResourceType.DOCUMENTATION,
                language=Language.SPANISH,
                is_free=True,
                description="Documentación oficial de AWS VPC en español"
            ),
            Resource(
                title="Fundamentos de Redes en la Nube",
                url="https://aws.amazon.com/es/what-is/computer-networking/",
                type=ResourceType.TUTORIAL,
                language=Language.SPANISH,
                is_free=True,
                description="Conceptos de redes explicados por AWS"
            ),
            Resource(
                title="Laboratorios Prácticos de VPC",
                url="https://aws.amazon.com/es/getting-started/hands-on/",
                type=ResourceType.PRACTICE,
                language=Language.SPANISH,
                is_free=True,
                description="Ejercicios prácticos para configuración de VPC"
            ),
        ],
    },
    TechnicalArea.SECURITY: {
        Language.ENGLISH: [
            Resource(
                title="AWS Security Best Practices",
                url="https://aws.amazon.com/architecture/security-identity-compliance/",
                type=ResourceType.DOCUMENTATION,
                language=Language.ENGLISH,
                is_free=True,
                description="AWS security guidelines and best practices"
            ),
            Resource(
                title="Cloud Security Fundamentals",
                url="https://www.coursera.org/learn/cloud-security-basics",
                type=ResourceType.TUTORIAL,
                language=Language.ENGLISH,
                is_free=True,
                description="Introduction to cloud security concepts"
            ),
            Resource(
                title="Security Groups vs NACLs",
                url="https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html",
                type=ResourceType.DOCUMENTATION,
                language=Language.ENGLISH,
                is_free=True,
                description="Understanding AWS network security controls"
            ),
        ],
        Language.SPANISH: [
            Resource(
                title="Mejores Prácticas de Seguridad en AWS",
                url="https://aws.amazon.com/es/architecture/security-identity-compliance/",
                type=ResourceType.DOCUMENTATION,
                language=Language.SPANISH,
                is_free=True,
                description="Guías de seguridad de AWS"
            ),
            Resource(
                title="Fundamentos de Seguridad en la Nube",
                url="https://aws.amazon.com/es/security/",
                type=ResourceType.TUTORIAL,
                language=Language.SPANISH,
                is_free=True,
                description="Introducción a conceptos de seguridad en la nube"
            ),
            Resource(
                title="Grupos de Seguridad vs ACLs de Red",
                url="https://docs.aws.amazon.com/es_es/vpc/latest/userguide/vpc-security-groups.html",
                type=ResourceType.DOCUMENTATION,
                language=Language.SPANISH,
                is_free=True,
                description="Controles de seguridad de red en AWS"
            ),
        ],
    },
    TechnicalArea.CONTAINERIZATION: {
        Language.ENGLISH: [
            Resource(
                title="Docker Getting Started",
                url="https://docs.docker.com/get-started/",
                type=ResourceType.TUTORIAL,
                language=Language.ENGLISH,
                is_free=True,
                description="Official Docker tutorial for beginners"
            ),
            Resource(
                title="Kubernetes Basics",
                url="https://kubernetes.io/docs/tutorials/kubernetes-basics/",
                type=ResourceType.TUTORIAL,
                language=Language.ENGLISH,
                is_free=True,
                description="Interactive Kubernetes tutorial"
            ),
            Resource(
                title="Container Best Practices",
                url="https://cloud.google.com/architecture/best-practices-for-building-containers",
                type=ResourceType.DOCUMENTATION,
                language=Language.ENGLISH,
                is_free=True,
                description="Google Cloud container best practices"
            ),
        ],
        Language.SPANISH: [
            Resource(
                title="Introducción a Docker",
                url="https://docs.docker.com/get-started/",
                type=ResourceType.TUTORIAL,
                language=Language.SPANISH,
                is_free=True,
                description="Tutorial oficial de Docker para principiantes"
            ),
            Resource(
                title="Fundamentos de Kubernetes",
                url="https://kubernetes.io/es/docs/tutorials/kubernetes-basics/",
                type=ResourceType.TUTORIAL,
                language=Language.SPANISH,
                is_free=True,
                description="Tutorial interactivo de Kubernetes"
            ),
            Resource(
                title="Mejores Prácticas de Contenedores",
                url="https://cloud.google.com/architecture/best-practices-for-building-containers?hl=es",
                type=ResourceType.DOCUMENTATION,
                language=Language.SPANISH,
                is_free=True,
                description="Mejores prácticas de Google Cloud para contenedores"
            ),
        ],
    },
    TechnicalArea.MONITORING: {
        Language.ENGLISH: [
            Resource(
                title="AWS CloudWatch Documentation",
                url="https://docs.aws.amazon.com/cloudwatch/",
                type=ResourceType.DOCUMENTATION,
                language=Language.ENGLISH,
                is_free=True,
                description="Official AWS CloudWatch documentation"
            ),
            Resource(
                title="Monitoring Best Practices",
                url="https://aws.amazon.com/cloudwatch/getting-started/",
                type=ResourceType.TUTORIAL,
                language=Language.ENGLISH,
                is_free=True,
                description="Getting started with CloudWatch monitoring"
            ),
            Resource(
                title="Observability Fundamentals",
                url="https://www.datadoghq.com/knowledge-center/observability/",
                type=ResourceType.TUTORIAL,
                language=Language.ENGLISH,
                is_free=True,
                description="Introduction to observability concepts"
            ),
        ],
        Language.SPANISH: [
            Resource(
                title="Documentación de AWS CloudWatch",
                url="https://docs.aws.amazon.com/es_es/cloudwatch/",
                type=ResourceType.DOCUMENTATION,
                language=Language.SPANISH,
                is_free=True,
                description="Documentación oficial de AWS CloudWatch"
            ),
            Resource(
                title="Mejores Prácticas de Monitoreo",
                url="https://aws.amazon.com/es/cloudwatch/getting-started/",
                type=ResourceType.TUTORIAL,
                language=Language.SPANISH,
                is_free=True,
                description="Introducción al monitoreo con CloudWatch"
            ),
            Resource(
                title="Fundamentos de Observabilidad",
                url="https://aws.amazon.com/es/what-is/observability/",
                type=ResourceType.TUTORIAL,
                language=Language.SPANISH,
                is_free=True,
                description="Conceptos de observabilidad en la nube"
            ),
        ],
    },
    TechnicalArea.INFRASTRUCTURE_AS_CODE: {
        Language.ENGLISH: [
            Resource(
                title="Terraform Getting Started",
                url="https://developer.hashicorp.com/terraform/tutorials/aws-get-started",
                type=ResourceType.TUTORIAL,
                language=Language.ENGLISH,
                is_free=True,
                description="Official Terraform tutorial for AWS"
            ),
            Resource(
                title="AWS CloudFormation Documentation",
                url="https://docs.aws.amazon.com/cloudformation/",
                type=ResourceType.DOCUMENTATION,
                language=Language.ENGLISH,
                is_free=True,
                description="AWS CloudFormation official documentation"
            ),
            Resource(
                title="Infrastructure as Code Principles",
                url="https://www.hashicorp.com/resources/what-is-infrastructure-as-code",
                type=ResourceType.TUTORIAL,
                language=Language.ENGLISH,
                is_free=True,
                description="Understanding IaC concepts and benefits"
            ),
        ],
        Language.SPANISH: [
            Resource(
                title="Introducción a Terraform",
                url="https://developer.hashicorp.com/terraform/tutorials/aws-get-started",
                type=ResourceType.TUTORIAL,
                language=Language.SPANISH,
                is_free=True,
                description="Tutorial oficial de Terraform para AWS"
            ),
            Resource(
                title="Documentación de AWS CloudFormation",
                url="https://docs.aws.amazon.com/es_es/cloudformation/",
                type=ResourceType.DOCUMENTATION,
                language=Language.SPANISH,
                is_free=True,
                description="Documentación oficial de AWS CloudFormation"
            ),
            Resource(
                title="Principios de Infraestructura como Código",
                url="https://aws.amazon.com/es/what-is/iac/",
                type=ResourceType.TUTORIAL,
                language=Language.SPANISH,
                is_free=True,
                description="Conceptos y beneficios de IaC"
            ),
        ],
    },
    TechnicalArea.CI_CD: {
        Language.ENGLISH: [
            Resource(
                title="CI/CD Fundamentals",
                url="https://aws.amazon.com/devops/continuous-integration/",
                type=ResourceType.TUTORIAL,
                language=Language.ENGLISH,
                is_free=True,
                description="Introduction to CI/CD concepts"
            ),
            Resource(
                title="GitHub Actions Documentation",
                url="https://docs.github.com/en/actions",
                type=ResourceType.DOCUMENTATION,
                language=Language.ENGLISH,
                is_free=True,
                description="Official GitHub Actions documentation"
            ),
            Resource(
                title="AWS CodePipeline Tutorial",
                url="https://docs.aws.amazon.com/codepipeline/latest/userguide/tutorials.html",
                type=ResourceType.PRACTICE,
                language=Language.ENGLISH,
                is_free=True,
                description="Hands-on AWS CodePipeline tutorials"
            ),
        ],
        Language.SPANISH: [
            Resource(
                title="Fundamentos de CI/CD",
                url="https://aws.amazon.com/es/devops/continuous-integration/",
                type=ResourceType.TUTORIAL,
                language=Language.SPANISH,
                is_free=True,
                description="Introducción a conceptos de CI/CD"
            ),
            Resource(
                title="Documentación de GitHub Actions",
                url="https://docs.github.com/es/actions",
                type=ResourceType.DOCUMENTATION,
                language=Language.SPANISH,
                is_free=True,
                description="Documentación oficial de GitHub Actions"
            ),
            Resource(
                title="Tutorial de AWS CodePipeline",
                url="https://docs.aws.amazon.com/es_es/codepipeline/latest/userguide/tutorials.html",
                type=ResourceType.PRACTICE,
                language=Language.SPANISH,
                is_free=True,
                description="Tutoriales prácticos de AWS CodePipeline"
            ),
        ],
    },
}


def get_resources_for_area(
    technical_area: TechnicalArea,
    language: Language,
    min_count: int = 3
) -> List[Resource]:
    """Get learning resources for a technical area.
    
    Args:
        technical_area: The technical area
        language: Preferred language
        min_count: Minimum number of resources to return
        
    Returns:
        List of resources
    """
    resources = LEARNING_RESOURCES.get(technical_area, {}).get(language, [])
    
    # If we don't have enough resources in the preferred language,
    # fall back to English
    if len(resources) < min_count and language == Language.SPANISH:
        english_resources = LEARNING_RESOURCES.get(technical_area, {}).get(Language.ENGLISH, [])
        resources.extend(english_resources[:min_count - len(resources)])
    
    return resources[:min_count] if resources else []
