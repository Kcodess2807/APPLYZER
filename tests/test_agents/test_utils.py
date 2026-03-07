"""Tests for agent utilities."""
import pytest
from app.agents.utils import (
    extract_skills_from_text,
    sanitize_filename,
    validate_email,
    validate_url,
    calculate_text_similarity,
    chunk_list,
)


def test_extract_skills_from_text():
    """Test skill extraction from text."""
    text = "We need a Python developer with FastAPI and PostgreSQL experience"
    skills = extract_skills_from_text(text)
    
    assert "python" in skills
    assert "fastapi" in skills
    assert "postgresql" in skills


def test_extract_skills_case_insensitive():
    """Test skill extraction is case insensitive."""
    text = "PYTHON, JavaScript, and React developer"
    skills = extract_skills_from_text(text)
    
    assert "python" in skills
    assert "javascript" in skills
    assert "react" in skills


def test_sanitize_filename():
    """Test filename sanitization."""
    filename = "My Resume: Version 2.0 <final>.pdf"
    sanitized = sanitize_filename(filename)
    
    assert "<" not in sanitized
    assert ">" not in sanitized
    assert ":" not in sanitized
    assert " " not in sanitized  # Spaces replaced with underscores


def test_validate_email_valid():
    """Test email validation with valid emails."""
    assert validate_email("user@example.com")
    assert validate_email("test.user+tag@domain.co.uk")


def test_validate_email_invalid():
    """Test email validation with invalid emails."""
    assert not validate_email("invalid")
    assert not validate_email("@example.com")
    assert not validate_email("user@")


def test_validate_url_valid():
    """Test URL validation with valid URLs."""
    assert validate_url("https://example.com")
    assert validate_url("http://subdomain.example.com/path")


def test_validate_url_invalid():
    """Test URL validation with invalid URLs."""
    assert not validate_url("not a url")
    assert not validate_url("ftp://example.com")  # Only http/https


def test_calculate_text_similarity():
    """Test text similarity calculation."""
    text1 = "python developer with fastapi"
    text2 = "python engineer using fastapi"
    
    similarity = calculate_text_similarity(text1, text2)
    
    assert 0 < similarity < 1
    assert similarity > 0.5  # Should have decent overlap


def test_calculate_text_similarity_identical():
    """Test similarity of identical texts."""
    text = "same text"
    similarity = calculate_text_similarity(text, text)
    
    assert similarity == 1.0


def test_calculate_text_similarity_no_overlap():
    """Test similarity with no overlap."""
    text1 = "python developer"
    text2 = "java engineer"
    
    similarity = calculate_text_similarity(text1, text2)
    
    assert similarity < 0.5


def test_chunk_list():
    """Test list chunking."""
    lst = list(range(10))
    chunks = chunk_list(lst, 3)
    
    assert len(chunks) == 4  # [0-2], [3-5], [6-8], [9]
    assert chunks[0] == [0, 1, 2]
    assert chunks[-1] == [9]


def test_chunk_list_exact_division():
    """Test chunking with exact division."""
    lst = list(range(9))
    chunks = chunk_list(lst, 3)
    
    assert len(chunks) == 3
    assert all(len(chunk) == 3 for chunk in chunks)
