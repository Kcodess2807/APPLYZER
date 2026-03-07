#fixed file, across each agents
from typing import Final


#weight given when technologies match between job and project
SCORING_WEIGHTS: Final[dict[str, int]] = {
    "technology_match": 3,   
    "skill_match": 2,        
    "keyword_match": 1,      
    "title_relevance": 2,    
}

#minimum total score required for a project to be considered relevant
MIN_PROJECT_SCORE: Final[int]=1



#rules to be followed, while parsing he csv file
CSV_COLUMN_MAPPINGS: Final[dict[str, list[str]]] = {
    "title":       ["job_title", "title", "position", "role", "JOB TITLE"],
    "company":     ["company", "company_name", "organization", "employer", "COMPANY NAME"],
    "url":         ["job_link", "url", "link", "job_url", "posting_url", "COMPANY URL"],
    "description": ["job_description", "description", "desc", "details", "JOB DESCRIPTION"],
    "email":       ["email", "contact_email", "hr_email", "recruiter_email", "CONTACT MAIL"],
    "location":    ["location", "city", "office_location", "LOCATION"],
}

#if these columns dont exist it will raise an error
REQUIRED_CSV_COLUMNS: Final[list[str]]=["title", "company", "description"]



#fall back mechanism
DEFAULT_MAX_PROJECTS: Final[int]=3
DEFAULT_RESUME_TEMPLATE: Final[str]="standard"
DEFAULT_COVER_LETTER_TONE: Final[str]="professional"


#maximum allowed runtime per agent before timeout handling kicks in
AGENT_TIMEOUT: Final[dict[str, int]]={
    "job_fetcher": 300,         
    "project_matcher": 60,       
    "resume_generator": 120,     
    "cover_letter_writer": 120,  
}


#retry attempts for recoverable failures
MAX_RETRIES: Final[int]=3

#delay between retries
RETRY_DELAY_SECONDS: Final[int]=1



#CSS selectors used while extracting job information
LINKEDIN_SELECTORS: Final[dict[str, str]]={
    "job_title": ".job-title",
    "company": ".company-name",
    "description": ".job-description",
}


#Google Sheets permissions

#OAuth scopes required for read-only sheet access
GOOGLE_SHEETS_SCOPES: Final[list[str]] = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]



#Order in which resume sections should appear
RESUME_SECTIONS_ORDER: Final[list[str]] = [
    "personal_info",
    "summary",
    "skills",
    "experience",
    "projects",
    "education",
    "certifications",
]

#Logical layout for generated cover letters
COVER_LETTER_SECTIONS: Final[list[str]] = [
    "header",
    "recipient",
    "opening",
    "body",
    "closing",
    "signature",
]



#used by skill extraction utilities to categorize detected skills
SKILL_CATEGORIES: Final[dict[str, list[str]]] = {
    "programming_languages": [
        "python", "javascript", "java", "c++", "go", "rust",
        "typescript", "ruby", "php", "swift", "kotlin", "scala",
    ],

    "frameworks": [
        "react", "angular", "vue", "django", "flask", "fastapi",
        "spring", "express", "nextjs", "nestjs", "laravel",
    ],

    "databases": [
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "cassandra", "dynamodb", "sqlite",
    ],

    "cloud": [
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "cloudformation", "ansible",
    ],

    "tools": [
        "git", "jenkins", "gitlab", "github actions", "circleci",
        "jira", "confluence", "slack",
    ],

    "machine_learning": [
        "scikit-learn", "xgboost", "lightgbm", "pandas", "numpy",
        "matplotlib", "seaborn",
    ],

    "deep_learning": [
        "pytorch", "tensorflow", "keras", "torch", "onnx",
    ],

    "generative_ai": [
        "llm", "large language models", "transformers",
        "huggingface", "hugging face",
        "openai", "gemini", "claude", "groq",
        "ollama", "langchain", "llamaindex",
        "rag", "retrieval augmented generation",
        "prompt engineering", "fine tuning",
        "embeddings", "vector database",
    ],

    "agentic_ai": [
        "ai agents", "agentic ai", "autonomous agents",
        "multi-agent systems", "tool calling",
        "function calling", "workflow orchestration",
        "crew ai", "autogen", "langgraph",
    ],

    "computer_vision": [
        "opencv", "yolo", "yolov5", "yolov8",
        "object detection", "image segmentation",
        "cnn", "resnet", "mobilenet",
    ],
}



#job title classification

# Keywords used to roughly categorize job roles
JOB_TITLE_KEYWORDS: Final[dict[str, list[str]]] = {
    "software_engineer": [
        "software", "engineer", "developer", "programmer",
        "application engineer", "software developer"
    ],

    "data_scientist": [
        "data scientist", "data science", "analyst",
        "ml", "machine learning", "predictive modeling",
    ],

    "machine_learning_engineer": [
        "machine learning engineer", "ml engineer",
        "ml developer", "ai engineer", "ai developer",
        "model engineer",
    ],

    "ai_engineer": [
        "artificial intelligence", "ai engineer",
        "ai developer", "ai specialist",
    ],

    "generative_ai_engineer": [
        "generative ai", "gen ai", "genai",
        "llm engineer", "llm developer",
        "prompt engineer", "prompt engineering",
        "rag engineer", "rag developer",
    ],

    "agentic_ai_engineer": [
        "agentic ai", "ai agents", "agent engineer",
        "multi agent", "autonomous agent",
        "langchain", "langgraph", "autogen", "crew ai",
    ],

    "nlp_engineer": [
        "nlp", "natural language processing",
        "text mining", "language model",
    ],

    "computer_vision_engineer": [
        "computer vision", "cv engineer",
        "image processing", "object detection",
        "opencv", "yolo",
    ],

    "mlops": [
        "mlops", "machine learning ops",
        "model deployment", "model serving",
        "ai infrastructure", "model pipeline",
    ],

    "data_engineer": [
        "data engineer", "data pipeline",
        "etl", "big data", "data platform",
    ],

    "devops": [
        "devops", "sre", "infrastructure", "platform",
    ],

    "frontend": [
        "frontend", "front-end", "ui",
        "react", "angular", "vue",
    ],

    "backend": [
        "backend", "back-end", "api", "server",
    ],

    "fullstack": [
        "fullstack", "full-stack", "full stack",
    ],
}

