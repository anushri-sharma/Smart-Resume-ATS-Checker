# Smart Resume ATS Checker

#### Description:

Smart Resume ATS Checker is a command-line Python program that analyzes a
resume against a specific job description the way an Applicant Tracking
System (ATS) would, and then reports back a match score along with concrete
suggestions for improvement. Job seekers rarely get to see what an ATS
"sees" when it scans their resume, so this tool tries to make that process
transparent and actionable, right from the terminal.

## What the program does

The user provides two files: a resume and a job description, in `.txt`,
`.pdf`, or `.docx` format. The program then extracts the text from both
files and runs a series of analyses:

- **ATS Match Score** — a percentage representing how many of the job
  description's most important keywords also appear in the resume. This is
  the single number most real-world ATS dashboards show recruiters.
- **Missing Keywords** — the specific keywords from the job description
  that the resume does not currently contain, so the user knows exactly
  what to add (truthfully) to improve their match.
- **Skills Gap Analysis** — a comparison against a curated list of common
  technical and soft skills (Python, SQL, Docker, communication, teamwork,
  etc.). This is separate from the general keyword match because skills
  are the terms recruiters and ATS filters weight most heavily, and a
  generic word-frequency comparison alone can miss or bury them.
- **Readability Score** — an approximate Flesch Reading Ease score,
  calculated manually so the project does not depend on a large external
  NLP library. Higher scores mean the resume's sentences are easier to
  read; lower scores suggest overly long or complex sentences.
- **Formatting Problems** — heuristic checks for issues that commonly
  trip up ATS parsers or turn off a human reader: missing contact
  information (email or phone), resumes that are too short or too long,
  a lack of bullet points, heavy use of tab characters (often left behind
  by table-based layouts), and excessive use of first-person pronouns.
- **Suggestions** — a short, prioritized list of actionable next steps
  generated from the results above (e.g., "add these missing keywords" or
  "add a phone number").

## Project files

- **`project.py`** — Contains the entire program. `main()` parses command
  line arguments (`--resume`, `--jd`, and an optional `--top` for how many
  keywords to compare), coordinates all the analysis functions, and prints
  a formatted report. The remaining functions are all independent and
  individually testable:
  - `extract_text_from_file(filepath)` reads `.txt`, `.pdf` (via `PyPDF2`),
    and `.docx` (via `python-docx`) files and returns their plain text.
  - `clean_and_tokenize(text)` lowercases text, strips punctuation, and
    removes a hand-curated stopword list along with very short tokens, so
    that later keyword comparisons focus on meaningful words.
  - `extract_keywords(text, top_n)` returns the most frequent meaningful
    words in a piece of text using `collections.Counter`.
  - `calculate_ats_score(resume_keywords, jd_keywords)` computes what
    percentage of the job description's keywords also show up in the
    resume.
  - `find_missing_keywords(resume_keywords, jd_keywords)` returns the job
    description keywords absent from the resume.
  - `count_syllables(word)` is a small heuristic helper used to estimate
    syllables per word for the readability formula.
  - `calculate_readability(text)` implements the Flesch Reading Ease
    formula by hand, using sentence and syllable counts derived from the
    text.
  - `interpret_readability(score)` turns a numeric readability score into
    a short, human-readable description.
  - `check_formatting_issues(text)` runs a series of regex-based heuristic
    checks (contact info, resume length, bullet points, tab characters,
    pronoun overuse) and returns a list of issues found.
  - `skills_gap_analysis(resume_text, jd_text)` intersects the tokens from
    both documents with a curated `SKILLS_DB` set to identify which
    specific in-demand skills the job requires and which of those are
    missing from the resume.
  - `generate_suggestions(...)` converts the results of the analyses above
    into a short list of plain-English recommendations.

- **`test_project.py`** — Contains `pytest` tests for seven of the
  functions above (`clean_and_tokenize`, `extract_keywords`,
  `calculate_ats_score`, `find_missing_keywords`, `calculate_readability`,
  `check_formatting_issues`, and `skills_gap_analysis`), each verified
  against multiple representative inputs, including edge cases like empty
  text and zero job-description keywords.

- **`requirements.txt`** — Lists the pip-installable dependencies:
  `PyPDF2` (for reading PDF resumes), `python-docx` (for reading Word
  resumes), and `pytest` (for running the test suite).

- **`sample_resume.txt`** and **`sample_job_description.txt`** — Small
  example files included so the program can be tried out immediately
  without needing to supply your own documents.

## Design decisions

I considered using a full NLP library such as `nltk` or `spaCy` for
tokenization, stopword removal, and readability scoring. I decided against
it because those libraries typically require downloading additional
corpora or language models at runtime, which makes the project harder to
set up and less portable across grading environments. Instead, I
implemented a compact, hand-written stopword list and a simple
vowel-grouping syllable counter, which keep the dependency footprint small
while still producing reasonable, explainable results.

I also debated whether to build this as a web application (e.g., with
Flask) instead of a command-line tool. I chose the CLI approach because it
keeps the project focused on the core logic that this assignment is meant
to demonstrate — the text processing and analysis functions — while still
being genuinely useful: anyone can run it locally against their own resume
and a job posting in seconds.

Finally, keywords and skills are treated as two separate analyses on
purpose. A raw keyword-frequency match can easily be dominated by common
nouns from the job posting, while a dedicated, curated skills list (used
in `skills_gap_analysis`) surfaces the specific technical and soft skills
that actually determine whether a resume passes an ATS filter.

## How to run it

```bash
pip install -r requirements.txt
python project.py --resume sample_resume.txt --jd sample_job_description.txt
```

To run the test suite:

```bash
pytest test_project.py
```

#### Video Demo:  https://youtu.be/QiCVxHBciOA
