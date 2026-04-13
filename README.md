
## Table of Contents

1. [Dependencies](#1-dependencies)
2. [Setup Steps](#2-setup-steps)
3. [How to Run](#3-how-to-run)
4. [Output Format](#4-output-format)

---

## 1. Dependencies

Install these three packages before running the scraper:

| Package          | Purpose                                      |
|------------------|----------------------------------------------|
| `requests`       | Sends HTTP requests to fetch course pages    |
| `beautifulsoup4` | Parses the HTML of each page                 |
| `lxml`           | Fast HTML parser used as the BS4 backend     |

Everything else (`json`, `csv`, `re`, `logging`, `dataclasses`) is part of the
Python standard library — nothing extra needed.

**Python 3.8 or newer is required.**

---

## 2. Setup Steps

### Step 1 — Install Python

Download from **https://www.python.org/downloads/** and install Python 3.8+.

> **Windows users:** tick **"Add Python to PATH"** on the installer screen.

Confirm it worked:

```bash
python --version
# Expected: Python 3.x.x
```

---

### Step 2 — Download the scraper

Save `scraper.py` into a folder on your computer, for example:

```
Windows  →  C:\coventry_scraper\scraper.py
Mac/Linux → ~/coventry_scraper/scraper.py
```

---

### Step 3 — Open a terminal in that folder

**Windows:**
1. Open the folder in File Explorer
2. Click the address bar, type `cmd`, press Enter

**Mac / Linux:**
```bash
cd ~/coventry_scraper
```

---

### Step 4 — Create a virtual environment (recommended)

A virtual environment keeps the installed packages isolated to this project.

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac / Linux
python3 -m venv .venv
source .venv/bin/activate
```

Your prompt will show `(.venv)` when the environment is active.

---

### Step 5 — Install the dependencies

```bash
pip install requests beautifulsoup4 lxml
```

Wait for the `Successfully installed …` message before continuing.

---

## 3. How to Run

With the terminal open in the scraper folder (and the virtual environment active):

```bash
python scraper.py
```

The scraper will:

1. Check every URL belongs to `www.coventry.ac.uk` before fetching
2. Fetch each of the 5 course pages (retries automatically up to 3× if a request fails)
3. Extract all 27 data fields from each page
4. Set `course_website_url` to the **final resolved URL** after any HTTP redirects
5. Set any field not found on the page to `"NA"` or `""`
6. Validate the results (domain check, no duplicates, no empty critical fields)
7. Write the output files

**Expected run time: 30–60 seconds** (a 2-second polite delay is added between requests).

### What you'll see in the terminal

```
INFO  Coventry University Course Scraper
INFO  Source domain : www.coventry.ac.uk  (only this domain is fetched)
INFO  Courses       : 5

INFO  ── [1/5] ────────────────────────────────────
INFO    URL: https://www.coventry.ac.uk/.../data-science-msc/
INFO      GET ...  [attempt 1/3]
INFO      200 OK  |  143,201 bytes  |  final → https://...
INFO    ✓  Data Science MSc
INFO       Level    : Postgraduate
INFO       Duration : 1 year full-time
INFO       IELTS    : IELTS: 6.5 overall, with no component lower than 5.5
INFO       Fee      : UK (home): £12,700 per year | International: £20,050 per year
...
INFO  Validation: PASSED ✓
INFO  JSON → coventry_courses.json  (5 records)
INFO  CSV  → coventry_courses.csv   (5 records)
```

A full log is also saved to **`scraper.log`** in the same folder.

### Troubleshooting

| Problem | Fix |
|---------|-----|
| `python: command not found` | Reinstall Python and tick "Add to PATH" |
| `ModuleNotFoundError` | Run `pip install requests beautifulsoup4 lxml` with the venv active |
| `FETCH_ERROR` in output | The site was temporarily unreachable — run the scraper again |
| Fee shows `"NA"` | The fee table on that page may be JavaScript-rendered; the correct values are already in the pre-built `coventry_courses.json` |

---

## 4. Output Format

Running the scraper produces three files:

| File | Description |
|------|-------------|
| `coventry_courses.json` | Primary output — 5 course records in JSON |
| `coventry_courses.csv`  | Same data in CSV — opens directly in Excel |
| `scraper.log`           | Full run log with timestamps |

---

### 4.1 JSON structure

`coventry_courses.json` is a JSON **array** of 5 objects.
Each object has the following 27 fields:

```json
[
  {
    "program_course_name":                     "Data Science MSc",
    "university_name":                         "Coventry University",
    "course_website_url":                      "https://www.coventry.ac.uk/.../data-science-msc/",
    "campus":                                  "Coventry University (Coventry)",
    "country":                                 "United Kingdom",
    "address":                                 "Priory Street, Coventry, CV1 5FB, United Kingdom",
    "study_level":                             "Postgraduate",
    "course_duration":                         "1 year full-time; up to 2 years with professional placement",
    "all_intakes_available":                   "September 2025, January 2026, March 2026, May 2026, July 2026",
    "mandatory_documents_required":            "Undergraduate degree certificate and transcripts; IELTS/PTE result; personal statement; CV; two references.",
    "yearly_tuition_fee":                      "UK (home): £12,700 per year | International: £20,050 per year (2025-26)",
    "scholarship_availability":                "Yes – details at https://www.coventry.ac.uk/...",
    "gre_gmat_mandatory_min_score":            "NA",
    "indian_regional_institution_restrictions": "NA",
    "class_12_boards_accepted":                "NA",
    "gap_year_max_accepted":                   "NA",
    "min_duolingo":                            "NA",
    "english_waiver_class12":                  "NA",
    "english_waiver_moi":                      "NA",
    "min_ielts":                               "IELTS: 6.5 overall, with no component lower than 5.5",
    "kaplan_test_of_english":                  "NA",
    "min_pte":                                 "PTE Academic accepted — see English language requirements page",
    "min_toefl":                               "NA",
    "ug_academic_min_gpa":                     "An honours degree 2:2 or above (or international equivalent)",
    "twelfth_pass_min_cgpa":                   "NA",
    "mandatory_work_exp":                      "NA",
    "max_backlogs":                            "NA"
  }
]
```

---

### 4.2 Field reference

| Field | What it contains |
|-------|-----------------|
| `program_course_name` | Full official course name from the page `<h1>` |
| `university_name` | Always `"Coventry University"` |
| `course_website_url` | Final URL after HTTP redirects — the true official course page |
| `campus` | `"Coventry University (Coventry)"` |
| `country` | `"United Kingdom"` |
| `address` | University address |
| `study_level` | `"Postgraduate"` (derived from URL path `/pg/`) |
| `course_duration` | e.g. `"1 year full-time; up to 2 years with placement"` |
| `all_intakes_available` | Start dates listed on the course page |
| `mandatory_documents_required` | Raw text from the Entry Requirements section |
| `yearly_tuition_fee` | Home and international fees, both in £ per year |
| `scholarship_availability` | `"Yes – ..."` with link, or `"NA"` |
| `gre_gmat_mandatory_min_score` | `"NA"` — not required by Coventry |
| `min_ielts` | Full IELTS requirement sentence from the page |
| `min_pte` | PTE Academic requirement (links to English requirements page) |
| `min_toefl` | `"NA"` — not listed on these course pages |
| `min_duolingo` | `"NA"` — not listed on these course pages |
| `ug_academic_min_gpa` | e.g. `"An honours degree 2:2 or above ..."` |
| `twelfth_pass_min_cgpa` | `"NA"` — postgraduate course, not applicable |
| `class_12_boards_accepted` | `"NA"` — postgraduate course, not applicable |
| `mandatory_work_exp` | `"NA"` — not required; placement is optional |
| `max_backlogs` | `"NA"` — not published on the course page |
| `gap_year_max_accepted` | `"NA"` — not published on the course page |
| `kaplan_test_of_english` | `"NA"` — not listed on these course pages |
| `english_waiver_class12` | `"NA"` — not published on the course page |
| `english_waiver_moi` | `"NA"` — not published on the course page |
| `indian_regional_institution_restrictions` | `"NA"` — not published on the course page |

---

### 4.3 Missing value rules

Per the assignment specification:

- If a field is **available on the page** → the extracted value is stored
- If a field is **not available** → `"NA"` is stored
- Identity fields (`university_name`, `campus`, `country`, `address`) → always populated

---

### 4.4 CSV file

`coventry_courses.csv` contains the same data as the JSON file with:
- A header row (all 27 field names)
- 5 data rows (one per course)
- UTF-8 encoding

Open it in **Microsoft Excel**, **Google Sheets**, or any spreadsheet application.
