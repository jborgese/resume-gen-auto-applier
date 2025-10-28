"""
Unit tests for keyword extraction functionality.

Tests the keyword_extractor.py module for proper keyword extraction,
NLP processing, and dictionary matching.
"""

import pytest
from unittest.mock import patch, mock_open
import json
from pathlib import Path

# Import the module under test
from src.keyword_extractor import extract_keywords


class TestKeywordExtraction:
    """Test keyword extraction functionality."""
    
    def test_extract_keywords_basic(self, sample_job_description, sample_tech_dictionary, sample_stopwords):
        """Test basic keyword extraction from job description."""
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            keywords = extract_keywords(sample_job_description)
            
            assert isinstance(keywords, list)
            assert len(keywords) > 0
            
            # Should find programming languages
            assert "Python" in keywords
            assert "JavaScript" in keywords
            
            # Should find frameworks
            assert "React" in keywords
            
            # Should find cloud platforms
            assert "AWS" in keywords
            
            # Should find tools
            assert "Docker" in keywords
            assert "Kubernetes" in keywords
    
    def test_extract_keywords_empty_description(self, sample_tech_dictionary, sample_stopwords):
        """Test keyword extraction with empty description."""
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            keywords = extract_keywords("")
            assert keywords == []
    
    def test_extract_keywords_no_matches(self, sample_tech_dictionary, sample_stopwords):
        """Test keyword extraction with no dictionary matches."""
        description = "This is a job for a completely unrelated field with no technical terms."
        
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            keywords = extract_keywords(description)
            
            # Should still find some nouns from spaCy
            assert isinstance(keywords, list)
            # May find some generic terms, but no tech terms
    
    def test_extract_keywords_case_insensitive(self, sample_tech_dictionary, sample_stopwords):
        """Test that keyword extraction is case insensitive."""
        description = "We need someone with python, react, and aws experience."
        
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            keywords = extract_keywords(description)
            
            # Should find capitalized versions
            assert "Python" in keywords
            assert "React" in keywords
            assert "AWS" in keywords
    
    def test_extract_keywords_duplicates_removed(self, sample_tech_dictionary, sample_stopwords):
        """Test that duplicate keywords are removed."""
        description = "Python Python python REACT React react AWS aws AWS"
        
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            keywords = extract_keywords(description)
            
            # Should not have duplicates
            assert len(keywords) == len(set(keywords))
            
            # Should have the capitalized versions
            assert "Python" in keywords
            assert "React" in keywords
            assert "AWS" in keywords
    
    def test_extract_keywords_sorted(self, sample_tech_dictionary, sample_stopwords):
        """Test that keywords are returned in sorted order."""
        description = "We use Docker, AWS, Python, React, and Kubernetes."
        
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            keywords = extract_keywords(description)
            
            # Should be sorted
            assert keywords == sorted(keywords)
    
    def test_extract_keywords_filters_stopwords(self, sample_tech_dictionary, sample_stopwords):
        """Test that stopwords are filtered out."""
        description = "The company needs a developer with Python skills and the ability to work with React."
        
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            keywords = extract_keywords(description)
            
            # Should not contain stopwords
            stopwords = sample_stopwords["stopwords"]
            for stopword in stopwords:
                assert stopword.lower() not in [kw.lower() for kw in keywords]
    
    def test_extract_keywords_minimum_length(self, sample_tech_dictionary, sample_stopwords):
        """Test that keywords have minimum length requirement."""
        description = "We need someone with Go, C++, and Java skills."
        
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            keywords = extract_keywords(description)
            
            # All keywords should be longer than 2 characters
            for keyword in keywords:
                assert len(keyword) > 2
    
    def test_extract_keywords_mixed_content(self, sample_tech_dictionary, sample_stopwords):
        """Test keyword extraction with mixed technical and non-technical content."""
        description = """
        We are a fast-growing startup looking for a Senior Software Engineer.
        
        Technical Requirements:
        - 5+ years Python development experience
        - Strong React and JavaScript skills
        - AWS cloud platform experience
        - Docker containerization knowledge
        - Kubernetes orchestration experience
        - SQL database expertise
        
        Soft Skills:
        - Excellent communication
        - Team collaboration
        - Problem-solving abilities
        - Leadership potential
        """
        
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            keywords = extract_keywords(description)
            
            # Should find technical keywords
            tech_keywords = ["Python", "React", "JavaScript", "AWS", "Docker", "Kubernetes", "SQL"]
            for tech_keyword in tech_keywords:
                assert tech_keyword in keywords
            
            # Should not include soft skills as keywords
            soft_skills = ["communication", "collaboration", "problem-solving", "leadership"]
            for soft_skill in soft_skills:
                assert soft_skill not in keywords


class TestSpacyIntegration:
    """Test spaCy integration for NLP processing."""
    
    def test_spacy_noun_extraction(self, sample_tech_dictionary, sample_stopwords):
        """Test that spaCy extracts nouns properly."""
        description = "We need a developer with Python programming skills and React frontend experience."
        
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            keywords = extract_keywords(description)
            
            # Should find nouns from spaCy processing
            assert "Python" in keywords
            assert "React" in keywords
    
    def test_spacy_proper_noun_extraction(self, sample_tech_dictionary, sample_stopwords):
        """Test that spaCy extracts proper nouns."""
        description = "Experience with AWS, Docker, and Kubernetes is required."
        
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            keywords = extract_keywords(description)
            
            # Should find proper nouns
            assert "AWS" in keywords
            assert "Docker" in keywords
            assert "Kubernetes" in keywords
    
    def test_spacy_acronym_extraction(self, sample_tech_dictionary, sample_stopwords):
        """Test that spaCy extracts acronyms."""
        description = "Knowledge of SQL, API, and REST is essential."
        
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            keywords = extract_keywords(description)
            
            # Should find acronyms
            assert "SQL" in keywords


class TestDictionaryMatching:
    """Test dictionary-based keyword matching."""
    
    def test_dictionary_matching_programming_languages(self, sample_tech_dictionary, sample_stopwords):
        """Test matching programming languages from dictionary."""
        description = "We need developers skilled in Python, Java, and Go."
        
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            keywords = extract_keywords(description)
            
            # Should find programming languages
            assert "Python" in keywords
            assert "Java" in keywords
            assert "Go" in keywords
    
    def test_dictionary_matching_frameworks(self, sample_tech_dictionary, sample_stopwords):
        """Test matching frameworks from dictionary."""
        description = "Experience with React, Django, and Flask is preferred."
        
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            keywords = extract_keywords(description)
            
            # Should find frameworks
            assert "React" in keywords
            assert "Django" in keywords
            assert "Flask" in keywords
    
    def test_dictionary_matching_databases(self, sample_tech_dictionary, sample_stopwords):
        """Test matching databases from dictionary."""
        description = "Database experience with PostgreSQL, MySQL, and MongoDB."
        
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            keywords = extract_keywords(description)
            
            # Should find databases
            assert "PostgreSQL" in keywords
            assert "MySQL" in keywords
            assert "MongoDB" in keywords
    
    def test_dictionary_matching_cloud_platforms(self, sample_tech_dictionary, sample_stopwords):
        """Test matching cloud platforms from dictionary."""
        description = "Cloud experience with AWS, Azure, and Docker containers."
        
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            keywords = extract_keywords(description)
            
            # Should find cloud platforms
            assert "AWS" in keywords
            assert "Azure" in keywords
            assert "Docker" in keywords
    
    def test_dictionary_matching_tools(self, sample_tech_dictionary, sample_stopwords):
        """Test matching tools from dictionary."""
        description = "Familiarity with Git, Jenkins, and Terraform is required."
        
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            keywords = extract_keywords(description)
            
            # Should find tools
            assert "Git" in keywords
            assert "Jenkins" in keywords
            assert "Terraform" in keywords


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_extract_keywords_none_input(self, sample_tech_dictionary, sample_stopwords):
        """Test keyword extraction with None input."""
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            with pytest.raises((TypeError, AttributeError)):
                extract_keywords(None)
    
    def test_extract_keywords_non_string_input(self, sample_tech_dictionary, sample_stopwords):
        """Test keyword extraction with non-string input."""
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            with pytest.raises((TypeError, AttributeError)):
                extract_keywords(123)
    
    def test_extract_keywords_very_long_description(self, sample_tech_dictionary, sample_stopwords):
        """Test keyword extraction with very long description."""
        # Create a very long description
        long_description = "Python " * 1000 + "React " * 1000 + "AWS " * 1000
        
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            keywords = extract_keywords(long_description)
            
            # Should still work and return keywords
            assert isinstance(keywords, list)
            assert "Python" in keywords
            assert "React" in keywords
            assert "AWS" in keywords
    
    def test_extract_keywords_special_characters(self, sample_tech_dictionary, sample_stopwords):
        """Test keyword extraction with special characters."""
        description = "We need someone with Python@3.9, React.js, and AWS-EC2 experience!"
        
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            keywords = extract_keywords(description)
            
            # Should still find keywords despite special characters
            assert "Python" in keywords
            assert "React" in keywords
            assert "AWS" in keywords
    
    def test_extract_keywords_unicode_characters(self, sample_tech_dictionary, sample_stopwords):
        """Test keyword extraction with unicode characters."""
        description = "We need a développeur with Python skills and React expérience."
        
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            keywords = extract_keywords(description)
            
            # Should handle unicode characters
            assert isinstance(keywords, list)
            assert "Python" in keywords
            assert "React" in keywords


@pytest.mark.unit
class TestKeywordExtractionIntegration:
    """Integration tests for keyword extraction."""
    
    def test_keyword_extraction_with_real_data(self, sample_tech_dictionary, sample_stopwords):
        """Test keyword extraction with realistic job description data."""
        real_job_description = """
        Senior Software Engineer - Full Stack
        
        Company: TechCorp Inc.
        Location: San Francisco, CA
        
        We are seeking a Senior Software Engineer to join our dynamic team. 
        The ideal candidate will have extensive experience in modern web development.
        
        Required Skills:
        - 5+ years of Python development experience
        - Strong proficiency in React and JavaScript
        - Experience with AWS cloud services (EC2, S3, Lambda)
        - Docker containerization and Kubernetes orchestration
        - SQL database design and optimization
        - RESTful API development
        - Git version control
        - Agile development methodologies
        
        Preferred Qualifications:
        - Experience with Django or Flask frameworks
        - Knowledge of PostgreSQL or MySQL
        - CI/CD pipeline experience with Jenkins
        - Microservices architecture experience
        - Machine learning integration experience
        
        Responsibilities:
        - Design and develop scalable web applications
        - Collaborate with cross-functional teams
        - Mentor junior developers
        - Participate in code reviews
        - Contribute to architectural decisions
        """
        
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            keywords = extract_keywords(real_job_description)
            
            # Should find many relevant keywords
            assert len(keywords) > 10
            
            # Should find programming languages
            assert "Python" in keywords
            assert "JavaScript" in keywords
            
            # Should find frameworks
            assert "React" in keywords
            assert "Django" in keywords
            assert "Flask" in keywords
            
            # Should find cloud platforms
            assert "AWS" in keywords
            
            # Should find tools
            assert "Docker" in keywords
            assert "Kubernetes" in keywords
            assert "Git" in keywords
            assert "Jenkins" in keywords
            
            # Should find databases
            assert "SQL" in keywords
            assert "PostgreSQL" in keywords
            assert "MySQL" in keywords
    
    def test_keyword_extraction_performance(self, sample_tech_dictionary, sample_stopwords):
        """Test keyword extraction performance with large text."""
        import time
        
        # Create a large job description
        large_description = """
        We are looking for a Senior Software Engineer with the following requirements:
        """ + "Python, React, AWS, Docker, Kubernetes, SQL, " * 100
        
        with patch('src.keyword_extractor.TECH_DICT', sample_tech_dictionary), \
             patch('src.keyword_extractor.STOPWORDS', set(sample_stopwords["stopwords"])):
            
            start_time = time.time()
            keywords = extract_keywords(large_description)
            end_time = time.time()
            
            # Should complete in reasonable time (less than 5 seconds)
            assert end_time - start_time < 5.0
            
            # Should still return correct keywords
            assert "Python" in keywords
            assert "React" in keywords
            assert "AWS" in keywords
