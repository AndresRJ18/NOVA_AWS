"""Report Generator implementation."""

from typing import Dict, List, Tuple
from datetime import datetime
from collections import defaultdict
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

from mock_interview_coach.models import (
    Question,
    Evaluation,
    Report,
    TechnicalArea,
    Role,
    Level,
    Language,
    SessionState
)
from mock_interview_coach.data import get_resources_for_area


class ReportGenerator:
    """Generates final interview reports with scores and learning resources."""
    
    def generate_report(
        self,
        session_data: SessionState,
        language: Language
    ) -> Report:
        """Generate a report from session data.
        
        Args:
            session_data: The completed session state
            language: Language for the report
            
        Returns:
            Report with scores and resources
        """
        # Calculate overall score
        overall_score = self._calculate_overall_score(session_data.evaluations)
        
        # Calculate per-area scores
        area_scores = self._calculate_area_scores(
            session_data.questions,
            session_data.evaluations
        )
        
        # Identify weak areas (score < 70)
        weak_areas = [area for area, score in area_scores.items() if score < 70]
        
        # Get learning resources for weak areas
        learning_resources = self._get_learning_resources(weak_areas, language)
        
        # Build questions and responses list
        questions_and_responses = list(zip(
            session_data.questions,
            session_data.responses,
            session_data.evaluations
        ))
        
        return Report(
            session_id=session_data.session_id,
            role=session_data.role,
            level=session_data.level,
            language=session_data.language,
            overall_score=overall_score,
            area_scores=area_scores,
            questions_and_responses=questions_and_responses,
            learning_resources=learning_resources,
            timestamp=datetime.now()
        )
    
    def export_pdf(self, report: Report) -> bytes:
        """Export report as PDF with modern glassmorphism-inspired design.
        
        Args:
            report: The report to export
            
        Returns:
            PDF bytes
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        story = []
        styles = getSampleStyleSheet()
        
        # Modern color palette
        primary_color = colors.HexColor('#6366F1')  # Indigo
        secondary_color = colors.HexColor('#8B5CF6')  # Purple
        accent_color = colors.HexColor('#EC4899')  # Pink
        success_color = colors.HexColor('#10B981')  # Green
        text_color = colors.HexColor('#1E293B')  # Dark slate
        muted_color = colors.HexColor('#64748B')  # Slate
        bg_light = colors.HexColor('#F8FAFC')  # Very light blue
        
        # Title with gradient effect (simulated with color)
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=32,
            textColor=primary_color,
            spaceAfter=10,
            fontName='Helvetica-Bold',
            alignment=1  # Center
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=muted_color,
            spaceAfter=30,
            alignment=1  # Center
        )
        
        if report.language == Language.ENGLISH:
            title = Paragraph("🎯 Mock Interview Report", title_style)
            subtitle = Paragraph("AI-Powered Technical Interview Analysis", subtitle_style)
        else:
            title = Paragraph("🎯 Reporte de Entrevista Simulada", title_style)
            subtitle = Paragraph("Análisis de Entrevista Técnica con IA", subtitle_style)
        
        story.append(title)
        story.append(subtitle)
        story.append(Spacer(1, 0.3 * inch))
        
        # Session info with modern styling
        info_data = [
            [self._translate("Role", report.language), report.role.value.replace('_', ' ').title()],
            [self._translate("Level", report.language), report.level.value.title()],
            [self._translate("Date", report.language), report.timestamp.strftime("%B %d, %Y at %H:%M")],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), primary_color),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('TEXTCOLOR', (1, 0), (1, -1), text_color),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('BACKGROUND', (1, 0), (1, -1), bg_light),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0'))
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 0.4 * inch))
        
        # Overall score with prominent display
        score_style = ParagraphStyle(
            'ScoreStyle',
            parent=styles['Heading1'],
            fontSize=48,
            textColor=primary_color,
            alignment=1,
            fontName='Helvetica-Bold'
        )
        
        score_label_style = ParagraphStyle(
            'ScoreLabelStyle',
            parent=styles['Normal'],
            fontSize=16,
            textColor=muted_color,
            alignment=1,
            spaceAfter=10
        )
        
        score_para = Paragraph(f"{report.overall_score}", score_style)
        score_label = Paragraph(self._translate('Overall Score', report.language), score_label_style)
        
        story.append(score_label)
        story.append(score_para)
        story.append(Spacer(1, 0.4 * inch))
        
        # Area scores with color-coded performance
        if report.area_scores:
            area_title_style = ParagraphStyle(
                'AreaTitle',
                parent=styles['Heading2'],
                fontSize=18,
                textColor=secondary_color,
                spaceAfter=15,
                fontName='Helvetica-Bold'
            )
            
            area_title = Paragraph(self._translate("Performance by Technical Area", report.language), area_title_style)
            story.append(area_title)
            
            area_data = [[
                self._translate("Technical Area", report.language), 
                self._translate("Score", report.language),
                self._translate("Status", report.language)
            ]]
            
            for area, score in report.area_scores.items():
                # Determine status and color
                if score >= 80:
                    status = "Excellent" if report.language == Language.ENGLISH else "Excelente"
                    status_display = f"✓ {status}"
                elif score >= 70:
                    status = "Good" if report.language == Language.ENGLISH else "Bueno"
                    status_display = f"✓ {status}"
                else:
                    status = "Needs Improvement" if report.language == Language.ENGLISH else "Necesita Mejorar"
                    status_display = f"⚠ {status}"
                
                area_name = area.value.replace('_', ' ').title()
                area_data.append([area_name, f"{score}/100", status_display])
            
            area_table = Table(area_data, colWidths=[2.5*inch, 1.2*inch, 2*inch])
            
            # Apply color coding based on scores
            table_style = [
                ('BACKGROUND', (0, 0), (-1, 0), secondary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ]
            
            # Color code rows based on score
            for i, (area, score) in enumerate(report.area_scores.items(), start=1):
                if score >= 80:
                    table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#D1FAE5')))
                elif score >= 70:
                    table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#FEF3C7')))
                else:
                    table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#FEE2E2')))
            
            area_table.setStyle(TableStyle(table_style))
            
            story.append(area_table)
            story.append(Spacer(1, 0.4 * inch))
        
        # Learning resources with modern styling
        if report.learning_resources:
            resources_title_style = ParagraphStyle(
                'ResourcesTitle',
                parent=styles['Heading2'],
                fontSize=18,
                textColor=accent_color,
                spaceAfter=15,
                fontName='Helvetica-Bold'
            )
            
            resources_title = Paragraph(
                self._translate("Recommended Learning Resources", report.language), 
                resources_title_style
            )
            story.append(resources_title)
            
            resource_area_style = ParagraphStyle(
                'ResourceArea',
                parent=styles['Normal'],
                fontSize=13,
                textColor=primary_color,
                fontName='Helvetica-Bold',
                spaceAfter=8,
                spaceBefore=10
            )
            
            resource_item_style = ParagraphStyle(
                'ResourceItem',
                parent=styles['Normal'],
                fontSize=10,
                textColor=text_color,
                leftIndent=20,
                spaceAfter=6
            )
            
            for area, resources in report.learning_resources.items():
                area_name = area.value.replace('_', ' ').title()
                area_para = Paragraph(f"📚 {area_name}", resource_area_style)
                story.append(area_para)
                
                for resource in resources:
                    resource_text = f"<b>•</b> {resource.title} <i>({resource.type.value})</i><br/>&nbsp;&nbsp;&nbsp;<font color='#{muted_color.hexval()[2:]}'>{resource.url}</font>"
                    resource_para = Paragraph(resource_text, resource_item_style)
                    story.append(resource_para)
                
                story.append(Spacer(1, 0.1 * inch))
        
        # Detailed Feedback Section (NEW)
        story.append(Spacer(1, 0.4 * inch))
        
        feedback_title_style = ParagraphStyle(
            'FeedbackTitle',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=secondary_color,
            spaceAfter=15,
            fontName='Helvetica-Bold'
        )
        
        feedback_title = Paragraph(
            self._translate("Detailed Feedback by Question", report.language),
            feedback_title_style
        )
        story.append(feedback_title)
        
        # Iterate through questions and show detailed feedback
        for idx, (question, response, evaluation) in enumerate(report.questions_and_responses, 1):
            # Question header
            q_header_style = ParagraphStyle(
                'QuestionHeader',
                parent=styles['Normal'],
                fontSize=12,
                textColor=primary_color,
                fontName='Helvetica-Bold',
                spaceAfter=8,
                spaceBefore=12
            )
            
            q_header = Paragraph(f"Question {idx}: {question.text[:80]}...", q_header_style)
            story.append(q_header)
            
            # Score
            score_style = ParagraphStyle(
                'ScoreInline',
                parent=styles['Normal'],
                fontSize=11,
                textColor=text_color,
                spaceAfter=8
            )
            
            score_color = success_color if evaluation.score >= 70 else (colors.HexColor('#F59E0B') if evaluation.score >= 50 else colors.HexColor('#EF4444'))
            score_para = Paragraph(
                f"<b>Score:</b> <font color='#{score_color.hexval()[2:]}'>{evaluation.score}/100</font>",
                score_style
            )
            story.append(score_para)
            
            # Strengths
            if evaluation.strengths:
                strengths_style = ParagraphStyle(
                    'Strengths',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=text_color,
                    leftIndent=15,
                    spaceAfter=6
                )
                
                strengths_header = Paragraph(
                    f"<b><font color='#{success_color.hexval()[2:]}'>✓ Strengths:</font></b>",
                    strengths_style
                )
                story.append(strengths_header)
                
                for strength in evaluation.strengths:
                    strength_para = Paragraph(f"• {strength}", strengths_style)
                    story.append(strength_para)
                
                story.append(Spacer(1, 0.05 * inch))
            
            # Weaknesses
            if evaluation.weaknesses:
                weaknesses_style = ParagraphStyle(
                    'Weaknesses',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=text_color,
                    leftIndent=15,
                    spaceAfter=6
                )
                
                weaknesses_header = Paragraph(
                    f"<b><font color='#{colors.HexColor('#F59E0B').hexval()[2:]}'>⚠ Areas for Improvement:</font></b>",
                    weaknesses_style
                )
                story.append(weaknesses_header)
                
                for weakness in evaluation.weaknesses:
                    weakness_para = Paragraph(f"• {weakness}", weaknesses_style)
                    story.append(weakness_para)
                
                story.append(Spacer(1, 0.05 * inch))
            
            # Recommended Topics
            if evaluation.recommended_topics:
                topics_style = ParagraphStyle(
                    'Topics',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=text_color,
                    leftIndent=15,
                    spaceAfter=6
                )
                
                topics_header = Paragraph(
                    f"<b><font color='#{primary_color.hexval()[2:]}'>📚 Recommended Topics:</font></b>",
                    topics_style
                )
                story.append(topics_header)
                
                for topic in evaluation.recommended_topics:
                    topic_para = Paragraph(f"• {topic}", topics_style)
                    story.append(topic_para)
                
                story.append(Spacer(1, 0.1 * inch))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=muted_color,
            alignment=1,
            spaceAfter=0
        )
        
        story.append(Spacer(1, 0.5 * inch))
        footer_text = "Generated by Mock Interview Coach - AI-Powered Interview Practice" if report.language == Language.ENGLISH else "Generado por Mock Interview Coach - Práctica de Entrevistas con IA"
        footer = Paragraph(footer_text, footer_style)
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _calculate_overall_score(self, evaluations: List[Evaluation]) -> int:
        """Calculate overall score from evaluations."""
        if not evaluations:
            return 0
        
        total = sum(eval.score for eval in evaluations)
        return total // len(evaluations)
    
    def _calculate_area_scores(
        self,
        questions: List[Question],
        evaluations: List[Evaluation]
    ) -> Dict[TechnicalArea, int]:
        """Calculate scores per technical area."""
        area_scores: Dict[TechnicalArea, List[int]] = defaultdict(list)
        
        for question, evaluation in zip(questions, evaluations):
            area_scores[question.technical_area].append(evaluation.score)
        
        # Average scores per area
        return {
            area: sum(scores) // len(scores)
            for area, scores in area_scores.items()
        }
    
    def _get_learning_resources(
        self,
        weak_areas: List[TechnicalArea],
        language: Language
    ) -> Dict[TechnicalArea, List]:
        """Get learning resources for weak areas."""
        resources = {}
        
        for area in weak_areas:
            area_resources = get_resources_for_area(area, language, min_count=3)
            if area_resources:
                resources[area] = area_resources
        
        return resources
    
    def _translate(self, text: str, language: Language) -> str:
        """Translate text to the specified language."""
        translations = {
            "Role": {"en": "Role", "es": "Rol"},
            "Level": {"en": "Level", "es": "Nivel"},
            "Date": {"en": "Date", "es": "Fecha"},
            "Overall Score": {"en": "Overall Score", "es": "Puntuación General"},
            "Performance by Technical Area": {"en": "Performance by Technical Area", "es": "Rendimiento por Área Técnica"},
            "Scores by Technical Area": {"en": "Scores by Technical Area", "es": "Puntuaciones por Área Técnica"},
            "Technical Area": {"en": "Technical Area", "es": "Área Técnica"},
            "Score": {"en": "Score", "es": "Puntuación"},
            "Status": {"en": "Status", "es": "Estado"},
            "Recommended Learning Resources": {"en": "Recommended Learning Resources", "es": "Recursos de Aprendizaje Recomendados"},
            "Detailed Feedback by Question": {"en": "Detailed Feedback by Question", "es": "Retroalimentación Detallada por Pregunta"},
        }
        
        lang_code = language.value
        return translations.get(text, {}).get(lang_code, text)
