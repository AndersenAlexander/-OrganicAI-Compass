from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol
from urllib.parse import urlparse

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.assessment import AssessmentResponse, AssessmentSession, CareerMatch, CareerRoleTemplate, SkillsInventory
from app.models.learning import (
    ExternalProviderCache,
    LearningObjective,
    LearningPath,
    LearningPathItem,
    LearningPathPhase,
    LearningPreferences,
    LearningProvider,
    LearningRecommendation,
    LearningRecommendationFactor,
    LearningRecommendationRun,
    LearningResource,
    LearningResourceComparison,
    LearningResourceFeedback,
    LearningResourceObjective,
    LearningResourceSkill,
    LearningResourceVerification,
    LearningResourceVersion,
    PracticalProject,
    RoadmapLearningAction,
    SkillGapAnalysis,
    SkillGapItem,
)
from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.models.roadmap_adaptation import RoadmapAction
from app.services.assessment_engine import SKILL_LEVEL_LABELS, title_case_slug
from app.services.profile_generation import generate_roadmap_fallback
from app.services.roadmap_adaptation import event as roadmap_event
from app.services.roadmap_adaptation import normalize_legacy, snapshot

LEARNING_CATALOGUE_VERSION = "learning-catalogue-v1"
SKILL_GAP_VERSION = "skill-gap-v1"
LEARNING_OBJECTIVE_VERSION = "learning-objective-v1"
LEARNING_RECOMMENDATION_VERSION = "learning-rec-v1"

NO_CAREER_SELECTED_MESSAGE = "Select or save a career direction before generating a personalised learning path."

RESOURCE_ALIGNMENT_WEIGHTS = {
    "skill_gap_relevance": 0.30,
    "level_compatibility": 0.15,
    "objective_coverage": 0.15,
    "source_quality": 0.10,
    "language_fit": 0.08,
    "time_fit": 0.07,
    "budget_fit": 0.05,
    "practical_evidence_value": 0.05,
    "freshness": 0.03,
    "format_preference": 0.02,
}

RESOURCE_TYPE_LABELS = {
    "internal_article": "Internal article",
    "internal_guided_module": "Internal guided module",
    "official_documentation": "Official documentation",
    "online_course": "Online course",
    "youtube_video": "YouTube video",
    "youtube_playlist": "YouTube playlist",
    "practical_project": "Practical project",
    "portfolio_project": "Portfolio project",
    "interactive_tutorial": "Interactive tutorial",
    "book_or_chapter": "Book or chapter",
    "certification_preparation": "Certification preparation",
    "workshop": "Workshop",
    "mentoring_activity": "Mentoring activity",
    "professional_interview": "Professional interview",
    "job_description_analysis_exercise": "Job-description analysis exercise",
}

LEVEL_VALUES = {
    "no_experience": 0,
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3,
    "expert": 4,
    "mixed": 2,
}

EVIDENCE_STRENGTH = {
    "self_reported": 1,
    "supported_by_experience": 2,
    "supported_by_project": 3,
    "supported_by_certification": 4,
    "practically_verified": 5,
}

PREREQUISITES = {
    "apis": ["software_development"],
    "databases": ["data_analysis"],
    "automation": ["apis"],
    "evaluation": ["critical_thinking"],
    "rag_fundamentals": ["software_development", "apis"],
    "quality_assurance": ["problem_solving"],
    "leadership": ["communication"],
    "client_relations": ["communication"],
}

AI_AUGMENTABLE_SKILLS = {
    "ai_tools",
    "automation",
    "communication",
    "critical_thinking",
    "data_analysis",
    "evaluation",
    "ideation",
    "planning",
    "research",
    "systems_thinking",
    "visual_communication",
    "writing",
}

PROVIDERS = [
    ("internal", "Internal curated catalogue", "internal", "/learning/internal"),
    ("official_documentation", "Official documentation", "official", None),
    ("youtube", "YouTube", "external_video", "https://www.youtube.com"),
    ("udemy", "Udemy", "external_course", "https://www.udemy.com"),
    ("coursera", "Coursera", "external_course", "https://www.coursera.org"),
    ("edx", "edX", "external_course", "https://www.edx.org"),
    ("microsoft_learn", "Microsoft Learn", "official_course", "https://learn.microsoft.com"),
    ("google_learning", "Google Learning", "official_course", "https://developers.google.com"),
    ("aws_skill_builder", "AWS Skill Builder", "official_course", "https://skillbuilder.aws"),
    ("nvidia_dli", "NVIDIA Deep Learning Institute", "official_course", "https://www.nvidia.com"),
    ("other", "Other curated external provider", "external", None),
]


def _res(
    resource_id: str,
    provider: str,
    title: str,
    url: str,
    resource_type: str,
    skills: list[str],
    *,
    level: str = "beginner",
    duration: int | None = None,
    cost: str = "free",
    org: str | None = None,
    certificate: bool | None = None,
    project: bool = False,
    exercises: bool = False,
    objectives: list[str] | None = None,
    quality: str = "Partially verified",
    verified: str = "2026-07-20T00:00:00",
    notes: str = "Metadata is curated for the prototype; check provider page for the current details.",
    price: float | None = None,
    currency: str | None = None,
    subtitles: list[str] | None = None,
    prerequisites: list[str] | None = None,
    provenance: str = "manual curated MVP catalogue",
) -> dict[str, Any]:
    return {
        "id": resource_id,
        "provider": provider,
        "title": title,
        "canonical_url": url,
        "description": notes,
        "resource_type": resource_type,
        "skill_ids": skills,
        "objective_keys": objectives or skills,
        "level": level,
        "language": "en",
        "subtitles": subtitles or [],
        "duration_minutes": duration,
        "cost_type": cost,
        "displayed_price": price,
        "currency": currency,
        "instructor_organization": org,
        "rating": None,
        "review_count": None,
        "publication_date": None,
        "last_updated_date": None,
        "last_verified_at": verified,
        "prerequisites": prerequisites or [],
        "certificate_available": certificate,
        "practical_exercises": exercises,
        "project_included": project,
        "quality_status": quality,
        "source_provenance": provenance,
        "active": True,
        "affiliate": False,
        "affiliate_disclosure": "No affiliate relationship is used for ranking.",
        "notes_limitations": notes,
    }


RESOURCE_CATALOGUE = [
    _res("internal_ai_literacy_primer", "internal", "OrganicAI AI Literacy Primer", "/knowledge-base/ai_literacy", "internal_article", ["ai_tools"], level="beginner", duration=45, org="OrganicAI Compass", quality="Verified", exercises=True),
    _res("internal_responsible_ai_review", "internal", "OrganicAI Responsible AI and Human Oversight Notes", "/knowledge-base/responsible_ai", "internal_article", ["ai_tools", "evaluation", "critical_thinking"], level="beginner", duration=60, org="OrganicAI Compass", quality="Verified", exercises=True),
    _res("internal_human_ai_collaboration", "internal", "OrganicAI Human-AI Collaboration Patterns", "/knowledge-base/human_ai_collaboration", "internal_article", ["communication", "ai_tools", "systems_thinking"], level="beginner", duration=50, org="OrganicAI Compass", quality="Verified"),
    _res("internal_future_work_transition", "internal", "OrganicAI Future of Work Transition Notes", "/knowledge-base/future_of_work", "internal_article", ["planning", "communication", "systems_thinking"], level="beginner", duration=50, org="OrganicAI Compass", quality="Verified"),
    _res("internal_learning_quality", "internal", "OrganicAI Learning Resource Quality Guide", "/knowledge-base/learning_resource_recommendations", "internal_article", ["research", "evaluation", "critical_thinking"], level="beginner", duration=45, org="OrganicAI Compass", quality="Verified"),
    _res("internal_skill_gap_reflection", "internal", "Skill-Gap Reflection and Evidence Worksheet", "/learning/internal/skill-gap-evidence-worksheet", "internal_guided_module", ["planning", "research", "communication"], level="beginner", duration=90, org="OrganicAI Compass", quality="Verified", exercises=True),
    _res("project_ai_product_interface", "internal", "Portfolio Project: Explainable AI Recommendation Interface", "/learning/projects/explainable-ai-recommendation-interface", "portfolio_project", ["ux_ui", "ai_tools", "visual_communication", "evaluation"], level="intermediate", duration=480, org="OrganicAI Compass", quality="Verified", project=True, exercises=True, prerequisites=["ux_ui"]),
    _res("project_rag_service", "internal", "Practical Project: Source-Grounded RAG Service", "/learning/projects/source-grounded-rag-service", "practical_project", ["software_development", "apis", "databases", "evaluation", "ai_tools"], level="intermediate", duration=720, org="OrganicAI Compass", quality="Verified", project=True, exercises=True, prerequisites=["software_development", "apis"]),
    _res("project_ai_workflow_audit", "internal", "Practical Project: AI-Assisted Workflow Audit", "/learning/projects/ai-assisted-workflow-audit", "practical_project", ["automation", "planning", "systems_thinking", "communication"], level="beginner", duration=300, org="OrganicAI Compass", quality="Verified", project=True, exercises=True),
    _res("project_accessible_react_app", "internal", "Portfolio Project: Accessible React API Application", "/learning/projects/accessible-react-api-application", "portfolio_project", ["software_development", "ux_ui", "apis", "quality_assurance"], level="intermediate", duration=720, org="OrganicAI Compass", quality="Verified", project=True, exercises=True, prerequisites=["software_development"]),
    _res("project_data_story", "internal", "Portfolio Project: Public Dataset Analysis and Data Story", "/learning/projects/public-dataset-data-story", "portfolio_project", ["data_analysis", "databases", "writing", "visual_communication"], level="beginner", duration=360, org="OrganicAI Compass", quality="Verified", project=True, exercises=True),
    _res("project_ux_research_case", "internal", "Portfolio Project: Small UX Research Case Study", "/learning/projects/small-ux-research-case-study", "portfolio_project", ["research", "ux_ui", "communication", "writing"], level="beginner", duration=360, org="OrganicAI Compass", quality="Verified", project=True, exercises=True),
    _res("project_portfolio_case_study", "internal", "Portfolio Exercise: Role-Specific Case Study Rewrite", "/learning/projects/role-specific-case-study-rewrite", "portfolio_project", ["writing", "visual_communication", "communication"], level="beginner", duration=180, org="OrganicAI Compass", quality="Verified", project=True),
    _res("exercise_job_description_analysis", "internal", "Job-Description Analysis Exercise", "/learning/exercises/job-description-analysis", "job_description_analysis_exercise", ["research", "planning", "critical_thinking"], level="beginner", duration=90, org="OrganicAI Compass", quality="Verified", exercises=True),
    _res("activity_professional_interview", "internal", "Professional Interview Guide for Career Validation", "/learning/exercises/professional-interview-guide", "professional_interview", ["communication", "research", "client_relations"], level="beginner", duration=120, org="OrganicAI Compass", quality="Verified", exercises=True),
    _res("workshop_peer_portfolio_review", "internal", "Peer Portfolio Review Workshop Template", "/learning/workshops/peer-portfolio-review", "workshop", ["communication", "visual_communication", "quality_assurance"], level="beginner", duration=120, org="OrganicAI Compass", quality="Verified", exercises=True),
    _res("nist_ai_rmf", "official_documentation", "NIST AI Risk Management Framework", "https://www.nist.gov/itl/ai-risk-management-framework", "official_documentation", ["ai_tools", "evaluation", "critical_thinking"], level="intermediate", duration=180, org="NIST", quality="Verified"),
    _res("owasp_llm_top10", "official_documentation", "OWASP Top 10 for Large Language Model Applications", "https://owasp.org/www-project-top-10-for-large-language-model-applications/", "official_documentation", ["ai_tools", "evaluation", "quality_assurance"], level="intermediate", duration=150, org="OWASP", quality="Verified"),
    _res("google_pair_guidebook", "official_documentation", "People + AI Guidebook", "https://pair.withgoogle.com/guidebook/", "official_documentation", ["ux_ui", "ai_tools", "research", "visual_communication"], level="beginner", duration=180, org="Google PAIR", quality="Verified", exercises=True),
    _res("microsoft_responsible_ai", "official_documentation", "Microsoft Responsible AI", "https://www.microsoft.com/ai/responsible-ai", "official_documentation", ["ai_tools", "evaluation", "critical_thinking"], level="beginner", duration=90, org="Microsoft", quality="Verified"),
    _res("google_responsible_ai_practices", "official_documentation", "Google Responsible AI Practices", "https://ai.google/responsibility/responsible-ai-practices/", "official_documentation", ["ai_tools", "evaluation", "research"], level="beginner", duration=90, org="Google", quality="Verified"),
    _res("react_learn", "official_documentation", "React Learn", "https://react.dev/learn", "official_documentation", ["software_development", "ux_ui"], level="beginner", duration=480, org="React", quality="Verified", exercises=True),
    _res("typescript_handbook", "official_documentation", "The TypeScript Handbook", "https://www.typescriptlang.org/docs/handbook/intro.html", "official_documentation", ["software_development"], level="beginner", duration=420, org="Microsoft", quality="Verified", exercises=True),
    _res("mdn_accessibility", "official_documentation", "MDN Web Docs: Accessibility", "https://developer.mozilla.org/en-US/docs/Web/Accessibility", "official_documentation", ["ux_ui", "quality_assurance", "software_development"], level="beginner", duration=240, org="Mozilla", quality="Verified"),
    _res("webdev_accessibility", "official_documentation", "web.dev Learn Accessibility", "https://web.dev/learn/accessibility/", "official_documentation", ["ux_ui", "quality_assurance", "software_development"], level="beginner", duration=360, org="Google", quality="Verified", exercises=True),
    _res("fastapi_tutorial", "official_documentation", "FastAPI Tutorial", "https://fastapi.tiangolo.com/tutorial/", "official_documentation", ["apis", "software_development"], level="beginner", duration=420, org="FastAPI", quality="Verified", exercises=True, prerequisites=["software_development"]),
    _res("python_tutorial", "official_documentation", "The Python Tutorial", "https://docs.python.org/3/tutorial/", "official_documentation", ["software_development", "data_analysis"], level="beginner", duration=540, org="Python Software Foundation", quality="Verified", exercises=True),
    _res("postgresql_tutorial", "official_documentation", "PostgreSQL Tutorial", "https://www.postgresql.org/docs/current/tutorial.html", "official_documentation", ["databases"], level="beginner", duration=240, org="PostgreSQL", quality="Verified"),
    _res("sqlbolt", "other", "SQLBolt", "https://sqlbolt.com/", "interactive_tutorial", ["databases", "data_analysis"], level="beginner", duration=240, org="SQLBolt", quality="Partially verified", exercises=True),
    _res("pandas_user_guide", "official_documentation", "pandas User Guide", "https://pandas.pydata.org/docs/user_guide/", "official_documentation", ["data_analysis"], level="intermediate", duration=600, org="pandas", quality="Verified", prerequisites=["data_analysis"]),
    _res("kaggle_python", "other", "Kaggle Learn: Python", "https://www.kaggle.com/learn/python", "interactive_tutorial", ["software_development", "data_analysis"], level="beginner", duration=300, org="Kaggle", quality="Partially verified", certificate=True, exercises=True),
    _res("kaggle_pandas", "other", "Kaggle Learn: Pandas", "https://www.kaggle.com/learn/pandas", "interactive_tutorial", ["data_analysis"], level="beginner", duration=240, org="Kaggle", quality="Partially verified", certificate=True, exercises=True),
    _res("google_ml_crash_course", "google_learning", "Machine Learning Crash Course", "https://developers.google.com/machine-learning/crash-course", "online_course", ["data_analysis", "ai_tools", "evaluation"], level="intermediate", duration=900, org="Google", quality="Verified", certificate=False, exercises=True),
    _res("microsoft_genai_beginners", "microsoft_learn", "Generative AI for Beginners", "https://github.com/microsoft/generative-ai-for-beginners", "online_course", ["ai_tools", "prompt_design", "evaluation"], level="beginner", duration=720, org="Microsoft", quality="Verified", exercises=True),
    _res("langchain_rag_tutorial", "official_documentation", "LangChain RAG Tutorial", "https://python.langchain.com/docs/tutorials/rag/", "official_documentation", ["ai_tools", "software_development", "apis", "evaluation"], level="intermediate", duration=240, org="LangChain", quality="Verified", exercises=True, prerequisites=["software_development", "apis"]),
    _res("w3c_accessibility_intro", "official_documentation", "W3C WAI: Introduction to Web Accessibility", "https://www.w3.org/WAI/fundamentals/accessibility-intro/", "official_documentation", ["ux_ui", "quality_assurance"], level="beginner", duration=90, org="W3C WAI", quality="Verified"),
    _res("scrum_guide", "official_documentation", "The Scrum Guide", "https://scrumguides.org/scrum-guide.html", "official_documentation", ["planning", "coordination", "leadership"], level="beginner", duration=120, org="Scrum.org and Scrum Inc.", quality="Verified"),
    _res("coursera_ai_for_everyone", "coursera", "AI For Everyone", "https://www.coursera.org/learn/ai-for-everyone", "online_course", ["ai_tools", "communication", "planning"], level="beginner", duration=360, org="DeepLearning.AI", certificate=True, quality="Partially verified", cost="paid_or_audit"),
    _res("coursera_google_ux", "coursera", "Google UX Design Professional Certificate", "https://www.coursera.org/professional-certificates/google-ux-design", "certification_preparation", ["ux_ui", "research", "visual_communication"], level="beginner", duration=6000, org="Google", certificate=True, quality="Partially verified", cost="paid_or_audit", project=True),
    _res("coursera_google_data_analytics", "coursera", "Google Data Analytics Professional Certificate", "https://www.coursera.org/professional-certificates/google-data-analytics", "certification_preparation", ["data_analysis", "databases", "visual_communication"], level="beginner", duration=6000, org="Google", certificate=True, quality="Partially verified", cost="paid_or_audit", project=True),
    _res("edx_cs50x", "edx", "CS50's Introduction to Computer Science", "https://www.edx.org/learn/computer-science/harvard-university-cs50-s-introduction-to-computer-science", "online_course", ["software_development", "critical_thinking", "problem_solving"], level="beginner", duration=7200, org="Harvard University", certificate=True, quality="Partially verified", cost="paid_or_audit", exercises=True),
    _res("edx_cs50p", "edx", "CS50's Introduction to Programming with Python", "https://www.edx.org/learn/python/harvard-university-cs50-s-introduction-to-programming-with-python", "online_course", ["software_development", "data_analysis"], level="beginner", duration=3600, org="Harvard University", certificate=True, quality="Partially verified", cost="paid_or_audit", exercises=True),
    _res("freecodecamp_responsive_web_design", "other", "freeCodeCamp Responsive Web Design", "https://www.freecodecamp.org/learn/2022/responsive-web-design/", "interactive_tutorial", ["ux_ui", "software_development", "visual_communication"], level="beginner", duration=1800, org="freeCodeCamp", quality="Partially verified", certificate=True, exercises=True, project=True),
    _res("freecodecamp_js", "other", "freeCodeCamp JavaScript Algorithms and Data Structures", "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures-v8/", "interactive_tutorial", ["software_development", "problem_solving"], level="beginner", duration=2400, org="freeCodeCamp", quality="Partially verified", certificate=True, exercises=True),
    _res("microsoft_ai_fundamentals_path", "microsoft_learn", "Microsoft Learn: Get started with artificial intelligence", "https://learn.microsoft.com/en-us/training/paths/get-started-with-artificial-intelligence-on-azure/", "online_course", ["ai_tools", "evaluation"], level="beginner", duration=240, org="Microsoft Learn", quality="Partially verified", certificate=True, exercises=True),
    _res("google_cloud_intro_genai", "google_learning", "Introduction to Generative AI", "https://www.cloudskillsboost.google/course_templates/536", "online_course", ["ai_tools", "prompt_design"], level="beginner", duration=60, org="Google Cloud Skills Boost", quality="Partially verified", certificate=True),
    _res("udemy_react_complete_guide", "udemy", "React - The Complete Guide", "https://www.udemy.com/course/react-the-complete-guide-incl-redux/", "online_course", ["software_development", "ux_ui"], level="intermediate", duration=2400, org="Udemy instructor", quality="Partially verified", cost="paid", certificate=True, project=True, prerequisites=["software_development"]),
    _res("udemy_automate_boring_stuff", "udemy", "Automate the Boring Stuff with Python Programming", "https://www.udemy.com/course/automate/", "online_course", ["software_development", "automation"], level="beginner", duration=600, org="Udemy instructor", quality="Partially verified", cost="paid", certificate=True, exercises=True),
    _res("udemy_python_data_science_ml", "udemy", "Python for Data Science and Machine Learning Bootcamp", "https://www.udemy.com/course/python-for-data-science-and-machine-learning-bootcamp/", "online_course", ["data_analysis", "software_development"], level="intermediate", duration=1500, org="Udemy instructor", quality="Partially verified", cost="paid", certificate=True, project=True, prerequisites=["software_development"]),
    _res("youtube_freecodecamp_playlists", "youtube", "freeCodeCamp.org YouTube playlists", "https://www.youtube.com/@freecodecamp/playlists", "youtube_playlist", ["software_development", "apis", "data_analysis", "ux_ui"], level="mixed", duration=None, org="freeCodeCamp.org", quality="Partially verified", subtitles=["en"]),
    _res("youtube_google_chrome_developers", "youtube", "Google Chrome for Developers YouTube playlists", "https://www.youtube.com/@ChromeDevs/playlists", "youtube_playlist", ["software_development", "ux_ui", "quality_assurance"], level="mixed", duration=None, org="Google Chrome for Developers", quality="Partially verified", subtitles=["en"]),
    _res("youtube_nngroup_playlists", "youtube", "Nielsen Norman Group YouTube playlists", "https://www.youtube.com/@NNgroup/playlists", "youtube_playlist", ["ux_ui", "research", "communication"], level="mixed", duration=None, org="Nielsen Norman Group", quality="Partially verified", subtitles=["en"]),
    _res("youtube_microsoft_developer", "youtube", "Microsoft Developer YouTube playlists", "https://www.youtube.com/@MicrosoftDeveloper/playlists", "youtube_playlist", ["ai_tools", "software_development", "apis"], level="mixed", duration=None, org="Microsoft Developer", quality="Partially verified", subtitles=["en"]),
]


@dataclass(frozen=True)
class LearningResourceQuery:
    profile_id: str
    skill_ids: list[str]
    objective_keys: list[str]
    language: str = "en"
    provider_names: list[str] | None = None
    limit: int = 50


@dataclass(frozen=True)
class ExternalLearningResource:
    external_id: str
    provider: str
    title: str
    canonical_url: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ResourceAvailability:
    available: bool
    status: str
    checked_at: datetime
    error_message: str = ""


class LearningProviderAdapter(Protocol):
    provider_name: str

    def search_resources(self, query: LearningResourceQuery) -> list[ExternalLearningResource]:
        ...

    def get_resource(self, external_id: str) -> ExternalLearningResource | None:
        ...

    def check_availability(self, external_id: str) -> ResourceAvailability:
        ...


class CuratedCatalogueProvider:
    provider_name = "curated_catalogue"

    def __init__(self, db: Session):
        self.db = db

    def search_resources(self, query: LearningResourceQuery) -> list[ExternalLearningResource]:
        skill_rows = self.db.scalars(select(LearningResourceSkill).where(LearningResourceSkill.skill_id.in_(query.skill_ids))).all() if query.skill_ids else []
        resource_ids = {row.resource_id for row in skill_rows}
        if not resource_ids:
            return []
        statement = select(LearningResource).where(LearningResource.id.in_(resource_ids), LearningResource.active.is_(True))
        if query.provider_names:
            providers = self.db.scalars(select(LearningProvider.id).where(LearningProvider.provider_name.in_(query.provider_names))).all()
            statement = statement.where(LearningResource.provider_id.in_(providers))
        rows = self.db.scalars(statement.limit(query.limit)).all()
        return [
            ExternalLearningResource(
                external_id=row.external_id or row.id,
                provider=row.provider_id,
                title=row.title,
                canonical_url=row.canonical_url,
                metadata={"resource_id": row.id},
            )
            for row in rows
        ]

    def get_resource(self, external_id: str) -> ExternalLearningResource | None:
        row = self.db.get(LearningResource, external_id) or self.db.scalar(select(LearningResource).where(LearningResource.external_id == external_id))
        if not row:
            return None
        return ExternalLearningResource(row.external_id or row.id, row.provider_id, row.title, row.canonical_url, {"resource_id": row.id})

    def check_availability(self, external_id: str) -> ResourceAvailability:
        row = self.db.get(LearningResource, external_id)
        return ResourceAvailability(bool(row and row.active), "curated_catalogue", datetime.utcnow())


class DisabledExternalProviderAdapter:
    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    def search_resources(self, query: LearningResourceQuery) -> list[ExternalLearningResource]:
        return []

    def get_resource(self, external_id: str) -> ExternalLearningResource | None:
        return None

    def check_availability(self, external_id: str) -> ResourceAvailability:
        return ResourceAvailability(False, "external_api_disabled", datetime.utcnow(), "External API access is disabled.")


def safe_resource_url(url: str) -> bool:
    if url.startswith("/"):
        return not url.startswith("//") and "\x00" not in url
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def parse_verified_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def sync_learning_catalogue(db: Session) -> None:
    for provider_name, display_name, provider_type, base_url in PROVIDERS:
        provider = db.get(LearningProvider, provider_name) or LearningProvider(id=provider_name, provider_name=provider_name, display_name=display_name)
        provider.provider_name = provider_name
        provider.display_name = display_name
        provider.provider_type = provider_type
        provider.base_url = base_url
        provider.active = True
        provider.supports_external_search = provider_name in {"youtube", "udemy"}
        provider.api_enabled = False
        provider.metadata_json = {"catalogue_version": LEARNING_CATALOGUE_VERSION}
        db.add(provider)
    db.flush()

    for item in RESOURCE_CATALOGUE:
        row = db.get(LearningResource, item["id"]) or LearningResource(id=item["id"], provider_id=item["provider"], title=item["title"], canonical_url=item["canonical_url"], resource_type=item["resource_type"])
        row.provider_id = item["provider"]
        row.external_id = item.get("external_id")
        row.title = item["title"]
        row.canonical_url = item["canonical_url"]
        row.description = item["description"]
        row.resource_type = item["resource_type"]
        row.level = item["level"]
        row.language = item["language"]
        row.subtitles_json = item["subtitles"]
        row.duration_minutes = item["duration_minutes"]
        row.cost_type = item["cost_type"]
        row.displayed_price = item["displayed_price"]
        row.currency = item["currency"]
        row.instructor_organization = item["instructor_organization"]
        row.rating = item["rating"]
        row.review_count = item["review_count"]
        row.publication_date = item["publication_date"]
        row.last_updated_date = item["last_updated_date"]
        row.last_verified_at = parse_verified_at(item["last_verified_at"])
        row.prerequisites_json = item["prerequisites"]
        row.certificate_available = item["certificate_available"]
        row.practical_exercises = item["practical_exercises"]
        row.project_included = item["project_included"]
        row.quality_status = item["quality_status"] if safe_resource_url(item["canonical_url"]) else "Needs review"
        row.source_provenance = item["source_provenance"]
        row.active = bool(item["active"] and safe_resource_url(item["canonical_url"]))
        row.affiliate = item["affiliate"]
        row.affiliate_disclosure = item["affiliate_disclosure"]
        row.notes_limitations = item["notes_limitations"]
        row.metadata_version = LEARNING_CATALOGUE_VERSION
        row.metadata_json = {"source": "curated_catalogue", "resource_type_label": RESOURCE_TYPE_LABELS.get(item["resource_type"], item["resource_type"])}
        db.add(row)
        db.flush()
        db.execute(delete(LearningResourceSkill).where(LearningResourceSkill.resource_id == row.id))
        db.execute(delete(LearningResourceObjective).where(LearningResourceObjective.resource_id == row.id))
        for skill_id in item["skill_ids"]:
            db.add(LearningResourceSkill(resource_id=row.id, skill_id=skill_id, coverage_level="primary" if skill_id == item["skill_ids"][0] else "supporting", target_level=item["level"], weight=1.0))
        for objective_key in item["objective_keys"]:
            db.add(LearningResourceObjective(resource_id=row.id, objective_key=objective_key, coverage_level="supporting"))
        verification = db.scalar(select(LearningResourceVerification).where(LearningResourceVerification.resource_id == row.id).order_by(LearningResourceVerification.created_at.desc()))
        if not verification:
            db.add(
                LearningResourceVerification(
                    resource_id=row.id,
                    verification_status=row.quality_status,
                    verified_at=row.last_verified_at,
                    verified_by="OrganicAI curated seed",
                    verification_method="manual catalogue entry; no automated scraping",
                    last_availability_check=row.last_verified_at,
                    verification_notes=row.notes_limitations,
                )
            )
        version_exists = db.scalar(select(LearningResourceVersion.id).where(LearningResourceVersion.resource_id == row.id, LearningResourceVersion.metadata_version == LEARNING_CATALOGUE_VERSION).limit(1))
        if not version_exists:
            db.add(LearningResourceVersion(resource_id=row.id, metadata_version=LEARNING_CATALOGUE_VERSION, snapshot_json=item))
    db.flush()


def provider_public(row: LearningProvider) -> dict[str, Any]:
    return {
        "id": row.id,
        "provider_name": row.provider_name,
        "display_name": row.display_name,
        "provider_type": row.provider_type,
        "base_url": row.base_url,
        "active": row.active,
        "supports_external_search": row.supports_external_search,
        "api_enabled": row.api_enabled,
        "metadata": row.metadata_json,
    }


def resource_public(row: LearningResource, skills: list[LearningResourceSkill] | None = None, objectives: list[LearningResourceObjective] | None = None) -> dict[str, Any]:
    return {
        "id": row.id,
        "provider_id": row.provider_id,
        "external_id": row.external_id,
        "title": row.title,
        "canonical_url": row.canonical_url,
        "description": row.description,
        "resource_type": row.resource_type,
        "resource_type_label": RESOURCE_TYPE_LABELS.get(row.resource_type, title_case_slug(row.resource_type)),
        "level": row.level,
        "language": row.language,
        "subtitles": row.subtitles_json or [],
        "duration_minutes": row.duration_minutes,
        "cost_type": row.cost_type,
        "displayed_price": row.displayed_price,
        "currency": row.currency,
        "instructor_organization": row.instructor_organization,
        "rating": row.rating,
        "review_count": row.review_count,
        "publication_date": row.publication_date,
        "last_updated_date": row.last_updated_date,
        "last_verified_at": row.last_verified_at.isoformat() if row.last_verified_at else None,
        "prerequisites": row.prerequisites_json or [],
        "certificate_available": row.certificate_available,
        "practical_exercises": row.practical_exercises,
        "project_included": row.project_included,
        "quality_status": row.quality_status,
        "source_provenance": row.source_provenance,
        "active": row.active,
        "affiliate": row.affiliate,
        "affiliate_disclosure": row.affiliate_disclosure,
        "notes_limitations": row.notes_limitations,
        "metadata_version": row.metadata_version,
        "skills": [{"skill_id": item.skill_id, "coverage_level": item.coverage_level, "target_level": item.target_level, "weight": item.weight} for item in skills or []],
        "objective_keys": [item.objective_key for item in objectives or []],
    }


def preferences_public(row: LearningPreferences) -> dict[str, Any]:
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "preferred_language": row.preferred_language,
        "acceptable_secondary_languages": row.acceptable_secondary_languages_json or [],
        "free_only": row.free_only,
        "max_budget_per_course": row.max_budget_per_course,
        "monthly_learning_budget": row.monthly_learning_budget,
        "available_hours_per_week": row.available_hours_per_week,
        "preferred_content_formats": row.preferred_content_formats_json or [],
        "preferred_session_length_minutes": row.preferred_session_length_minutes,
        "theory_practice_preference": row.theory_practice_preference,
        "certificate_importance": row.certificate_importance,
        "preferred_difficulty": row.preferred_difficulty,
        "target_completion_date": row.target_completion_date,
        "accessibility_preferences": row.accessibility_preferences_json or [],
        "subtitles_required": row.subtitles_required,
        "mobile_friendly": row.mobile_friendly,
        "offline_availability": row.offline_availability,
        "provider_exclusions": row.provider_exclusions_json or [],
        "strict_duration_limit_minutes": row.strict_duration_limit_minutes,
        "metadata": row.metadata_json,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def latest_assessment_session(db: Session, profile_id: str) -> AssessmentSession | None:
    return db.scalar(select(AssessmentSession).where(AssessmentSession.profile_id == profile_id, AssessmentSession.status == "completed").order_by(AssessmentSession.updated_at.desc()))


def ensure_learning_preferences(db: Session, profile: Profile) -> LearningPreferences:
    row = db.scalar(select(LearningPreferences).where(LearningPreferences.profile_id == profile.id).order_by(LearningPreferences.updated_at.desc()))
    if row:
        return row
    session = latest_assessment_session(db, profile.id)
    responses = db.scalars(select(AssessmentResponse).where(AssessmentResponse.session_id == session.id)).all() if session else []
    response_by_item = {item.item_id: item for item in responses}
    language_text = (response_by_item.get("goals_languages").text_value if response_by_item.get("goals_languages") else "") or ""
    preferred_language = "en" if "english" in language_text.lower() or "engleza" in language_text.lower() else "en"
    secondary = ["ro"] if "romanian" in language_text.lower() or "romana" in language_text.lower() else []
    weekly_text = (response_by_item.get("goals_weekly_time").option_value if response_by_item.get("goals_weekly_time") else "") or ""
    available_hours = {"0-2 hours": 2, "3-5 hours": 4, "6-10 hours": 8, "10+ hours": 12}.get(weekly_text, 6)
    budget_text = (response_by_item.get("goals_budget").option_value if response_by_item.get("goals_budget") else "") or ""
    format_text = (response_by_item.get("goals_learning_format").option_value if response_by_item.get("goals_learning_format") else "") or ""
    row = LearningPreferences(
        profile_id=profile.id,
        user_id=profile.user_id,
        preferred_language=preferred_language,
        acceptable_secondary_languages_json=secondary,
        free_only=budget_text == "none",
        max_budget_per_course=0 if budget_text == "none" else 50 if budget_text == "low" else 150 if budget_text == "moderate" else None,
        monthly_learning_budget=0 if budget_text == "none" else 50 if budget_text == "low" else 150 if budget_text == "moderate" else None,
        available_hours_per_week=float(available_hours),
        preferred_content_formats_json=["Project-based", "Text", "Video"] if format_text == "project-based" else ["Mixed"],
        preferred_session_length_minutes=60,
        theory_practice_preference="practical" if format_text == "project-based" else "mixed",
        certificate_importance="medium",
        preferred_difficulty="adaptive",
        provider_exclusions_json=[],
        metadata_json={"source": "assessment_defaults" if session else "system_default"},
    )
    db.add(row)
    db.flush()
    return row


def update_learning_preferences(db: Session, profile: Profile, payload: dict[str, Any]) -> LearningPreferences:
    row = ensure_learning_preferences(db, profile)
    field_map = {
        "preferred_language": "preferred_language",
        "acceptable_secondary_languages": "acceptable_secondary_languages_json",
        "free_only": "free_only",
        "max_budget_per_course": "max_budget_per_course",
        "monthly_learning_budget": "monthly_learning_budget",
        "available_hours_per_week": "available_hours_per_week",
        "preferred_content_formats": "preferred_content_formats_json",
        "preferred_session_length_minutes": "preferred_session_length_minutes",
        "theory_practice_preference": "theory_practice_preference",
        "certificate_importance": "certificate_importance",
        "preferred_difficulty": "preferred_difficulty",
        "target_completion_date": "target_completion_date",
        "accessibility_preferences": "accessibility_preferences_json",
        "subtitles_required": "subtitles_required",
        "mobile_friendly": "mobile_friendly",
        "offline_availability": "offline_availability",
        "provider_exclusions": "provider_exclusions_json",
        "strict_duration_limit_minutes": "strict_duration_limit_minutes",
    }
    for key, attr in field_map.items():
        if key in payload and payload[key] is not None:
            setattr(row, attr, payload[key])
    row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return row


def selected_career_match(db: Session, profile_id: str, career_match_id: str | None = None) -> CareerMatch | None:
    if career_match_id:
        return db.scalar(select(CareerMatch).where(CareerMatch.id == career_match_id, CareerMatch.profile_id == profile_id, CareerMatch.status != "rejected"))
    return db.scalar(
        select(CareerMatch)
        .where(CareerMatch.profile_id == profile_id, CareerMatch.status.in_(["saved", "roadmap_draft_created", "learning_selected"]))
        .order_by(CareerMatch.updated_at.desc())
    )


def skill_label(skill_id: str) -> str:
    return title_case_slug(skill_id).replace("Ui", "UI")


def skill_inventory(db: Session, profile_id: str, session_id: str | None = None) -> dict[str, SkillsInventory]:
    statement = select(SkillsInventory).where(SkillsInventory.profile_id == profile_id)
    if session_id:
        statement = statement.where(SkillsInventory.session_id == session_id)
    rows = db.scalars(statement.order_by(SkillsInventory.updated_at.desc())).all()
    out: dict[str, SkillsInventory] = {}
    for row in rows:
        out.setdefault(row.skill_id, row)
    return out


def target_level_for_skill(match: CareerMatch, role: CareerRoleTemplate | None, skill_id: str, index: int) -> int:
    if skill_id in {"evaluation", "prompt_design", "rag_fundamentals"}:
        return 3
    if skill_id in {"software_development", "apis", "databases", "ux_ui", "ai_tools", "automation", "planning"}:
        return 3 if index <= 2 or match.role_family in {"Software and AI Engineering", "Product Strategy"} else 2
    if skill_id in {"communication", "research", "visual_communication", "critical_thinking", "systems_thinking"}:
        return 3 if index <= 1 else 2
    return 2


def gap_status(current_level: int, target_level: int, missing_prerequisites: list[str], evidence_status: str) -> str:
    if missing_prerequisites:
        return "Missing prerequisite"
    if current_level >= target_level and EVIDENCE_STRENGTH.get(evidence_status, 1) <= 1:
        return "Evidence required"
    gap = max(0, target_level - current_level)
    if gap == 0:
        return "No gap"
    if gap == 1:
        return "Small gap"
    if gap == 2:
        return "Moderate gap"
    return "Significant gap"


def priority_label(score: float, status: str) -> str:
    if status == "No gap":
        return "Optional"
    if score >= 8:
        return "Essential"
    if score >= 5:
        return "High priority"
    if score >= 2:
        return "Recommended"
    if score >= 1:
        return "Supplementary"
    return "Optional"


def transition_urgency(match: CareerMatch) -> float:
    return {"1-4 weeks": 1.25, "1-3 months": 1.15, "3-6 months": 1.0, "6-12+ months": 0.85}.get(match.time_horizon, 1.0)


def objective_descriptions(skill_id: str) -> list[str]:
    templates = {
        "ai_tools": [
            "Explain common limitations of generative AI, including hallucinations and unsupported claims.",
            "Apply privacy-aware AI usage in a realistic professional workflow.",
            "Compare AI-assisted and human-only outputs using transparent criteria.",
        ],
        "evaluation": [
            "Define evaluation criteria before testing an AI or digital product output.",
            "Identify unsupported claims, bias risks, and missing source evidence.",
            "Document human oversight decisions and improvement actions.",
        ],
        "ux_ui": [
            "Map user goals, states, and interaction flows for the selected role context.",
            "Design accessible interface states for success, uncertainty, error, and recovery.",
            "Test a prototype with at least one realistic user task.",
        ],
        "research": [
            "Create a focused research question and interview or observation plan.",
            "Compare evidence from users, documentation, and role requirements.",
            "Summarise insights into decisions and open uncertainties.",
        ],
        "software_development": [
            "Implement a small, version-controlled feature with readable structure.",
            "Connect frontend, backend, or data components through a clear interface.",
            "Document setup, tradeoffs, and known limitations.",
        ],
        "apis": [
            "Explain request, response, authentication, and error-handling basics.",
            "Build a small API integration with validation and graceful failure states.",
            "Document API assumptions, privacy constraints, and test cases.",
        ],
        "databases": [
            "Model simple relational data with searchable fields and clear identifiers.",
            "Write basic queries to create, read, update, and filter records.",
            "Explain how schema choices affect evidence, traceability, and privacy.",
        ],
        "data_analysis": [
            "Clean a small dataset and document assumptions.",
            "Create a concise analysis with charts or tables that answer a question.",
            "Explain uncertainty, limitations, and what would need verification.",
        ],
        "automation": [
            "Map a repetitive workflow before deciding what to automate.",
            "Build a low-risk automation with manual review and rollback.",
            "Measure effort saved, errors introduced, and human oversight points.",
        ],
        "planning": [
            "Break a role transition into milestones, weekly commitments, and evidence.",
            "Identify dependencies, blockers, and decision checkpoints.",
            "Adjust a plan using feedback without silently changing core goals.",
        ],
        "communication": [
            "Explain a technical or AI-assisted recommendation to a non-specialist.",
            "Adapt communication for stakeholder concerns, risks, and evidence needs.",
            "Ask for feedback and record what changed as a result.",
        ],
    }
    return templates.get(
        skill_id,
        [
            f"Explain the core concepts behind {skill_label(skill_id)} in the selected career context.",
            f"Complete a small practical exercise that demonstrates {skill_label(skill_id)}.",
            f"Document evidence, limitations, and next steps for improving {skill_label(skill_id)}.",
        ],
    )


def create_skill_gap_analysis(db: Session, profile: Profile, career_match_id: str | None = None) -> dict[str, Any]:
    sync_learning_catalogue(db)
    match = selected_career_match(db, profile.id, career_match_id)
    if not match:
        return {"status": "no_career_selected", "message": NO_CAREER_SELECTED_MESSAGE}
    role = db.get(CareerRoleTemplate, match.role_template_id) if match.role_template_id else None
    required_skills = list(role.required_skills_json if role else [item.lower().replace(" ", "_") for item in match.missing_skills_json or []])
    category_skill_map = {
        "AI evaluation": ["evaluation"],
        "production product process": ["planning", "quality_assurance"],
        "systematic UX methods": ["research", "ux_ui"],
        "AI-specific risk patterns": ["evaluation", "critical_thinking"],
        "production deployment": ["software_development", "apis"],
        "AI rights and evaluation": ["evaluation", "critical_thinking"],
        "business process evidence": ["systems_thinking", "planning"],
        "change management": ["communication", "planning"],
        "learning assessment design": ["teaching", "evaluation"],
        "content evaluation": ["evaluation", "writing"],
        "product analytics": ["data_analysis", "evaluation"],
        "backend deployment": ["software_development", "apis"],
        "systematic evaluation": ["evaluation"],
        "statistics": ["data_analysis"],
        "SQL/Python evidence": ["databases", "software_development"],
        "testing": ["quality_assurance"],
        "deployment": ["software_development"],
        "performance": ["quality_assurance"],
        "interactive prototyping": ["ux_ui", "software_development"],
        "accessibility": ["ux_ui", "quality_assurance"],
        "integration testing": ["quality_assurance", "apis"],
        "security basics": ["quality_assurance"],
        "technical delivery vocabulary": ["planning", "communication"],
        "risk management": ["planning", "critical_thinking"],
        "pricing": ["budgeting"],
        "client acquisition": ["client_relations", "communication"],
        "scope boundaries": ["planning", "communication"],
    }
    if role:
        for category in role.skill_gap_categories_json or []:
            for skill_id in category_skill_map.get(category, []):
                if skill_id not in required_skills:
                    required_skills.append(skill_id)
    if not required_skills:
        required_skills = ["ai_tools", "research", "communication", "planning"]
    session = latest_assessment_session(db, profile.id)
    current_skills = skill_inventory(db, profile.id, session.id if session else None)
    preferences = ensure_learning_preferences(db, profile)

    analysis = SkillGapAnalysis(
        profile_id=profile.id,
        user_id=profile.user_id,
        career_match_id=match.id,
        role_template_id=match.role_template_id,
        analysis_version=SKILL_GAP_VERSION,
        status="ready",
        summary=f"Skill-gap analysis for {match.title}. Self-reported skills are not treated as verified evidence.",
        context_json={
            "career_title": match.title,
            "role_family": match.role_family,
            "assessment_session_id": session.id if session else None,
            "preferences_id": preferences.id,
            "methodology": "Deterministic comparison of current skill levels with curated role requirements.",
        },
        demo_marker=match.demo_marker,
    )
    db.add(analysis)
    db.flush()

    gap_items: list[SkillGapItem] = []
    for index, skill_id in enumerate(required_skills):
        inventory = current_skills.get(skill_id)
        current_level = int(inventory.level) if inventory else 0
        evidence_status = inventory.evidence_status if inventory else "self_reported"
        target_level = target_level_for_skill(match, role, skill_id, index)
        prerequisites = PREREQUISITES.get(skill_id, [])
        missing_prerequisites = [item for item in prerequisites if (current_skills.get(item).level if current_skills.get(item) else 0) < 1]
        status = gap_status(current_level, target_level, missing_prerequisites, evidence_status)
        gap_size = max(0, target_level - current_level)
        importance = max(1.0, 5.0 - (index * 0.45))
        dependency_weight = 1.25 if missing_prerequisites else 1.0
        evidence_adjustment = 1.15 if EVIDENCE_STRENGTH.get(evidence_status, 1) <= 1 or status == "Evidence required" else 1.0
        base_gap = gap_size if gap_size else 0.7 if status == "Evidence required" else 0.35
        priority_score = round(importance * base_gap * dependency_weight * transition_urgency(match) * evidence_adjustment, 2)
        label = priority_label(priority_score, status)
        row = SkillGapItem(
            analysis_id=analysis.id,
            profile_id=profile.id,
            career_match_id=match.id,
            skill_id=skill_id,
            skill_label=skill_label(skill_id),
            current_level=current_level,
            target_level=target_level,
            gap_size=gap_size,
            importance=round(importance, 2),
            evidence_level=evidence_status,
            required=True,
            ai_augmentable=skill_id in AI_AUGMENTABLE_SKILLS,
            prerequisite_skill_ids_json=prerequisites,
            missing_prerequisites_json=missing_prerequisites,
            status=status,
            priority_label=label,
            priority_score_internal=priority_score,
            dependency_order=index,
            explanation=f"{skill_label(skill_id)} is required for {match.title}; current level is {SKILL_LEVEL_LABELS.get(current_level, 'No experience')} and target level is {SKILL_LEVEL_LABELS.get(target_level, 'Intermediate')}.",
        )
        db.add(row)
        db.flush()
        gap_items.append(row)
        if status != "No gap" or label != "Optional":
            for objective_index, description in enumerate(objective_descriptions(skill_id), start=1):
                db.add(
                    LearningObjective(
                        analysis_id=analysis.id,
                        gap_item_id=row.id,
                        profile_id=profile.id,
                        career_match_id=match.id,
                        objective_key=f"{skill_id}_{objective_index}",
                        skill_id=skill_id,
                        target_level=target_level,
                        description=description,
                        prerequisite_ids_json=missing_prerequisites,
                        estimated_effort_minutes=max(60, gap_size * 120 + objective_index * 30),
                        evidence_expected="Short summary plus practical evidence; course completion alone records exposure, not advanced competence.",
                        role_relevance=f"Supports {match.title} requirement: {skill_label(skill_id)}.",
                        priority=label,
                        objective_version=LEARNING_OBJECTIVE_VERSION,
                    )
                )

    important = sorted([item for item in gap_items if item.priority_label in {"Essential", "High priority", "Recommended"}], key=lambda item: item.priority_score_internal, reverse=True)
    if important:
        ensure_practical_project(db, profile, match, important[0])
    db.commit()
    return skill_gap_analysis_public(db, analysis.id)


def ensure_practical_project(db: Session, profile: Profile, match: CareerMatch, gap: SkillGapItem) -> PracticalProject:
    existing = db.scalar(select(PracticalProject).where(PracticalProject.profile_id == profile.id, PracticalProject.career_match_id == match.id).limit(1))
    if existing:
        return existing
    role_key = (match.role_template_id or match.title.lower().replace(" ", "_"))
    templates = {
        "human_centred_ai_product_designer": ("Create an explainable AI recommendation interface", ["Prototype screens", "Confidence/source states", "Usability notes"]),
        "rag_application_developer": ("Build a small RAG service with source attribution", ["Working endpoint", "Source display", "Supported/unsupported question log"]),
        "ai_integration_consultant": ("Map and redesign one AI-assisted organisational workflow", ["Current workflow map", "AI-assisted workflow", "Risk and oversight note"]),
        "frontend_developer": ("Build an accessible React application with API integration", ["Responsive UI", "Keyboard checks", "API error states"]),
    }
    title, deliverables = templates.get(role_key, (f"Build a portfolio experiment for {match.title}", ["Problem statement", "Small prototype", "Reflection and next decision"]))
    row = PracticalProject(
        profile_id=profile.id,
        user_id=profile.user_id,
        career_match_id=match.id,
        skill_gap_item_id=gap.id,
        title=title,
        description=f"A practical evidence project connected to {match.title}.",
        skills_demonstrated_json=[gap.skill_id, "communication", "evaluation"],
        estimated_effort_minutes=480,
        suggested_deliverables_json=deliverables,
        completion_criteria_json=["A reviewer can understand the problem, process, outcome, and limitations.", "Evidence is stored in a portfolio, GitHub repository, or written reflection."],
        portfolio_value="Creates evidence beyond course completion.",
        prerequisites_json=gap.prerequisite_skill_ids_json,
        demo_marker=match.demo_marker,
    )
    db.add(row)
    return row


def skill_gap_item_public(row: SkillGapItem) -> dict[str, Any]:
    return {
        "id": row.id,
        "analysis_id": row.analysis_id,
        "skill_id": row.skill_id,
        "skill_label": row.skill_label,
        "current_level": row.current_level,
        "current_level_label": SKILL_LEVEL_LABELS.get(row.current_level, "No experience"),
        "target_level": row.target_level,
        "target_level_label": SKILL_LEVEL_LABELS.get(row.target_level, "Intermediate"),
        "gap_size": row.gap_size,
        "importance": row.importance,
        "evidence_level": row.evidence_level,
        "required": row.required,
        "ai_augmentable": row.ai_augmentable,
        "prerequisite_skill_ids": row.prerequisite_skill_ids_json or [],
        "missing_prerequisites": row.missing_prerequisites_json or [],
        "status": row.status,
        "priority_label": row.priority_label,
        "priority_score_internal": row.priority_score_internal,
        "dependency_order": row.dependency_order,
        "explanation": row.explanation,
    }


def objective_public(row: LearningObjective) -> dict[str, Any]:
    return {
        "id": row.id,
        "analysis_id": row.analysis_id,
        "gap_item_id": row.gap_item_id,
        "objective_key": row.objective_key,
        "skill_id": row.skill_id,
        "target_level": row.target_level,
        "target_level_label": SKILL_LEVEL_LABELS.get(row.target_level, "Intermediate"),
        "description": row.description,
        "prerequisite_ids": row.prerequisite_ids_json or [],
        "estimated_effort_minutes": row.estimated_effort_minutes,
        "evidence_expected": row.evidence_expected,
        "role_relevance": row.role_relevance,
        "priority": row.priority,
        "objective_version": row.objective_version,
        "status": row.status,
    }


def practical_project_public(row: PracticalProject) -> dict[str, Any]:
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "career_match_id": row.career_match_id,
        "skill_gap_item_id": row.skill_gap_item_id,
        "title": row.title,
        "description": row.description,
        "skills_demonstrated": row.skills_demonstrated_json or [],
        "estimated_effort_minutes": row.estimated_effort_minutes,
        "suggested_deliverables": row.suggested_deliverables_json or [],
        "completion_criteria": row.completion_criteria_json or [],
        "portfolio_value": row.portfolio_value,
        "prerequisites": row.prerequisites_json or [],
        "status": row.status,
    }


def skill_gap_analysis_public(db: Session, analysis_id: str) -> dict[str, Any]:
    analysis = db.get(SkillGapAnalysis, analysis_id)
    if not analysis:
        return {"status": "not_found"}
    items = db.scalars(select(SkillGapItem).where(SkillGapItem.analysis_id == analysis.id).order_by(SkillGapItem.priority_score_internal.desc())).all()
    objectives = db.scalars(select(LearningObjective).where(LearningObjective.analysis_id == analysis.id).order_by(LearningObjective.skill_id, LearningObjective.created_at)).all()
    projects = db.scalars(select(PracticalProject).where(PracticalProject.profile_id == analysis.profile_id, PracticalProject.career_match_id == analysis.career_match_id)).all()
    return {
        "id": analysis.id,
        "profile_id": analysis.profile_id,
        "career_match_id": analysis.career_match_id,
        "role_template_id": analysis.role_template_id,
        "analysis_version": analysis.analysis_version,
        "status": analysis.status,
        "summary": analysis.summary,
        "hard_filters": analysis.hard_filters_json or [],
        "context": analysis.context_json or {},
        "items": [skill_gap_item_public(item) for item in items],
        "objectives": [objective_public(item) for item in objectives],
        "practical_projects": [practical_project_public(item) for item in projects],
        "created_at": analysis.created_at.isoformat(),
        "updated_at": analysis.updated_at.isoformat(),
    }


def latest_gap_analysis(db: Session, profile_id: str, career_match_id: str | None = None) -> dict[str, Any]:
    statement = select(SkillGapAnalysis).where(SkillGapAnalysis.profile_id == profile_id)
    if career_match_id:
        statement = statement.where(SkillGapAnalysis.career_match_id == career_match_id)
    row = db.scalar(statement.order_by(SkillGapAnalysis.created_at.desc()))
    if not row:
        return {"status": "not_started"}
    return skill_gap_analysis_public(db, row.id)


def feedback_adjustments(db: Session, profile_id: str) -> dict[str, Any]:
    rows = db.scalars(select(LearningResourceFeedback).where(LearningResourceFeedback.profile_id == profile_id).order_by(LearningResourceFeedback.created_at.desc())).all()
    out = {"prefer_free": False, "prefer_practical": False, "min_level_offset": 0, "excluded_languages": set(), "excluded_resource_ids": set(), "completed_resource_ids": set()}
    for row in rows:
        code = row.reason_code or ""
        if code == "too_expensive":
            out["prefer_free"] = True
        if code == "too_theoretical":
            out["prefer_practical"] = True
        if code == "too_basic":
            out["min_level_offset"] = max(out["min_level_offset"], 1)
        if code == "wrong_language" and row.effect_json.get("language"):
            out["excluded_languages"].add(row.effect_json["language"])
        if code in {"not_relevant", "rejected", "wrong_language"} and row.learning_resource_id:
            out["excluded_resource_ids"].add(row.learning_resource_id)
        if code == "already_completed" and row.learning_resource_id:
            out["completed_resource_ids"].add(row.learning_resource_id)
    out["excluded_languages"] = list(out["excluded_languages"])
    out["excluded_resource_ids"] = list(out["excluded_resource_ids"])
    out["completed_resource_ids"] = list(out["completed_resource_ids"])
    return out


def hard_filter_resource(
    resource: LearningResource,
    resource_skill_ids: set[str],
    gap: SkillGapItem,
    preferences: LearningPreferences,
    current_skills: dict[str, SkillsInventory],
    adjustments: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []
    if not resource.active:
        reasons.append("resource is inactive")
    if not safe_resource_url(resource.canonical_url):
        reasons.append("unsafe or invalid URL")
    acceptable_languages = {preferences.preferred_language, *(preferences.acceptable_secondary_languages_json or [])}
    if resource.language not in acceptable_languages:
        reasons.append("language is not acceptable")
    if resource.language in adjustments.get("excluded_languages", []):
        reasons.append("language was rejected in feedback")
    if preferences.free_only and resource.cost_type not in {"free", "open"}:
        reasons.append("free-only preference excludes paid or audit-priced resources")
    if preferences.max_budget_per_course is not None and resource.cost_type == "paid" and resource.displayed_price is None:
        reasons.append("price is not verified against strict budget")
    if preferences.max_budget_per_course is not None and resource.displayed_price is not None and resource.displayed_price > preferences.max_budget_per_course:
        reasons.append("price exceeds strict maximum")
    provider_exclusions = set(preferences.provider_exclusions_json or [])
    if resource.provider_id in provider_exclusions:
        reasons.append("provider is excluded")
    if preferences.strict_duration_limit_minutes and resource.duration_minutes and resource.duration_minutes > preferences.strict_duration_limit_minutes:
        reasons.append("duration exceeds strict limit")
    if preferences.subtitles_required and resource.resource_type.startswith("youtube") and preferences.preferred_language not in (resource.subtitles_json or []):
        reasons.append("required subtitles are not verified")
    if gap.skill_id not in resource_skill_ids:
        reasons.append("content does not cover the required skill")
    if resource.id in adjustments.get("excluded_resource_ids", []):
        reasons.append("resource was rejected by the user")
    if resource.id in adjustments.get("completed_resource_ids", []):
        reasons.append("resource already completed")
    for prerequisite in resource.prerequisites_json or []:
        if LEVEL_VALUES.get(resource.level, 1) >= 2 and (current_skills.get(prerequisite).level if current_skills.get(prerequisite) else 0) < 1:
            reasons.append(f"prerequisite missing: {skill_label(prerequisite)}")
    return reasons


def score_alignment(
    resource: LearningResource,
    resource_skill_ids: set[str],
    resource_objective_keys: set[str],
    gap: SkillGapItem,
    objective: LearningObjective | None,
    preferences: LearningPreferences,
    adjustments: dict[str, Any],
) -> dict[str, tuple[float, str]]:
    direct_skill = gap.skill_id in resource_skill_ids
    skill_relevance = 100 if direct_skill else 45
    resource_level = LEVEL_VALUES.get(resource.level, 2)
    target_distance = abs(resource_level - max(1, min(gap.target_level, 4)))
    if adjustments.get("min_level_offset") and resource_level < max(1, gap.current_level + adjustments["min_level_offset"]):
        level_score = 35
    else:
        level_score = max(20, 100 - target_distance * 22)
    objective_score = 90 if objective and (objective.objective_key in resource_objective_keys or objective.skill_id in resource_objective_keys or objective.skill_id in resource_skill_ids) else 65 if direct_skill else 35
    quality_base = {"Verified": 92, "Partially verified": 72, "Community submitted": 55, "Needs review": 35, "Unavailable": 0, "Archived": 0}.get(resource.quality_status, 55)
    if resource.provider_id in {"official_documentation", "microsoft_learn", "google_learning"}:
        quality_base = min(100, quality_base + 6)
    language_score = 100 if resource.language == preferences.preferred_language else 78
    weekly_minutes = max(60, int((preferences.available_hours_per_week or 6) * 60))
    if not resource.duration_minutes:
        time_score = 70
    elif resource.duration_minutes <= weekly_minutes:
        time_score = 100
    elif resource.duration_minutes <= weekly_minutes * 4:
        time_score = 78
    else:
        time_score = 52
    if resource.cost_type in {"free", "open"}:
        budget_score = 100
    elif adjustments.get("prefer_free"):
        budget_score = 35
    elif resource.cost_type == "paid_or_audit":
        budget_score = 72
    else:
        budget_score = 58
    practical = 100 if resource.project_included or resource.resource_type in {"practical_project", "portfolio_project"} else 82 if resource.practical_exercises else 45
    if adjustments.get("prefer_practical") and practical < 80:
        practical = max(20, practical - 25)
    if resource.last_verified_at:
        age_days = (datetime.utcnow() - resource.last_verified_at).days
        freshness = 100 if age_days <= 180 else 85 if age_days <= 365 else 60 if age_days <= 730 else 45
    else:
        freshness = 45
    format_map = {
        "youtube_video": "Video",
        "youtube_playlist": "Video",
        "official_documentation": "Text",
        "internal_article": "Text",
        "interactive_tutorial": "Interactive",
        "practical_project": "Project-based",
        "portfolio_project": "Project-based",
        "online_course": "Mixed",
        "certification_preparation": "Mixed",
        "workshop": "Instructor-led",
    }
    preferred_formats = set(preferences.preferred_content_formats_json or ["Mixed"])
    resource_format = format_map.get(resource.resource_type, "Mixed")
    format_score = 100 if resource_format in preferred_formats or "Mixed" in preferred_formats else 68
    return {
        "skill_gap_relevance": (skill_relevance, f"Covers {gap.skill_label}." if direct_skill else "Only indirectly related to the skill gap."),
        "level_compatibility": (level_score, f"Resource level is {resource.level}; target level is {SKILL_LEVEL_LABELS.get(gap.target_level, 'Intermediate')}."),
        "objective_coverage": (objective_score, "Covers the selected learning objective or its parent skill."),
        "source_quality": (quality_base, f"Quality status: {resource.quality_status}; provider: {resource.provider_id}."),
        "language_fit": (language_score, f"Language: {resource.language}; preferred language: {preferences.preferred_language}."),
        "time_fit": (time_score, "Estimated duration is compared with available weekly time."),
        "budget_fit": (budget_score, f"Cost type: {resource.cost_type}; prices may change on provider pages."),
        "practical_evidence_value": (practical, "Project or exercise value is considered separately from course popularity."),
        "freshness": (freshness, "Uses last verification date, not assumed real-time provider metadata."),
        "format_preference": (format_score, f"Resource format is {resource_format}."),
    }


def alignment_label(score: float) -> str:
    if score >= 78:
        return "Strong learning alignment"
    if score >= 62:
        return "Good learning alignment"
    if score >= 45:
        return "Supplementary resource"
    if score >= 30:
        return "Alternative option"
    return "Not recommended at the current stage"


def deterministic_explanation(resource: LearningResource, gap: SkillGapItem, objective: LearningObjective | None, label: str) -> str:
    objective_text = objective.description if objective else f"Improve {gap.skill_label}."
    return (
        f"{label}: {resource.title} is recommended because it addresses {gap.skill_label} for the selected career direction. "
        f"Primary objective: {objective_text} Resource metadata comes from the stored catalogue, not generated text."
    )


def generate_learning_recommendations(db: Session, profile: Profile, career_match_id: str | None = None) -> dict[str, Any]:
    sync_learning_catalogue(db)
    match = selected_career_match(db, profile.id, career_match_id)
    if not match:
        return {"status": "no_career_selected", "message": NO_CAREER_SELECTED_MESSAGE, "recommendations": []}
    preferences = ensure_learning_preferences(db, profile)
    analysis_payload = latest_gap_analysis(db, profile.id, match.id)
    if analysis_payload.get("status") == "not_started":
        analysis_payload = create_skill_gap_analysis(db, profile, match.id)
    analysis = db.get(SkillGapAnalysis, analysis_payload["id"])
    gap_rows = db.scalars(select(SkillGapItem).where(SkillGapItem.analysis_id == analysis.id).order_by(SkillGapItem.priority_score_internal.desc())).all()
    objective_rows = db.scalars(select(LearningObjective).where(LearningObjective.analysis_id == analysis.id)).all()
    objectives_by_gap: dict[str, list[LearningObjective]] = defaultdict(list)
    for objective in objective_rows:
        objectives_by_gap[objective.gap_item_id].append(objective)
    current_skills = skill_inventory(db, profile.id)
    adjustments = feedback_adjustments(db, profile.id)
    resources = db.scalars(select(LearningResource).where(LearningResource.active.is_(True))).all()
    skill_links = db.scalars(select(LearningResourceSkill)).all()
    objective_links = db.scalars(select(LearningResourceObjective)).all()
    skills_by_resource: dict[str, set[str]] = defaultdict(set)
    objectives_by_resource: dict[str, set[str]] = defaultdict(set)
    for link in skill_links:
        skills_by_resource[link.resource_id].add(link.skill_id)
    for link in objective_links:
        objectives_by_resource[link.resource_id].add(link.objective_key)

    provider_status = [{"provider": "internal", "status": "available", "source": "curated catalogue"}]
    settings = get_settings()
    if not settings.learning_resource_external_search_enabled:
        provider_status.append({"provider": "external_search", "status": "disabled", "message": "Curated catalogue remains available."})
    filters: list[dict[str, Any]] = []
    run = LearningRecommendationRun(
        profile_id=profile.id,
        user_id=profile.user_id,
        career_match_id=match.id,
        skill_gap_analysis_id=analysis.id,
        preferences_id=preferences.id,
        recommendation_version=LEARNING_RECOMMENDATION_VERSION,
        status="ready",
        provider_status_json=provider_status,
        ranking_weights_json=RESOURCE_ALIGNMENT_WEIGHTS,
        demo_marker=match.demo_marker,
    )
    db.add(run)
    db.flush()

    created: list[LearningRecommendation] = []
    rank = 1
    important_gaps = [gap for gap in gap_rows if gap.status != "No gap" and gap.priority_label != "Optional"] or gap_rows[:3]
    for gap in important_gaps[:6]:
        scored: list[tuple[float, LearningResource, LearningObjective | None, dict[str, tuple[float, str]]]] = []
        objective = (objectives_by_gap.get(gap.id) or [None])[0]
        for resource in resources:
            reasons = hard_filter_resource(resource, skills_by_resource.get(resource.id, set()), gap, preferences, current_skills, adjustments)
            if reasons:
                filters.append({"resource_id": resource.id, "skill_gap_id": gap.id, "reasons": reasons})
                continue
            factors = score_alignment(resource, skills_by_resource.get(resource.id, set()), objectives_by_resource.get(resource.id, set()), gap, objective, preferences, adjustments)
            score = round(sum(value * RESOURCE_ALIGNMENT_WEIGHTS[key] for key, (value, _) in factors.items()), 2)
            scored.append((score, resource, objective, factors))
        selected: list[tuple[float, LearningResource, LearningObjective | None, dict[str, tuple[float, str]]]] = []
        sorted_candidates = sorted(scored, key=lambda item: item[0], reverse=True)
        bundle_checks = [
            lambda resource: resource.resource_type in {"online_course", "certification_preparation", "internal_guided_module", "interactive_tutorial"},
            lambda resource: resource.cost_type in {"free", "open"} and resource.provider_id != "internal",
            lambda resource: resource.provider_id in {"official_documentation", "microsoft_learn", "google_learning"} or resource.resource_type == "official_documentation",
            lambda resource: resource.resource_type in {"practical_project", "portfolio_project"},
        ]
        used_ids: set[str] = set()
        for check in bundle_checks:
            for candidate in sorted_candidates:
                if candidate[1].id not in used_ids and check(candidate[1]):
                    selected.append(candidate)
                    used_ids.add(candidate[1].id)
                    break
        for candidate in sorted_candidates:
            if len(selected) >= 6:
                break
            if candidate[1].id not in used_ids:
                selected.append(candidate)
                used_ids.add(candidate[1].id)
        for score, resource, objective, factors in selected:
            label = alignment_label(score)
            recommendation = LearningRecommendation(
                run_id=run.id,
                profile_id=profile.id,
                user_id=profile.user_id,
                career_match_id=match.id,
                skill_gap_item_id=gap.id,
                learning_objective_id=objective.id if objective else None,
                learning_resource_id=resource.id,
                alignment_label=label,
                ranking_score_internal=score,
                rank_position=rank,
                status="suggested",
                explanation=deterministic_explanation(resource, gap, objective, label),
                limitations_json=[
                    "Resource metadata is curated and may become stale.",
                    "Course completion alone does not prove advanced skill.",
                    "No employment outcome is guaranteed.",
                ],
                recommendation_version=LEARNING_RECOMMENDATION_VERSION,
                demo_marker=match.demo_marker,
            )
            db.add(recommendation)
            db.flush()
            for key, (value, explanation) in factors.items():
                db.add(LearningRecommendationFactor(recommendation_id=recommendation.id, factor_type=key, factor_value=value, weight=RESOURCE_ALIGNMENT_WEIGHTS[key], explanation=explanation))
            created.append(recommendation)
            rank += 1
    run.filters_json = filters[:250]
    if not created:
        run.status = "no_matching_resources"
    match.status = "learning_selected" if match.status == "suggested" else match.status
    db.commit()
    return recommendation_run_public(db, run.id)


def factor_public(row: LearningRecommendationFactor) -> dict[str, Any]:
    return {
        "id": row.id,
        "factor_type": row.factor_type,
        "factor_value": row.factor_value,
        "weight": row.weight,
        "explanation": row.explanation,
    }


def recommendation_public(
    row: LearningRecommendation,
    resource: LearningResource,
    factors: list[LearningRecommendationFactor],
    gap: SkillGapItem | None,
    objective: LearningObjective | None,
) -> dict[str, Any]:
    return {
        "id": row.id,
        "run_id": row.run_id,
        "profile_id": row.profile_id,
        "career_match_id": row.career_match_id,
        "skill_gap_item_id": row.skill_gap_item_id,
        "learning_objective_id": row.learning_objective_id,
        "learning_resource_id": row.learning_resource_id,
        "alignment_label": row.alignment_label,
        "ranking_score_internal": row.ranking_score_internal,
        "rank_position": row.rank_position,
        "status": row.status,
        "explanation": row.explanation,
        "limitations": row.limitations_json or [],
        "recommendation_version": row.recommendation_version,
        "resource": resource_public(resource),
        "skill_gap": skill_gap_item_public(gap) if gap else None,
        "objective": objective_public(objective) if objective else None,
        "factors": [factor_public(item) for item in factors],
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def recommendation_run_public(db: Session, run_id: str) -> dict[str, Any]:
    run = db.get(LearningRecommendationRun, run_id)
    if not run:
        return {"status": "not_found"}
    rows = db.scalars(select(LearningRecommendation).where(LearningRecommendation.run_id == run.id).order_by(LearningRecommendation.rank_position)).all()
    resources = {row.id: row for row in db.scalars(select(LearningResource).where(LearningResource.id.in_([item.learning_resource_id for item in rows]))).all()} if rows else {}
    gap_ids = [item.skill_gap_item_id for item in rows if item.skill_gap_item_id]
    objective_ids = [item.learning_objective_id for item in rows if item.learning_objective_id]
    gaps = {row.id: row for row in db.scalars(select(SkillGapItem).where(SkillGapItem.id.in_(gap_ids))).all()} if gap_ids else {}
    objectives = {row.id: row for row in db.scalars(select(LearningObjective).where(LearningObjective.id.in_(objective_ids))).all()} if objective_ids else {}
    factors = db.scalars(select(LearningRecommendationFactor).where(LearningRecommendationFactor.recommendation_id.in_([row.id for row in rows]))).all() if rows else []
    factors_by_rec: dict[str, list[LearningRecommendationFactor]] = defaultdict(list)
    for factor in factors:
        factors_by_rec[factor.recommendation_id].append(factor)
    recommendations = [recommendation_public(row, resources[row.learning_resource_id], factors_by_rec[row.id], gaps.get(row.skill_gap_item_id), objectives.get(row.learning_objective_id)) for row in rows]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in recommendations:
        gap_label = item["skill_gap"]["skill_label"] if item.get("skill_gap") else "General"
        grouped[gap_label].append(item)
    return {
        "id": run.id,
        "profile_id": run.profile_id,
        "career_match_id": run.career_match_id,
        "skill_gap_analysis_id": run.skill_gap_analysis_id,
        "preferences_id": run.preferences_id,
        "recommendation_version": run.recommendation_version,
        "status": run.status,
        "provider_status": run.provider_status_json or [],
        "hard_filters": run.filters_json or [],
        "ranking_weights": run.ranking_weights_json or RESOURCE_ALIGNMENT_WEIGHTS,
        "recommendations": recommendations,
        "grouped_by_skill_gap": dict(grouped),
        "created_at": run.created_at.isoformat(),
    }


def latest_recommendations(db: Session, profile_id: str, career_match_id: str | None = None) -> dict[str, Any]:
    statement = select(LearningRecommendationRun).where(LearningRecommendationRun.profile_id == profile_id)
    if career_match_id:
        statement = statement.where(LearningRecommendationRun.career_match_id == career_match_id)
    row = db.scalar(statement.order_by(LearningRecommendationRun.created_at.desc()))
    if not row:
        return {"status": "not_started", "recommendations": [], "message": "Generate recommendations after selecting a career direction."}
    return recommendation_run_public(db, row.id)


def set_recommendation_status(db: Session, recommendation: LearningRecommendation, status: str, reason_code: str | None = None, feedback_text: str | None = None) -> LearningRecommendation:
    recommendation.status = status
    db.add(
        LearningResourceFeedback(
            recommendation_id=recommendation.id,
            learning_resource_id=recommendation.learning_resource_id,
            profile_id=recommendation.profile_id,
            user_id=recommendation.user_id,
            reason_code=reason_code,
            relevant=False if status == "rejected" else None,
            feedback_text=feedback_text,
            effect_json={"resource_status": status},
        )
    )
    db.commit()
    db.refresh(recommendation)
    return recommendation


def add_feedback(db: Session, recommendation: LearningRecommendation, payload: dict[str, Any]) -> dict[str, Any]:
    resource = db.get(LearningResource, recommendation.learning_resource_id)
    code = payload.get("reason_code")
    effect: dict[str, Any] = {"recalibration_scope": "future_learning_recommendation_runs_only"}
    if code == "too_basic":
        effect["minimum_level_adjustment"] = "prefer next level in future runs"
    elif code == "too_expensive":
        effect["budget_adjustment"] = "prioritise free and open resources in future runs"
    elif code == "too_theoretical":
        effect["format_adjustment"] = "increase practical project weight in future runs"
    elif code == "wrong_language" and resource:
        effect["language"] = resource.language
    elif code == "already_completed":
        recommendation.status = "completed"
        effect["completion"] = "resource excluded from future suggestions; evidence still requires user confirmation"
    row = LearningResourceFeedback(
        recommendation_id=recommendation.id,
        learning_resource_id=recommendation.learning_resource_id,
        profile_id=recommendation.profile_id,
        user_id=recommendation.user_id,
        reason_code=code,
        rating=payload.get("rating"),
        relevant=payload.get("relevant"),
        feedback_text=payload.get("feedback_text"),
        effect_json=effect,
    )
    db.add(row)
    db.commit()
    return {"status": "saved", "feedback_id": row.id, "effect": effect}


def alternative_for_recommendation(db: Session, recommendation: LearningRecommendation, reason_code: str | None = None) -> dict[str, Any]:
    set_recommendation_status(db, recommendation, "alternative_requested", reason_code or "alternative_requested", "User requested another resource.")
    run = db.get(LearningRecommendationRun, recommendation.run_id)
    if run:
        next_run = generate_learning_recommendations(db, db.get(Profile, recommendation.profile_id), run.career_match_id)
        alternatives = [
            item for item in next_run.get("recommendations", [])
            if item["learning_resource_id"] != recommendation.learning_resource_id
            and item.get("skill_gap_item_id") == recommendation.skill_gap_item_id
        ][:3]
    else:
        alternatives = []
    return {"status": "alternative_requested", "alternatives": alternatives}


def comparison_public(row: LearningResourceComparison) -> dict[str, Any]:
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "recommendation_ids": row.recommendation_ids_json or [],
        "resource_ids": row.resource_ids_json or [],
        "criteria_weights": row.criteria_weights_json or {},
        "matrix": row.matrix_json or {},
        "created_at": row.created_at.isoformat(),
    }


def create_learning_resource_comparison(db: Session, profile: Profile, recommendation_ids: list[str], weights: dict[str, float] | None = None) -> LearningResourceComparison:
    selected = recommendation_ids[:3]
    rows = db.scalars(select(LearningRecommendation).where(LearningRecommendation.profile_id == profile.id, LearningRecommendation.id.in_(selected))).all()
    resources = {row.id: row for row in db.scalars(select(LearningResource).where(LearningResource.id.in_([item.learning_resource_id for item in rows]))).all()} if rows else {}
    factors = db.scalars(select(LearningRecommendationFactor).where(LearningRecommendationFactor.recommendation_id.in_([row.id for row in rows]))).all() if rows else []
    factors_by_rec: dict[str, dict[str, float]] = defaultdict(dict)
    for factor in factors:
        factors_by_rec[factor.recommendation_id][factor.factor_type] = factor.factor_value
    matrix = {"items": []}
    for row in rows:
        resource = resources[row.learning_resource_id]
        matrix["items"].append(
            {
                "recommendation_id": row.id,
                "resource_id": resource.id,
                "title": resource.title,
                "provider": resource.provider_id,
                "resource_type": resource.resource_type,
                "alignment_label": row.alignment_label,
                "level": resource.level,
                "duration_minutes": resource.duration_minutes,
                "price": resource.displayed_price,
                "cost_type": resource.cost_type,
                "language": resource.language,
                "certificate_available": resource.certificate_available,
                "project_component": resource.project_included,
                "last_verification": resource.last_verified_at.isoformat() if resource.last_verified_at else None,
                "prerequisites": resource.prerequisites_json or [],
                "strengths": [key for key, value in factors_by_rec[row.id].items() if value >= 75],
                "limitations": row.limitations_json or [],
                "criteria": factors_by_rec[row.id],
            }
        )
    comparison = LearningResourceComparison(
        profile_id=profile.id,
        user_id=profile.user_id,
        recommendation_ids_json=[row.id for row in rows],
        resource_ids_json=[row.learning_resource_id for row in rows],
        criteria_weights_json=weights or {},
        matrix_json=matrix,
        demo_marker=bool(getattr(profile.user, "is_demo", False)) if getattr(profile, "user", None) else False,
    )
    db.add(comparison)
    db.commit()
    db.refresh(comparison)
    return comparison


def roadmap_payload_defaults(recommendation: LearningRecommendation, resource: LearningResource, objective: LearningObjective | None, payload: dict[str, Any]) -> dict[str, Any]:
    title = payload.get("roadmap_title") or f"Learn: {resource.title}"
    objective_text = payload.get("learning_objective") or (objective.description if objective else f"Build evidence with {resource.title}")
    return {
        "title": title,
        "description": f"{objective_text} Resource: {resource.title}.",
        "reason": recommendation.explanation,
        "first_step": "Open the resource, confirm it is still available, and schedule the first learning session.",
        "success_criteria": payload.get("expected_evidence") or "Record a personal summary and one practical evidence artifact.",
        "estimated_minutes": resource.duration_minutes or 120,
        "priority": int(payload.get("priority") or 2),
        "due_date": payload.get("target_completion_date"),
        "scheduled_date": payload.get("start_date"),
        "user_notes": payload.get("notes") or "",
    }


def add_recommendation_to_roadmap(db: Session, recommendation: LearningRecommendation, payload: dict[str, Any]) -> dict[str, Any]:
    resource = db.get(LearningResource, recommendation.learning_resource_id)
    objective = db.get(LearningObjective, recommendation.learning_objective_id) if recommendation.learning_objective_id else None
    roadmap = db.scalar(select(Roadmap).where(Roadmap.profile_id == recommendation.profile_id).order_by(Roadmap.created_at.desc()))
    created = False
    if not roadmap:
        roadmap = Roadmap(user_id=recommendation.user_id, profile_id=recommendation.profile_id, data={**generate_roadmap_fallback(), "version": 0, "status": "active"})
        db.add(roadmap)
        db.flush()
        created = True
    normalize_legacy(db, roadmap)
    if created:
        snapshot(db, roadmap, "Initial roadmap created for learning resource")
    defaults = roadmap_payload_defaults(recommendation, resource, objective, payload)
    action = RoadmapAction(
        roadmap_id=roadmap.id,
        profile_id=recommendation.profile_id,
        user_id=recommendation.user_id,
        recommendation_id=recommendation.id,
        horizon="thirty_days",
        title=defaults["title"],
        description=defaults["description"],
        reason=defaults["reason"],
        first_step=defaults["first_step"],
        success_criteria=defaults["success_criteria"],
        estimated_minutes=defaults["estimated_minutes"],
        effort="medium",
        impact="high",
        priority=defaults["priority"],
        status="not_started",
        due_date=defaults["due_date"],
        scheduled_date=defaults["scheduled_date"],
        user_notes=defaults["user_notes"],
        source_type="learning_resource",
        profile_signals_json=[resource.title, objective.description if objective else "Learning objective"],
        rag_sources_json=[{"title": resource.title, "url": resource.canonical_url, "provider": resource.provider_id}],
        ethical_cautions_json=["Course completion alone records exposure; practical evidence is needed before claiming advanced competence."],
    )
    db.add(action)
    db.flush()
    link = RoadmapLearningAction(
        roadmap_action_id=action.id,
        profile_id=recommendation.profile_id,
        recommendation_id=recommendation.id,
        learning_resource_id=resource.id,
        learning_objective_id=objective.id if objective else None,
        expected_evidence=defaults["success_criteria"],
        metadata_json={"associated_practical_project": payload.get("associated_practical_project"), "weekly_commitment": payload.get("weekly_commitment")},
    )
    db.add(link)
    recommendation.status = "roadmap_added"
    roadmap_event(db, roadmap.id, recommendation.user_id or roadmap.user_id, "action_added", action.id, {"source_type": "learning_resource", "learning_recommendation_id": recommendation.id})
    db.commit()
    return {"status": "added_to_roadmap", "roadmap_id": roadmap.id, "action_id": action.id, "roadmap_learning_action_id": link.id}


def phase_for_resource(resource: LearningResource) -> int:
    if resource.resource_type in {"official_documentation", "internal_article"}:
        return 1
    if resource.resource_type in {"online_course", "interactive_tutorial", "certification_preparation", "internal_guided_module", "youtube_playlist", "youtube_video"}:
        return 2
    if resource.resource_type in {"practical_project", "portfolio_project"}:
        return 3
    if resource.resource_type in {"professional_interview", "job_description_analysis_exercise", "mentoring_activity"}:
        return 4
    return 5


def generate_learning_path(db: Session, profile: Profile, run_id: str | None = None) -> dict[str, Any]:
    if run_id:
        run = db.get(LearningRecommendationRun, run_id)
    else:
        run = db.scalar(select(LearningRecommendationRun).where(LearningRecommendationRun.profile_id == profile.id).order_by(LearningRecommendationRun.created_at.desc()))
    if not run:
        return {"status": "not_started", "message": "Generate recommendations before creating a learning path."}
    preferences = db.get(LearningPreferences, run.preferences_id) if run.preferences_id else ensure_learning_preferences(db, profile)
    match = db.get(CareerMatch, run.career_match_id) if run.career_match_id else None
    recommendations = db.scalars(select(LearningRecommendation).where(LearningRecommendation.run_id == run.id, LearningRecommendation.status != "rejected").order_by(LearningRecommendation.rank_position)).all()
    resources = {row.id: row for row in db.scalars(select(LearningResource).where(LearningResource.id.in_([item.learning_resource_id for item in recommendations]))).all()} if recommendations else {}
    path = LearningPath(
        profile_id=profile.id,
        user_id=profile.user_id,
        career_match_id=run.career_match_id,
        recommendation_run_id=run.id,
        title=f"Personalised Learning Path: {match.title if match else 'Selected direction'}",
        summary="A staged plan generated from skill gaps, preferences, and stored resource records.",
        status="draft",
        weekly_effort_hours=preferences.available_hours_per_week,
        demo_marker=run.demo_marker,
    )
    db.add(path)
    db.flush()
    phase_specs = [
        ("Foundations", "Essential concepts, prerequisites, and AI literacy.", "Personal summary and prerequisite checklist."),
        ("Applied Skills", "Tools, methods, guided exercises, and structured learning.", "Completed exercises and notes."),
        ("Practical Evidence", "Projects, case studies, and portfolio artefacts.", "Project artefact or portfolio entry."),
        ("Career Validation", "Job-description review, professional interview, and role experiment.", "Reflection note and next decision."),
        ("Transition Preparation", "CV, portfolio, interview, and targeted applications.", "Updated profile or application material."),
    ]
    phases: dict[int, LearningPathPhase] = {}
    for index, (title, description, evidence) in enumerate(phase_specs, start=1):
        phase = LearningPathPhase(
            learning_path_id=path.id,
            phase_index=index,
            title=title,
            description=description,
            objectives_json=[],
            estimated_duration_minutes=240,
            weekly_effort_hours=max(1, preferences.available_hours_per_week / 2),
            completion_evidence=evidence,
            dependencies_json=[] if index == 1 else [index - 1],
        )
        db.add(phase)
        db.flush()
        phases[index] = phase
    used_resource_ids: set[str] = set()
    for recommendation in recommendations:
        if recommendation.learning_resource_id in used_resource_ids:
            continue
        resource = resources[recommendation.learning_resource_id]
        phase = phases[phase_for_resource(resource)]
        db.add(
            LearningPathItem(
                learning_path_id=path.id,
                phase_id=phase.id,
                recommendation_id=recommendation.id,
                learning_resource_id=resource.id,
                learning_objective_id=recommendation.learning_objective_id,
                title=resource.title,
                status="planned",
                expected_evidence="Course completion records exposure; practical exercise, project, or reflection records stronger evidence.",
            )
        )
        used_resource_ids.add(resource.id)
    db.commit()
    return learning_path_public(db, path.id)


def learning_path_public(db: Session, path_id: str) -> dict[str, Any]:
    path = db.get(LearningPath, path_id)
    if not path:
        return {"status": "not_found"}
    phases = db.scalars(select(LearningPathPhase).where(LearningPathPhase.learning_path_id == path.id).order_by(LearningPathPhase.phase_index)).all()
    items = db.scalars(select(LearningPathItem).where(LearningPathItem.learning_path_id == path.id).order_by(LearningPathItem.created_at)).all()
    items_by_phase: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        items_by_phase[item.phase_id].append(learning_path_item_public(item))
    return {
        "id": path.id,
        "profile_id": path.profile_id,
        "career_match_id": path.career_match_id,
        "recommendation_run_id": path.recommendation_run_id,
        "title": path.title,
        "summary": path.summary,
        "status": path.status,
        "weekly_effort_hours": path.weekly_effort_hours,
        "phases": [
            {
                "id": phase.id,
                "phase_index": phase.phase_index,
                "title": phase.title,
                "description": phase.description,
                "objectives": phase.objectives_json or [],
                "estimated_duration_minutes": phase.estimated_duration_minutes,
                "weekly_effort_hours": phase.weekly_effort_hours,
                "completion_evidence": phase.completion_evidence,
                "dependencies": phase.dependencies_json or [],
                "items": items_by_phase.get(phase.id, []),
            }
            for phase in phases
        ],
        "created_at": path.created_at.isoformat(),
        "updated_at": path.updated_at.isoformat(),
    }


def learning_path_item_public(item: LearningPathItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "learning_path_id": item.learning_path_id,
        "phase_id": item.phase_id,
        "recommendation_id": item.recommendation_id,
        "learning_resource_id": item.learning_resource_id,
        "learning_objective_id": item.learning_objective_id,
        "title": item.title,
        "status": item.status,
        "progress_percentage": item.progress_percentage,
        "user_reported_progress": item.user_reported_progress,
        "completion_date": item.completion_date,
        "evidence_url": item.evidence_url,
        "reflection": item.reflection,
        "difficulty_feedback": item.difficulty_feedback,
        "relevance_feedback": item.relevance_feedback,
        "expected_evidence": item.expected_evidence,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def latest_learning_path(db: Session, profile_id: str) -> dict[str, Any]:
    path = db.scalar(select(LearningPath).where(LearningPath.profile_id == profile_id).order_by(LearningPath.created_at.desc()))
    if not path:
        return {"status": "not_started", "phases": []}
    return learning_path_public(db, path.id)


def update_learning_path_item_progress(db: Session, item: LearningPathItem, payload: dict[str, Any]) -> dict[str, Any]:
    for key in ["status", "progress_percentage", "user_reported_progress", "completion_date", "evidence_url", "reflection", "difficulty_feedback", "relevance_feedback"]:
        if key in payload and payload[key] is not None:
            setattr(item, key, payload[key])
    if item.status == "completed" and item.progress_percentage < 100:
        item.progress_percentage = 100
    item.updated_at = datetime.utcnow()
    if item.recommendation_id and (payload.get("difficulty_feedback") or payload.get("relevance_feedback")):
        recommendation = db.get(LearningRecommendation, item.recommendation_id)
        db.add(
            LearningResourceFeedback(
                recommendation_id=item.recommendation_id,
                learning_resource_id=item.learning_resource_id,
                profile_id=recommendation.profile_id if recommendation else "",
                user_id=recommendation.user_id if recommendation else None,
                reason_code=payload.get("difficulty_feedback") or payload.get("relevance_feedback"),
                feedback_text=payload.get("reflection"),
                effect_json={"source": "learning_path_progress", "scope": "future_learning_recommendation_runs_only"},
            )
        )
    db.commit()
    return learning_path_item_public(item)


def delete_learning_data(db: Session, profile_id: str) -> dict[str, Any]:
    run_ids = db.scalars(select(LearningRecommendationRun.id).where(LearningRecommendationRun.profile_id == profile_id)).all()
    recommendation_ids = db.scalars(select(LearningRecommendation.id).where(LearningRecommendation.profile_id == profile_id)).all()
    analysis_ids = db.scalars(select(SkillGapAnalysis.id).where(SkillGapAnalysis.profile_id == profile_id)).all()
    gap_ids = db.scalars(select(SkillGapItem.id).where(SkillGapItem.profile_id == profile_id)).all()
    path_ids = db.scalars(select(LearningPath.id).where(LearningPath.profile_id == profile_id)).all()
    phase_ids = db.scalars(select(LearningPathPhase.id).where(LearningPathPhase.learning_path_id.in_(path_ids))).all() if path_ids else []
    if recommendation_ids:
        db.execute(delete(LearningRecommendationFactor).where(LearningRecommendationFactor.recommendation_id.in_(recommendation_ids)))
        db.execute(delete(LearningResourceFeedback).where(LearningResourceFeedback.recommendation_id.in_(recommendation_ids)))
    db.execute(delete(LearningResourceFeedback).where(LearningResourceFeedback.profile_id == profile_id))
    if phase_ids:
        db.execute(delete(LearningPathItem).where(LearningPathItem.phase_id.in_(phase_ids)))
    if path_ids:
        db.execute(delete(LearningPathPhase).where(LearningPathPhase.learning_path_id.in_(path_ids)))
    for model in [RoadmapLearningAction, LearningResourceComparison, LearningPath, PracticalProject, LearningRecommendation, LearningRecommendationRun, LearningObjective, SkillGapItem, SkillGapAnalysis, LearningPreferences]:
        db.execute(delete(model).where(model.profile_id == profile_id))
    db.commit()
    return {"status": "deleted", "deleted": {"runs": len(run_ids), "recommendations": len(recommendation_ids), "analyses": len(analysis_ids), "gaps": len(gap_ids), "paths": len(path_ids)}}


def cache_provider_failure(db: Session, provider_name: str, cache_key: str, error_message: str) -> None:
    settings = get_settings()
    db.add(
        ExternalProviderCache(
            provider_name=provider_name,
            cache_key=cache_key,
            response_json={},
            status="error",
            error_message=error_message[:1000],
            expires_at=datetime.utcnow() + timedelta(seconds=settings.learning_resource_cache_ttl_seconds),
        )
    )
    db.flush()


def search_with_provider_fallback(db: Session, adapters: list[LearningProviderAdapter], query: LearningResourceQuery) -> tuple[list[ExternalLearningResource], list[dict[str, str]]]:
    results: list[ExternalLearningResource] = []
    statuses: list[dict[str, str]] = []
    for adapter in adapters:
        try:
            found = adapter.search_resources(query)
            results.extend(found[: query.limit])
            statuses.append({"provider": adapter.provider_name, "status": "ok", "count": str(len(found))})
        except TimeoutError as error:
            cache_provider_failure(db, adapter.provider_name, repr(query), str(error))
            statuses.append({"provider": adapter.provider_name, "status": "timeout", "message": "Curated catalogue fallback remained available."})
        except Exception as error:
            cache_provider_failure(db, adapter.provider_name, repr(query), str(error))
            statuses.append({"provider": adapter.provider_name, "status": "error", "message": "Provider failure did not stop recommendation flow."})
    return results, statuses
