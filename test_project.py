"""
Tests for project.py — run with: pytest test_project.py
"""

from project import (
    clean_and_tokenize,
    extract_keywords,
    calculate_ats_score,
    find_missing_keywords,
    calculate_readability,
    check_formatting_issues,
    skills_gap_analysis,
)


def test_clean_and_tokenize():
    text = "I am a Python Developer! I love Python, APIs, and Data-Science."
    tokens = clean_and_tokenize(text)
    # Stopwords and short words like "am", "a", "and" should be removed
    assert "python" in tokens
    assert "developer" in tokens
    assert "am" not in tokens
    assert "and" not in tokens
    # Duplicate word "python" should appear twice since we don't dedupe here
    assert tokens.count("python") == 2


def test_extract_keywords():
    text = "python python python sql sql java data data data data"
    keywords = extract_keywords(text, top_n=3)
    assert keywords == ["data", "python", "sql"]
    # Requesting more keywords than exist should not raise an error
    all_keywords = extract_keywords(text, top_n=10)
    assert set(all_keywords) == {"python", "sql", "java", "data"}


def test_calculate_ats_score():
    resume_keywords = ["python", "sql", "django", "excel"]
    jd_keywords = ["python", "sql", "aws", "docker"]
    # 2 out of 4 jd keywords are present in the resume => 50%
    assert calculate_ats_score(resume_keywords, jd_keywords) == 50.0
    # Perfect match
    assert calculate_ats_score(["python", "sql"], ["python", "sql"]) == 100.0
    # No job keywords at all should return 0.0, not raise a ZeroDivisionError
    assert calculate_ats_score(["python"], []) == 0.0


def test_find_missing_keywords():
    resume_keywords = ["python", "sql"]
    jd_keywords = ["python", "sql", "aws", "docker"]
    missing = find_missing_keywords(resume_keywords, jd_keywords)
    assert missing == ["aws", "docker"]
    # If resume already covers everything, nothing should be missing
    assert find_missing_keywords(["python", "sql", "aws", "docker"], jd_keywords) == []


def test_calculate_readability():
    # Empty text should return 0.0 rather than raising an error
    assert calculate_readability("") == 0.0
    # Simple short sentences should score reasonably high (easy to read)
    easy_text = "I like cats. Cats are nice. Cats are fun."
    score = calculate_readability(easy_text)
    assert score > 60
    # A very dense sentence with long words should score lower than the easy text
    hard_text = ("Notwithstanding the aforementioned considerations, the multifaceted "
                 "implementation necessitates comprehensive interdisciplinary collaboration.")
    hard_score = calculate_readability(hard_text)
    assert hard_score < score


def test_check_formatting_issues():
    short_text = "Short resume with no contact info."
    issues = check_formatting_issues(short_text)
    assert any("short" in issue.lower() for issue in issues)
    assert any("email" in issue.lower() for issue in issues)
    assert any("phone" in issue.lower() for issue in issues)

    good_text = (
        "Jane Doe jane.doe@email.com 555-123-4567\n" + ("Managed projects and led teams. " * 40) +
        "• Delivered results\n• Improved processes\n• Mentored engineers"
    )
    good_issues = check_formatting_issues(good_text)
    assert not any("email" in issue.lower() for issue in good_issues)
    assert not any("phone" in issue.lower() for issue in good_issues)
    assert not any("bullet" in issue.lower() for issue in good_issues)


def test_skills_gap_analysis():
    resume_text = "Experienced with Python, SQL and Git for version control."
    jd_text = "Looking for a candidate skilled in Python, SQL, Docker, and AWS."
    result = skills_gap_analysis(resume_text, jd_text)
    assert "python" in result["required_skills"]
    assert "sql" in result["required_skills"]
    assert "docker" in result["missing_skills"]
    assert "aws" in result["missing_skills"]
    assert "python" not in result["missing_skills"]
