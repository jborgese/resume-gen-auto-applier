"""
Unit tests for resume builder functionality.

Tests the resume_builder.py module for PDF generation,
template rendering, and error handling.
"""

import pytest
from unittest.mock import patch, mock_open, Mock
from pathlib import Path
import tempfile
import shutil

# Import the module under test
from src.resume_builder import build_resume, sanitize_filename


class TestSanitizeFilename:
    """Test filename sanitization functionality."""
    
    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization."""
        result = sanitize_filename("Software Engineer")
        assert result == "Software_Engineer"
    
    def test_sanitize_filename_special_characters(self):
        """Test sanitization of special characters."""
        result = sanitize_filename("Senior Software Engineer @ Tech Corp!")
        assert result == "Senior_Software_Engineer__Tech_Corp"
    
    def test_sanitize_filename_numbers(self):
        """Test that numbers are preserved."""
        result = sanitize_filename("Engineer Level 3")
        assert result == "Engineer_Level_3"
    
    def test_sanitize_filename_underscores(self):
        """Test that underscores are preserved."""
        result = sanitize_filename("Software_Engineer")
        assert result == "Software_Engineer"
    
    def test_sanitize_filename_dashes(self):
        """Test that dashes are preserved."""
        result = sanitize_filename("Software-Engineer")
        assert result == "Software-Engineer"
    
    def test_sanitize_filename_empty(self):
        """Test sanitization of empty string."""
        result = sanitize_filename("")
        assert result == ""
    
    def test_sanitize_filename_unicode(self):
        """Test sanitization of unicode characters."""
        result = sanitize_filename("Développeur Logiciel")
        assert result == "Dveloppeur_Logiciel"


class TestBuildResume:
    """Test resume building functionality."""
    
    def test_build_resume_success(self, sample_resume_payload, temp_dir, mock_jinja2, mock_weasyprint):
        """Test successful resume building."""
        with patch('src.resume_builder.Path') as mock_path:
            # Mock the output path
            mock_output_path = temp_dir / "test_resume.pdf"
            mock_path.return_value.parent.mkdir.return_value = None
            mock_path.return_value = mock_output_path
            
            result = build_resume(sample_resume_payload)
            
            assert result == str(mock_output_path)
            mock_jinja2.assert_called_once()
            mock_weasyprint.assert_called_once()
    
    def test_build_resume_missing_name(self, mock_jinja2, mock_weasyprint):
        """Test resume building with missing name field."""
        payload = {
            "email": "test@example.com",
            "summary": "Test summary",
            "skills": ["Python", "React"],
            "experiences": [],
            "education": [],
            "references": []
        }
        
        with patch('src.resume_builder.Path') as mock_path:
            mock_output_path = Path("test_resume.pdf")
            mock_path.return_value.parent.mkdir.return_value = None
            mock_path.return_value = mock_output_path
            
            result = build_resume(payload)
            
            assert result == str(mock_output_path)
    
    def test_build_resume_missing_optional_fields(self, mock_jinja2, mock_weasyprint):
        """Test resume building with missing optional fields."""
        payload = {
            "name": "John Doe",
            "email": "test@example.com",
            "summary": "Test summary",
            "skills": ["Python", "React"],
            "experiences": [],
            "education": [],
            "references": []
        }
        
        with patch('src.resume_builder.Path') as mock_path:
            mock_output_path = Path("test_resume.pdf")
            mock_path.return_value.parent.mkdir.return_value = None
            mock_path.return_value = mock_output_path
            
            result = build_resume(payload)
            
            assert result == str(mock_output_path)
    
    def test_build_resume_with_job_info(self, mock_jinja2, mock_weasyprint):
        """Test resume building with job-specific information."""
        payload = {
            "name": "John Doe",
            "email": "test@example.com",
            "summary": "Test summary",
            "skills": ["Python", "React"],
            "matched_keywords": ["Python", "React", "AWS"],
            "experiences": [],
            "education": [],
            "references": [],
            "title": "Senior Software Engineer",
            "company": "Tech Corp",
            "location": "San Francisco, CA"
        }
        
        with patch('src.resume_builder.Path') as mock_path:
            mock_output_path = Path("test_resume.pdf")
            mock_path.return_value.parent.mkdir.return_value = None
            mock_path.return_value = mock_output_path
            
            result = build_resume(payload)
            
            assert result == str(mock_output_path)
    
    def test_build_resume_weasyprint_failure_fallback(self, sample_resume_payload, mock_jinja2):
        """Test resume building with WeasyPrint failure and fallback."""
        with patch('src.resume_builder.Path') as mock_path, \
             patch('weasyprint.HTML') as mock_html, \
             patch('src.resume_builder.APIFailureHandler') as mock_handler:
            
            # Mock WeasyPrint failure
            mock_html.side_effect = Exception("WeasyPrint failed")
            mock_handler.handle_weasyprint_failure.return_value = True
            
            mock_output_path = Path("test_resume.pdf")
            mock_path.return_value.parent.mkdir.return_value = None
            mock_path.return_value = mock_output_path
            
            result = build_resume(sample_resume_payload)
            
            assert result == str(mock_output_path)
            mock_handler.handle_weasyprint_failure.assert_called_once()
    
    def test_build_resume_weasyprint_failure_no_fallback(self, sample_resume_payload, mock_jinja2):
        """Test resume building with WeasyPrint failure and no fallback."""
        with patch('src.resume_builder.Path') as mock_path, \
             patch('weasyprint.HTML') as mock_html, \
             patch('src.resume_builder.APIFailureHandler') as mock_handler, \
             patch('src.resume_builder.FatalError') as mock_fatal_error:
            
            # Mock WeasyPrint failure
            mock_html.side_effect = Exception("WeasyPrint failed")
            mock_handler.handle_weasyprint_failure.return_value = False
            
            mock_output_path = Path("test_resume.pdf")
            mock_path.return_value.parent.mkdir.return_value = None
            mock_path.return_value = mock_output_path
            
            with pytest.raises(Exception):
                build_resume(sample_resume_payload)
    
    def test_build_resume_template_error(self, sample_resume_payload, mock_weasyprint):
        """Test resume building with template error."""
        with patch('src.resume_builder.Path') as mock_path, \
             patch('jinja2.Environment') as mock_env, \
             patch('src.resume_builder.FatalError') as mock_fatal_error:
            
            # Mock template error
            mock_env.side_effect = Exception("Template error")
            
            mock_output_path = Path("test_resume.pdf")
            mock_path.return_value.parent.mkdir.return_value = None
            mock_path.return_value = mock_output_path
            
            with pytest.raises(Exception):
                build_resume(sample_resume_payload)
    
    def test_build_resume_permission_error(self, sample_resume_payload, mock_jinja2, mock_weasyprint):
        """Test resume building with permission error."""
        with patch('src.resume_builder.Path') as mock_path, \
             patch('src.resume_builder.FatalError') as mock_fatal_error:
            
            # Mock permission error
            mock_path.return_value.parent.mkdir.side_effect = PermissionError("Permission denied")
            
            with pytest.raises(Exception):
                build_resume(sample_resume_payload)
    
    def test_build_resume_retry_logic(self, sample_resume_payload, mock_jinja2):
        """Test resume building retry logic."""
        with patch('src.resume_builder.Path') as mock_path, \
             patch('weasyprint.HTML') as mock_html, \
             patch('src.resume_builder.time.sleep') as mock_sleep:
            
            # Mock WeasyPrint failure on first attempt, success on second
            mock_html.side_effect = [Exception("Temporary failure"), Mock()]
            
            mock_output_path = Path("test_resume.pdf")
            mock_path.return_value.parent.mkdir.return_value = None
            mock_path.return_value = mock_output_path
            
            result = build_resume(sample_resume_payload)
            
            assert result == str(mock_output_path)
            assert mock_html.call_count == 2  # Should retry once


class TestResumeBuilderIntegration:
    """Integration tests for resume builder."""
    
    def test_build_resume_with_real_template(self, sample_resume_payload, temp_dir):
        """Test resume building with real template file."""
        # Create a simple HTML template
        template_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ name }} - Resume</title>
        </head>
        <body>
            <h1>{{ name }}</h1>
            <p>{{ email }}</p>
            <h2>Summary</h2>
            <p>{{ summary }}</h2>
            <h2>Skills</h2>
            <ul>
                {% for skill in skills %}
                <li>{{ skill }}</li>
                {% endfor %}
            </ul>
        </body>
        </html>
        """
        
        # Create template directory and file
        template_dir = temp_dir / "templates"
        template_dir.mkdir()
        template_file = template_dir / "base_resume.html"
        template_file.write_text(template_content)
        
        with patch('src.resume_builder.Path') as mock_path, \
             patch('jinja2.FileSystemLoader') as mock_loader, \
             patch('weasyprint.HTML') as mock_html:
            
            # Mock the template loading
            mock_env = Mock()
            mock_template = Mock()
            mock_template.render.return_value = template_content
            mock_env.get_template.return_value = mock_template
            mock_loader.return_value = Mock()
            
            # Mock the output path
            mock_output_path = temp_dir / "test_resume.pdf"
            mock_path.return_value.parent.mkdir.return_value = None
            mock_path.return_value = mock_output_path
            
            with patch('jinja2.Environment', return_value=mock_env):
                result = build_resume(sample_resume_payload)
                
                assert result == str(mock_output_path)
                mock_template.render.assert_called_once()
    
    def test_build_resume_filename_generation(self, sample_resume_payload, mock_jinja2, mock_weasyprint):
        """Test that resume filename is generated correctly."""
        with patch('src.resume_builder.Path') as mock_path, \
             patch('src.resume_builder.time.strftime') as mock_strftime:
            
            mock_strftime.return_value = "20231201-120000"
            
            mock_output_path = Path("output/resumes/Doe_Senior_Software_Engineer_Tech_Corp.pdf")
            mock_path.return_value.parent.mkdir.return_value = None
            mock_path.return_value = mock_output_path
            
            result = build_resume(sample_resume_payload)
            
            assert result == str(mock_output_path)
            mock_strftime.assert_called_once()
    
    def test_build_resume_utf8_encoding(self, sample_resume_payload, mock_jinja2, mock_weasyprint):
        """Test resume building with UTF-8 encoding."""
        # Add unicode characters to payload
        sample_resume_payload["summary"] = "Développeur expérimenté avec des compétences techniques solides."
        
        with patch('src.resume_builder.Path') as mock_path:
            mock_output_path = Path("test_resume.pdf")
            mock_path.return_value.parent.mkdir.return_value = None
            mock_path.return_value = mock_output_path
            
            result = build_resume(sample_resume_payload)
            
            assert result == str(mock_output_path)
    
    def test_build_resume_large_payload(self, mock_jinja2, mock_weasyprint):
        """Test resume building with large payload."""
        # Create a large payload
        large_payload = {
            "name": "John Doe",
            "email": "test@example.com",
            "summary": "Test summary " * 100,
            "skills": ["Python", "React", "AWS", "Docker", "Kubernetes"] * 20,
            "matched_keywords": ["Python", "React", "AWS"] * 10,
            "experiences": [
                {
                    "role": f"Engineer {i}",
                    "company": f"Company {i}",
                    "years": "2020-2023",
                    "responsibilities": [f"Responsibility {j}" for j in range(10)]
                }
                for i in range(5)
            ],
            "education": [
                {
                    "degree": f"Degree {i}",
                    "field": f"Field {i}",
                    "institution": f"School {i}",
                    "graduation_date": "2018"
                }
                for i in range(3)
            ],
            "references": [
                {
                    "name": f"Reference {i}",
                    "title": f"Title {i}",
                    "company": f"Company {i}",
                    "contact": {
                        "email": f"ref{i}@example.com",
                        "phone": f"+1-555-{i:03d}-{i:04d}"
                    }
                }
                for i in range(5)
            ],
            "title": "Senior Software Engineer",
            "company": "Tech Corp",
            "location": "San Francisco, CA"
        }
        
        with patch('src.resume_builder.Path') as mock_path:
            mock_output_path = Path("test_resume.pdf")
            mock_path.return_value.parent.mkdir.return_value = None
            mock_path.return_value = mock_output_path
            
            result = build_resume(large_payload)
            
            assert result == str(mock_output_path)


@pytest.mark.unit
class TestResumeBuilderErrorHandling:
    """Test error handling in resume builder."""
    
    def test_build_resume_invalid_data_type(self, mock_jinja2, mock_weasyprint):
        """Test resume building with invalid data type."""
        with patch('src.resume_builder.Path') as mock_path:
            mock_output_path = Path("test_resume.pdf")
            mock_path.return_value.parent.mkdir.return_value = None
            mock_path.return_value = mock_output_path
            
            # Pass non-dict data
            with pytest.raises((TypeError, AttributeError)):
                build_resume("invalid data")
    
    def test_build_resume_missing_required_fields(self, mock_jinja2, mock_weasyprint):
        """Test resume building with missing required fields."""
        # Empty payload
        empty_payload = {}
        
        with patch('src.resume_builder.Path') as mock_path:
            mock_output_path = Path("test_resume.pdf")
            mock_path.return_value.parent.mkdir.return_value = None
            mock_path.return_value = mock_output_path
            
            # Should handle missing fields gracefully
            result = build_resume(empty_payload)
            assert result == str(mock_output_path)
    
    def test_build_resume_none_values(self, mock_jinja2, mock_weasyprint):
        """Test resume building with None values."""
        payload_with_nones = {
            "name": None,
            "email": None,
            "summary": None,
            "skills": None,
            "experiences": None,
            "education": None,
            "references": None
        }
        
        with patch('src.resume_builder.Path') as mock_path:
            mock_output_path = Path("test_resume.pdf")
            mock_path.return_value.parent.mkdir.return_value = None
            mock_path.return_value = mock_output_path
            
            # Should handle None values gracefully
            result = build_resume(payload_with_nones)
            assert result == str(mock_output_path)
