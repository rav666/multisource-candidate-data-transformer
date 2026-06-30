"""
skills.py — Canonical skill name mapping and deduplication.

The SKILL_MAP is intentionally broad; the transformer will always accept unknown
skills (returning them title-cased) rather than silently dropping them.
"""

SKILL_MAP: dict[str, str] = {
    # Languages
    "py": "Python", "python3": "Python", "python2": "Python", "python": "Python",
    "js": "JavaScript", "javascript": "JavaScript",
    "ts": "TypeScript", "typescript": "TypeScript",
    "c++": "C++", "cpp": "C++",
    "c#": "C#", "csharp": "C#",
    "go": "Go", "golang": "Go",
    "rb": "Ruby", "ruby": "Ruby",
    "rs": "Rust", "rust": "Rust",
    "php": "PHP",
    "scala": "Scala",
    "kotlin": "Kotlin",
    "swift": "Swift",
    "r": "R",
    "matlab": "MATLAB",
    "shell": "Shell Scripting", "bash": "Shell Scripting",
    "sql": "SQL",
    "html": "HTML", "html5": "HTML",
    "css": "CSS", "css3": "CSS",
    "java": "Java",
    "c": "C",

    # Web frameworks
    "nodejs": "Node.js", "node": "Node.js", "node.js": "Node.js",
    "react": "React", "reactjs": "React", "react.js": "React",
    "vue": "Vue.js", "vuejs": "Vue.js",
    "angular": "Angular", "angularjs": "Angular",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "spring": "Spring", "springboot": "Spring Boot", "spring boot": "Spring Boot",
    "express": "Express.js", "expressjs": "Express.js",
    "nextjs": "Next.js", "next.js": "Next.js",
    "rails": "Ruby on Rails",

    # Databases
    "postgres": "PostgreSQL", "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB", "mongo": "MongoDB",
    "redis": "Redis",
    "sqlite": "SQLite",
    "cassandra": "Cassandra",
    "elasticsearch": "Elasticsearch",
    "dynamodb": "DynamoDB",
    "mssql": "Microsoft SQL Server", "sql server": "Microsoft SQL Server",

    # Cloud & DevOps
    "aws": "AWS", "amazon web services": "AWS",
    "gcp": "GCP", "google cloud": "GCP", "google cloud platform": "GCP",
    "azure": "Azure", "microsoft azure": "Azure",
    "k8s": "Kubernetes", "kubernetes": "Kubernetes",
    "docker": "Docker",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "ci/cd": "CI/CD", "cicd": "CI/CD",
    "jenkins": "Jenkins",
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "unix": "Linux/Unix", "linux": "Linux/Unix",

    # ML / Data
    "ml": "Machine Learning", "machine learning": "Machine Learning",
    "dl": "Deep Learning", "deep learning": "Deep Learning",
    "ai": "Artificial Intelligence", "artificial intelligence": "Artificial Intelligence",
    "nlp": "NLP", "natural language processing": "NLP",
    "cv": "Computer Vision", "computer vision": "Computer Vision",
    "sklearn": "Scikit-Learn", "scikit-learn": "Scikit-Learn", "scikit learn": "Scikit-Learn",
    "tensorflow": "TensorFlow", "tf": "TensorFlow",
    "pytorch": "PyTorch", "torch": "PyTorch",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "matplotlib": "Matplotlib",
    "seaborn": "Seaborn",
    "powerbi": "Power BI", "power bi": "Power BI",
    "tableau": "Tableau",
    "streamlit": "Streamlit",
    "jupyter": "Jupyter",

    # APIs & protocols
    "rest": "REST API", "rest api": "REST API", "restful": "REST API",
    "graphql": "GraphQL",
    "grpc": "gRPC",
    "postman": "Postman",

    # Other tools
    "excel": "Excel",
    "jira": "Jira",
    "confluence": "Confluence",
    "figma": "Figma",
    "beautifulsoup": "BeautifulSoup", "beautiful soup": "BeautifulSoup",
    "pygame": "Pygame",
    "sentence transformers": "Sentence Transformers",
    "google gemini api": "Google Gemini API",
    "gemini": "Google Gemini API",
}


def normalize_skill(skill: str | None) -> str | None:
    """Return canonical skill name or title-cased original if unknown."""
    if not skill:
        return None

    key = skill.strip().lower()
    return SKILL_MAP.get(key, skill.strip().title())


def normalize_skills(skills: list[str]) -> list[str]:
    """Deduplicate and canonicalize a list of skill strings."""
    seen: set[str] = set()
    result: list[str] = []

    for raw in skills:
        canonical = normalize_skill(raw)

        if canonical and canonical not in seen:
            seen.add(canonical)
            result.append(canonical)

    return result
