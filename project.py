"""
Smart Resume ATS Checker
=========================
A command-line tool that compares a resume against a job description the
way an Applicant Tracking System (ATS) would. It reports a match score,
missing keywords, a skills gap analysis, a readability score and common
resume formatting problems.

Usage:
    python project.py --resume resume.txt --jd job_description.txt
    python project.py --resume resume.pdf --jd job_description.docx --top 40
"""

import argparse
import re
import sys
from collections import Counter

try:
    from PyPDF2 import PdfReader
except ImportError:  # PyPDF2 is only required if the user uploads a .pdf
    PdfReader = None

try:
    import docx
except ImportError:  # python-docx is only required if the user uploads a .docx
    docx = None


# A small, hand curated set of very common English words that carry little
# meaning on their own and should not be treated as "keywords".
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "so", "of", "to",
    "in", "on", "at", "for", "with", "as", "by", "from", "is", "was",
    "are", "were", "be", "been", "being", "this", "that", "these", "those",
    "it", "its", "i", "you", "your", "we", "our", "they", "their", "he",
    "she", "his", "her", "them", "us", "will", "would", "can", "could",
    "should", "may", "might", "must", "shall", "not", "no", "do", "does",
    "did", "have", "has", "had", "having", "about", "into", "over",
    "under", "again", "further", "than", "too", "very", "just", "also",
    "up", "down", "out", "off", "each", "such", "own", "same", "other",
    "more", "most", "some", "all", "any", "both", "few", "which", "who",
    "whom", "what", "when", "where", "why", "how", "there", "here",
}

# A curated list of common technical and soft skills used for the
# "skills gap" comparison. Not exhaustive, but broad enough for a demo.
SKILLS_DB = {
    "python", "java", "javascript", "typescript", "c", "c++", "c#", "sql",
    "nosql", "mongodb", "postgresql", "mysql", "git", "github", "docker",
    "kubernetes", "aws", "azure", "gcp", "linux", "html", "css", "react",
    "angular", "vue", "django", "flask", "fastapi", "node", "express",
    "pandas", "numpy", "tensorflow", "pytorch", "scikit-learn", "excel",
    "tableau", "power", "bi", "machine", "learning", "deep", "learning",
    "data", "analysis", "analytics", "communication", "leadership",
    "teamwork", "problem-solving", "project", "management", "agile",
    "scrum", "rest", "api", "testing", "debugging", "ci/cd", "devops",
    "cloud", "security", "networking", "algorithms", "statistics",
}


def main():
    parser = argparse.ArgumentParser(
        description="Compare a resume against a job description like an ATS would."
    )
    parser.add_argument("--resume", required=True, help="Path to the resume file (.txt, .pdf or .docx)")
    parser.add_argument("--jd", required=True, help="Path to the job description file (.txt, .pdf or .docx)")
    parser.add_argument("--top", type=int, default=30, help="Number of top keywords to compare (default: 30)")
    args = parser.parse_args()

    try:
        resume_text = extract_text_from_file(args.resume)
        jd_text = extract_text_from_file(args.jd)
    except (FileNotFoundError, ValueError) as e:
        sys.exit(f"Error: {e}")

    resume_keywords = extract_keywords(resume_text, args.top)
    jd_keywords = extract_keywords(jd_text, args.top)

    score = calculate_ats_score(resume_keywords, jd_keywords)
    missing = find_missing_keywords(resume_keywords, jd_keywords)
    readability = calculate_readability(resume_text)
    formatting_issues = check_formatting_issues(resume_text)
    gap = skills_gap_analysis(resume_text, jd_text)

    print("=" * 60)
    print("SMART RESUME ATS CHECKER — REPORT")
    print("=" * 60)

    print(f"\nATS Match Score: {score}%")
    if score >= 75:
        print("This resume is a strong match for the job description.")
    elif score >= 45:
        print("This resume is a moderate match. Consider adding missing keywords.")
    else:
        print("This resume is a weak match for this job description.")

    print(f"\nMissing Keywords ({len(missing)}):")
    print(", ".join(missing) if missing else "None — great coverage!")

    print(f"\nSkills Gap Analysis:")
    print(f"  Skills mentioned in job description: {', '.join(gap['required_skills']) or 'None detected'}")
    print(f"  Skills missing from resume: {', '.join(gap['missing_skills']) or 'None — resume covers all detected skills!'}")

    print(f"\nReadability Score (Flesch Reading Ease): {readability}")
    print("  " + interpret_readability(readability))

    print(f"\nFormatting Issues ({len(formatting_issues)}):")
    if formatting_issues:
        for issue in formatting_issues:
            print(f"  - {issue}")
    else:
        print("  No obvious formatting issues detected.")

    print("\nSuggestions:")
    for suggestion in generate_suggestions(missing, formatting_issues, readability):
        print(f"  - {suggestion}")

    print("=" * 60)


def extract_text_from_file(filepath):
    """
    Read a .txt, .pdf or .docx file and return its contents as plain text.
    Raises FileNotFoundError if the file does not exist and ValueError for
    unsupported file extensions.
    """
    if filepath.lower().endswith(".txt"):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    elif filepath.lower().endswith(".pdf"):
        if PdfReader is None:
            raise ValueError("PyPDF2 is required to read .pdf files. Install it with 'pip install PyPDF2'.")
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    elif filepath.lower().endswith(".docx"):
        if docx is None:
            raise ValueError("python-docx is required to read .docx files. Install it with 'pip install python-docx'.")
        document = docx.Document(filepath)
        return "\n".join(paragraph.text for paragraph in document.paragraphs)

    else:
        raise ValueError(f"Unsupported file type: {filepath}. Use .txt, .pdf or .docx.")


def clean_and_tokenize(text):
    """
    Lowercase the text, strip punctuation, split it into words, and remove
    stopwords and very short tokens. Returns a list of cleaned word tokens.
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9+#/\-\s]", " ", text)
    tokens = text.split()
    tokens = [t.strip("-/") for t in tokens]
    tokens = [t for t in tokens if t and t not in STOPWORDS and len(t) > 2]
    return tokens


def extract_keywords(text, top_n=30):
    """
    Return the top_n most frequent meaningful words in the given text,
    ordered from most to least frequent.
    """
    tokens = clean_and_tokenize(text)
    counts = Counter(tokens)
    most_common = counts.most_common(top_n)
    return [word for word, _count in most_common]


def calculate_ats_score(resume_keywords, jd_keywords):
    """
    Calculate what percentage of the job description's keywords are also
    present in the resume's keywords. Returns a float rounded to 2 decimals.
    """
    if not jd_keywords:
        return 0.0
    resume_set = set(resume_keywords)
    matched = sum(1 for word in jd_keywords if word in resume_set)
    score = (matched / len(jd_keywords)) * 100
    return round(score, 2)


def find_missing_keywords(resume_keywords, jd_keywords):
    """
    Return a sorted list of keywords that appear in the job description's
    keyword list but not in the resume's keyword list.
    """
    resume_set = set(resume_keywords)
    missing = [word for word in jd_keywords if word not in resume_set]
    return sorted(set(missing))


def count_syllables(word):
    """Rough heuristic syllable counter based on vowel groupings."""
    word = word.lower()
    vowels = "aeiouy"
    syllables = 0
    previous_was_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not previous_was_vowel:
            syllables += 1
        previous_was_vowel = is_vowel
    if word.endswith("e") and syllables > 1:
        syllables -= 1
    return max(syllables, 1)


def calculate_readability(text):
    """
    Compute an approximate Flesch Reading Ease score for the given text.
    Higher scores (up to 100) indicate text that is easier to read.
    Returns 0.0 for empty text.
    """
    sentences = re.split(r"[.!?]+", text)
    sentences = [s for s in sentences if s.strip()]
    words = re.findall(r"[A-Za-z]+", text)

    if not sentences or not words:
        return 0.0

    total_syllables = sum(count_syllables(w) for w in words)
    words_per_sentence = len(words) / len(sentences)
    syllables_per_word = total_syllables / len(words)

    score = 206.835 - (1.015 * words_per_sentence) - (84.6 * syllables_per_word)
    return round(score, 2)


def interpret_readability(score):
    """Return a human-readable interpretation of a Flesch Reading Ease score."""
    if score >= 90:
        return "Very easy to read."
    elif score >= 60:
        return "Fairly easy to read — a good target for most resumes."
    elif score >= 30:
        return "Fairly difficult to read. Consider shorter sentences."
    else:
        return "Very difficult to read. Simplify sentence structure."


def check_formatting_issues(text):
    """
    Run simple heuristic checks for common resume formatting problems that
    can trip up an ATS. Returns a list of human-readable issue descriptions.
    """
    issues = []
    words = re.findall(r"[A-Za-z]+", text)
    word_count = len(words)

    if word_count < 150:
        issues.append("Resume seems too short (fewer than 150 words).")
    if word_count > 1200:
        issues.append("Resume seems too long (more than 1200 words).")

    if not re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text):
        issues.append("No email address detected.")

    if not re.search(r"(\+?\d[\d\-\s()]{7,}\d)", text):
        issues.append("No phone number detected.")

    if text.count("\t") > 5:
        issues.append("Resume contains many tab characters, which can confuse ATS parsers.")

    bullet_count = len(re.findall(r"[•●▪‣·]", text))
    if bullet_count == 0:
        issues.append("No bullet points detected — bullet points help ATS parsers and readers scan quickly.")

    first_person_count = len(re.findall(r"\bI\b", text))
    if first_person_count > 5:
        issues.append("Excessive use of first-person pronouns ('I') — resumes are usually written without them.")

    return issues


def skills_gap_analysis(resume_text, jd_text):
    """
    Compare the skills mentioned in the job description against the skills
    found in the resume, using a curated list of common skills (SKILLS_DB).
    Returns a dict with 'required_skills' and 'missing_skills' lists.
    """
    resume_tokens = set(clean_and_tokenize(resume_text))
    jd_tokens = set(clean_and_tokenize(jd_text))

    required_skills = sorted(jd_tokens & SKILLS_DB)
    missing_skills = sorted(skill for skill in required_skills if skill not in resume_tokens)

    return {"required_skills": required_skills, "missing_skills": missing_skills}


def generate_suggestions(missing_keywords, formatting_issues, readability_score):
    """
    Build a short list of actionable suggestions based on the analysis
    results produced by the other functions.
    """
    suggestions = []

    if missing_keywords:
        preview = ", ".join(missing_keywords[:8])
        suggestions.append(f"Add relevant missing keywords where truthful, e.g.: {preview}.")

    if readability_score < 30:
        suggestions.append("Simplify long sentences to improve readability.")

    for issue in formatting_issues:
        if "email" in issue.lower():
            suggestions.append("Add a professional email address near the top of your resume.")
        elif "phone" in issue.lower():
            suggestions.append("Add a phone number so recruiters can reach you.")
        elif "bullet" in issue.lower():
            suggestions.append("Use bullet points to list achievements and responsibilities.")
        elif "short" in issue.lower():
            suggestions.append("Expand on your experience and achievements with more detail.")
        elif "long" in issue.lower():
            suggestions.append("Trim your resume to focus on the most relevant experience.")
        elif "first-person" in issue.lower():
            suggestions.append("Remove first-person pronouns for a more professional tone.")
        elif "tab" in issue.lower():
            suggestions.append("Avoid tables and tab-based layouts; use simple text formatting instead.")

    if not suggestions:
        suggestions.append("Great job! No major improvements detected.")

    return suggestions


if __name__ == "__main__":
    main()
