# Forma — The right format. Every country.
# getforma.ai

from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from anthropic import Anthropic
from functools import wraps
from datetime import datetime, timedelta
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "forma-secret-change-me-in-prod")

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "forma2024")

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
DB_PATH = os.path.join(os.path.dirname(__file__), "forma.db")

# ── Database ──────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS generations (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            country      TEXT NOT NULL,
            country_name TEXT NOT NULL,
            flag         TEXT,
            created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip_hash      TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS email_leads (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            email      TEXT UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS generations (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                country     TEXT NOT NULL,
                country_name TEXT NOT NULL,
                flag        TEXT,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_hash     TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS email_leads (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                email      TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def log_generation(country, country_name, flag, ip=None):
    import hashlib
    ip_hash = hashlib.sha256((ip or "").encode()).hexdigest()[:16] if ip else None
    with get_db() as conn:
        conn.execute(
            "INSERT INTO generations (country, country_name, flag, ip_hash) VALUES (?, ?, ?, ?)",
            (country, country_name, flag, ip_hash)
        )
        conn.commit()

def save_lead(email):
    try:
        with get_db() as conn:
            conn.execute("INSERT OR IGNORE INTO email_leads (email) VALUES (?)", (email,))
            conn.commit()
        return True
    except Exception:
        return False

# ── Country configs ───────────────────────────────────────────────────────────

COUNTRY_CONFIGS = {
    "USA": {
        "name": "United States", "flag": "🇺🇸", "format": "American Resume",
        "rules": """
- NO photo, NO date of birth, NO age, NO marital status, NO nationality (discrimination laws)
- 1 page if under 10 years experience, max 2 pages
- Start every bullet with a strong action verb (Led, Built, Increased, Managed, Drove)
- Quantify ALL achievements with numbers, %, $, timeframes
- ATS-optimized: mirror keywords from the job description naturally
- Sections: Contact Info | Professional Summary | Work Experience | Skills | Education
- US date format: Month Year (e.g. June 2022 – Present)
- Address: City, State only — no full street address
"""
    },
    "UK": {
        "name": "United Kingdom", "flag": "🇬🇧", "format": "British CV",
        "rules": """
- Called a "CV" not a "resume"
- NO photo (discrimination laws)
- 2 pages is standard
- Start with a punchy Personal Profile/Statement (3–5 lines)
- Education can go before Experience if recent graduate
- Include: nationality or right-to-work statement if relevant
- UK date format: Month Year
- References section: "Available on request"
- Sections: Personal Details | Personal Profile | Work Experience | Education | Key Skills | Interests | References
"""
    },
    "Germany": {
        "name": "Germany", "flag": "🇩🇪", "format": "Lebenslauf",
        "rules": """
- PHOTO is mandatory — include a [PHOTO PLACEHOLDER] box at top right
- Include: Date of birth, place of birth, nationality, marital status, address
- Called "Lebenslauf" — must be titled as such
- 2–3 pages is completely normal and expected
- Strict reverse chronological order
- ALL employment gaps must be explained
- End with: City, Date, and "Unterschrift" (signature line)
- German date format: DD.MM.YYYY
- Section headers in German: Persönliche Daten | Berufserfahrung | Ausbildung | Kenntnisse | Sprachkenntnisse | Hobbys
- Language skills must include exact level (Muttersprache, C2, B2, etc.)
"""
    },
    "France": {
        "name": "France", "flag": "🇫🇷", "format": "CV Français",
        "rules": """
- Photo is optional but very common — include [PHOTO] placeholder
- Include: date of birth, nationality, address, driving licence if relevant
- 1 page strongly preferred (max 2)
- "Centres d'intérêt" (hobbies/interests) section is culturally important — always include it
- Language skills with CEFR levels (A1–C2)
- French date format: DD/MM/YYYY
- Sections: État Civil | Formation | Expériences Professionnelles | Compétences | Langues | Centres d'intérêt
"""
    },
    "Japan": {
        "name": "Japan", "flag": "🇯🇵", "format": "Rirekisho (履歴書)",
        "rules": """
- PHOTO mandatory — include [証明写真 PHOTO] placeholder (top right)
- Full name in kanji AND furigana (phonetic reading)
- Include: DOB, age, gender, current address, phone, email
- Education and Work History listed CHRONOLOGICALLY (oldest first) — OPPOSITE of Western style
- Use humble, formal language throughout
- Include: "志望動機" (Motivation for applying) — extremely important in Japan
- Include: 自己PR (Self-PR) section
- Include: 免許・資格 (Licenses & Certifications)
- Include: 趣味・特技 (Hobbies & Special Skills)
- Date: Use Japanese era if possible (e.g. 令和5年) alongside Western dates
- Sections: 個人情報 | 学歴 | 職歴 | 免許・資格 | 趣味・特技 | 自己PR | 志望動機
"""
    },
    "Australia": {
        "name": "Australia", "flag": "🇦🇺", "format": "Australian Resume",
        "rules": """
- NO photo
- 2–3 pages is acceptable and normal
- Include 2–3 referee names with full contact details OR "Referees available upon request"
- Include: Australian work rights / visa status if not a citizen
- Volunteer work and community involvement is highly valued — always include if applicable
- Casual professional tone — slightly warmer than US/UK
- Sections: Personal Details | Career Summary | Work Experience | Education | Skills | Volunteer Work | Referees
"""
    },
    "Canada": {
        "name": "Canada", "flag": "🇨🇦", "format": "Canadian Resume",
        "rules": """
- NO photo, NO age, NO marital status, NO nationality (human rights laws)
- 1–2 pages
- Include: Canadian work authorization status if applicable
- Include LinkedIn URL
- For Quebec or bilingual roles: French version or bilingual resume preferred
- Slightly more emphasis on soft skills than US
- Volunteer work valued
- Sections: Contact | Summary | Work Experience | Education | Skills | Volunteer Work
"""
    },
    "UAE": {
        "name": "UAE / Gulf", "flag": "🇦🇪", "format": "Gulf CV",
        "rules": """
- PHOTO expected — include [PHOTO] placeholder
- Include: nationality, date of birth, marital status, visa/work permit status
- 2–3 pages is standard
- Include: languages (Arabic proficiency is a major plus — always mention level)
- Include references section with full details
- Strong personal details section expected
- Religion may optionally be included
- Sections: Personal Information | Career Objective | Work Experience | Education | Skills | Languages | References
"""
    },
    "India": {
        "name": "India", "flag": "🇮🇳", "format": "Indian CV",
        "rules": """
- Photo is common — include [PHOTO] placeholder
- Include: DOB, nationality, marital status
- 2–3 pages
- Academic percentage/marks are important — include them
- End with a Declaration: "I hereby declare that all information given above is true and correct to the best of my knowledge."
- Include: languages known
- For fresh graduates: include internships, academic projects, and achievements
- Sections: Personal Details | Career Objective | Work Experience | Education | Technical Skills | Projects | Languages | Declaration
"""
    },
    "Singapore": {
        "name": "Singapore", "flag": "🇸🇬", "format": "Singapore CV",
        "rules": """
- Photo optional but common — include [PHOTO] placeholder
- Include: nationality, NRIC/Work Pass type if applicable
- 2 pages standard
- Language proficiency important (English + Mandarin/Malay/Tamil very relevant)
- Skills and certifications heavily valued
- Mix of Western efficiency and Asian personal detail
- Sections: Personal Particulars | Career Summary | Work Experience | Education | Skills | Certifications | Languages | References
"""
    },
    "Netherlands": {
        "name": "Netherlands", "flag": "🇳🇱", "format": "Dutch CV",
        "rules": """
- Photo becoming less common (anti-discrimination trend) — optional
- Include: DOB, address, driving licence
- 1–2 pages — Dutch culture prizes directness and conciseness
- Include LinkedIn URL prominently
- Language skills with levels (NT2, B2, C1, Native, etc.)
- Cover letter (motivatiebrief) is critically important in NL — mention to prepare one
- Sections: Persoonlijke gegevens | Werkervaring | Opleiding | Vaardigheden | Talen | Referenties
"""
    },
    "Brazil": {
        "name": "Brazil", "flag": "🇧🇷", "format": "Currículo Brasileiro",
        "rules": """
- Called "Currículo"
- Photo is expected — include [FOTO] placeholder
- Include: DOB, marital status, nationality, address
- Include: CNH (driver's license category) if applicable
- 1–2 pages
- Warmer, more personal tone than US/UK
- Include references
- Language skills section important
- Sections: Dados Pessoais | Objetivo | Experiência Profissional | Formação Acadêmica | Idiomas | Informações Adicionais | Referências
"""
    },
}

# ── Auth decorator ────────────────────────────────────────────────────────────

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

# ── Public routes ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", countries=COUNTRY_CONFIGS)

@app.route("/api/generate", methods=["POST"])
def generate_resume():
    try:
        data = request.json
        country_code = data.get("country", "USA")
        job_description = data.get("jobDescription", "")
        user_info = data.get("userInfo", {})

        config = COUNTRY_CONFIGS.get(country_code, COUNTRY_CONFIGS["USA"])

        prompt = f"""You are an expert resume writer with deep knowledge of hiring practices in {config["name"]}.

Create a complete, professional {config["format"]} tailored for the job description below.

━━━━━━━━━━━━━━━━━━━━━━━━
COUNTRY: {config["name"]}
FORMAT: {config["format"]}
━━━━━━━━━━━━━━━━━━━━━━━━

MANDATORY COUNTRY-SPECIFIC RULES (follow these exactly):
{config["rules"]}

━━━━━━━━━━━━━━━━━━━━━━━━
JOB DESCRIPTION:
{job_description}

━━━━━━━━━━━━━━━━━━━━━━━━
APPLICANT INFO:
Name: {user_info.get("name", "")}
Email: {user_info.get("email", "")}
Phone: {user_info.get("phone", "")}
Location: {user_info.get("location", "")}
Current/Recent Title: {user_info.get("currentTitle", "")}
Years of Experience: {user_info.get("yearsExperience", "")}
Key Skills: {user_info.get("skills", "")}
Work Experience Summary: {user_info.get("experience", "")}
Education: {user_info.get("education", "")}
Additional Info / Achievements: {user_info.get("additionalInfo", "")}

━━━━━━━━━━━━━━━━━━━━━━━━
INSTRUCTIONS:
1. Follow ALL country-specific rules above without exception
2. Extract keywords from the job description and weave them in naturally
3. Use the correct section headers for {config["name"]} (in local language if applicable)
4. Format using Markdown: ## for section headers, **bold** for company/school names, bullet points for achievements
5. Make achievements specific and impactful — invent plausible details if the user gave sparse info
6. Match the tone and style expected by {config["name"]} hiring managers
7. If the country requires a photo, write [📷 PHOTO] as a placeholder at the correct position
8. If a declaration/signature is required, include it at the end

Generate the complete resume now. Do not include any commentary — output ONLY the resume content."""

        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )

        resume_text = message.content[0].text

        # Log to DB
        log_generation(
            country=country_code,
            country_name=config["name"],
            flag=config["flag"],
            ip=request.remote_addr
        )

        return jsonify({
            "success": True,
            "resume": resume_text,
            "country": config["name"],
            "format": config["format"],
            "flag": config["flag"],
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/save-lead", methods=["POST"])
def save_lead_route():
    email = (request.json or {}).get("email", "").strip()
    if not email or "@" not in email:
        return jsonify({"success": False, "error": "Invalid email"}), 400
    save_lead(email)
    return jsonify({"success": True})

# ── Admin routes ──────────────────────────────────────────────────────────────

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USER and password == ADMIN_PASS:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            error = "Invalid credentials"
    return render_template("admin_login.html", error=error)

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    with get_db() as conn:
        # Totals
        total = conn.execute("SELECT COUNT(*) FROM generations").fetchone()[0]
        today_count = conn.execute(
            "SELECT COUNT(*) FROM generations WHERE DATE(created_at) = DATE('now')"
        ).fetchone()[0]
        week_count = conn.execute(
            "SELECT COUNT(*) FROM generations WHERE created_at >= datetime('now', '-7 days')"
        ).fetchone()[0]
        total_leads = conn.execute("SELECT COUNT(*) FROM email_leads").fetchone()[0]

        # By country
        by_country = conn.execute("""
            SELECT country_name, flag, COUNT(*) as cnt
            FROM generations
            GROUP BY country
            ORDER BY cnt DESC
        """).fetchall()

        # Daily trend (last 14 days)
        daily = conn.execute("""
            SELECT DATE(created_at) as day, COUNT(*) as cnt
            FROM generations
            WHERE created_at >= datetime('now', '-14 days')
            GROUP BY day
            ORDER BY day
        """).fetchall()

        # Recent activity
        recent = conn.execute("""
            SELECT country_name, flag, created_at
            FROM generations
            ORDER BY created_at DESC
            LIMIT 20
        """).fetchall()

        # Top country
        top_country = by_country[0] if by_country else None

        # Leads
        leads = conn.execute(
            "SELECT email, created_at FROM email_leads ORDER BY created_at DESC LIMIT 20"
        ).fetchall()

    return render_template("admin_dashboard.html",
        total=total,
        today_count=today_count,
        week_count=week_count,
        total_leads=total_leads,
        by_country=by_country,
        daily=daily,
        recent=recent,
        top_country=top_country,
        leads=leads,
    )

# ── Boot ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
