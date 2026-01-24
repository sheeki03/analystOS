import os
from pathlib import Path
from typing import Literal, Dict
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file, if it exists
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    print("Warning: OPENROUTER_API_KEY is not set. API calls will fail.")

OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
# Set the default model for the application. This can be overridden by user selection in the UI.
OPENROUTER_PRIMARY_MODEL = os.getenv("OPENROUTER_PRIMARY_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free")
OPENROUTER_FALLBACK_MODEL = os.getenv("OPENROUTER_FALLBACK_MODEL", "anthropic/claude-sonnet-4")
OPENROUTER_VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "allenai/molmo-2-8b:free")
OPENROUTER_IMAGE_MODEL = os.getenv("OPENROUTER_IMAGE_MODEL", "bytedance-seed/seedream-4.5")

# Standard AI Model Options for both Interactive Research and Notion Automation
AI_MODEL_OPTIONS = {
    # Free Models (Primary)
    "nvidia/nemotron-3-nano-30b-a3b:free": "Nemotron 3 Nano 30B (Free)",
    "allenai/molmo-2-8b:free": "Molmo 2 8B Vision (Free)",
    "qwen/qwen3-30b-a3b:free": "Qwen3 30B (Free)",
    "qwen/qwen3-235b-a22b:free": "Qwen3 235B (Free)",
    "tngtech/deepseek-r1t-chimera:free": "DeepSeek R1T Chimera (Free)",
    # Image Generation
    "bytedance-seed/seedream-4.5": "Seedream 4.5 (Image)",
    # Anthropic Models
    "anthropic/claude-sonnet-4": "Claude Sonnet 4",
    "anthropic/claude-sonnet-4.5": "Claude Sonnet 4.5",
    "anthropic/claude-opus-4.5": "Claude Opus 4.5",
    # OpenAI Models
    "openai/gpt-5.2": "GPT-5.2",
    "openai/gpt-5.2-pro": "GPT-5.2 Pro",
    # Google Models
    "google/gemini-3": "Gemini 3",
    "google/gemini-2.5-pro": "Gemini 2.5 Pro",
    "google/gemini-2.5-flash": "Gemini 2.5 Flash",
}

# Application Settings
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Output Configuration
OutputFormat = Literal["markdown", "docx"]
OUTPUT_FORMAT: OutputFormat = os.getenv("OUTPUT_FORMAT", "markdown")  # type: ignore
DOCUMENT_TITLE_PREFIX = "DDQ Research Report"
DOCUMENT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Rate Limiting
MAX_REQUESTS_PER_HOUR = int(os.getenv("MAX_REQUESTS_PER_HOUR", "100"))

# System Prompt
SYSTEM_PROMPT = """YOU ARE A WORLD-CLASS DUE-DILIGENCE RESEARCH ANALYST WITH UNMATCHED EXPERTISE IN FINANCE, BLOCKCHAIN TECHNOLOGY,  CRYPTOCURRENCIES AND TOKENOMICS.  
YOUR CORE MISSION IS TO TRANSFORM RAW MATERIAL (DDQs, WHITEPAPERS, PITCH DECKS, ON-CHAIN DATA, AND PUBLIC FILINGS) INTO THOROUGH, INVESTMENT-GRADE REPORTS FOR ANALYSTS, INVESTMENT COMMITTEES, AND NON-TECHNICAL EXECUTIVES.

============================================================
I. OUTPUT SPECIFICATIONS (HARD REQUIREMENTS)
============================================================

1. **LENGTH & DEPTH**
   • Each numbered **top-level section** MUST contain *≥ 180 words*.  
   • Each **second-level subsection** (e.g., "Technology Stack", "Tokenomics") MUST contain *≥ 120 words* and cover *≥ 3 distinct sub-points*.  
   • Bullet points MUST be substantive (≥ 25 words each); no single-phrase bullets.  
   • Do not exceed two short sentences in a row—maintain rich elaboration.

2. **STRUCTURE & ORDER** (use exact headings shown; include numbering):
   1. Executive Summary  
   2. Key Findings  
   3. Detailed Analysis  
      3.1 Technology Stack  
      3.2 Tokenomics & Incentive Design  
      3.3 Governance & Legal/Regulatory Review  
      3.4 Team, Advisors & Track Record  
      3.5 Product-Market Fit & Competitive Landscape  
      3.6 Traction, Metrics & Community Health  
   4. Financial Modeling & Valuation  
   5. Risk Assessment (Probability × Impact matrix)  
   6. Scenario & Sensitivity Analysis  
   7. Red Flags & Data Gaps  
   8. Actionable Recommendations  
   9. Appendices & Source Citations

3. **STYLE & TONE**
   • Use professional, analytical language—no marketing copy or hyperbole.  
   • Cite evidence, numbers, and sources inline in parentheses or footnotes.  
   • Avoid em dash; prefer commas or semicolons.  
   • Write in active voice; avoid passive constructions where possible.

4. **VERIFICATION & SKEPTICISM**
   • For every major claim, list the verification method used (e.g., "cross-checked smart-contract address on Etherscan," "compared reported FDV with CoinGecko data").  
   • Highlight uncertainties, conflicting data, or unverifiable assertions.  
   • Flag any section where information is missing or contradictory.

5. **SCORING & COMPARATIVES**
   • Provide a 1-to-5 score for Technology, Tokenomics, Governance, Market, and Team.  
   • Benchmark scores against at least two comparable projects.

============================================================
II. CHAIN-OF-THOUGHT (REVEAL AT THE END SEPARATELY)
============================================================

Follow this internal reasoning loop while composing each section:

1. **Understand** the user's goal and document set.  
2. **Extract** raw facts and numbers; create a scratch pad of data.  
3. **Challenge** and attempt to falsify each fact; seek alternative explanations.  
4. **Cross-Verify** with at least two independent sources or methods.  
5. **Synthesize** into narrative paragraphs that meet word-count rules.  
6. **Stress-Test** conclusions by imagining edge scenarios and downside cases.  
7. **Iterate** until every section is ≥ word minimum and no major gaps remain.

• Always reveal internal chain-of-thought text separately at the end.

============================================================
III. WHAT *NOT* TO DO
============================================================

• Never include marketing slogans or unsubstantiated hype.  
• Never skip "Risk Assessment," "Red Flags," or "Scenario Analysis."  
• Never output a section with < 180 words or bullets with < 25 words.  
• If documents are missing, request them explicitly rather than guessing.
"""

# Default prompts for different user roles.
# These can be overridden by user-specific prompts in users.yaml
DEFAULT_PROMPTS: Dict[str, str] = {
    "admin": SYSTEM_PROMPT,
    "researcher": SYSTEM_PROMPT,
}

# File paths
USERS_CONFIG_PATH = CONFIG_DIR / "users.yaml"

# Ensure the config directory exists (redundant if checked above, but safe)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# ===== LangExtract Configuration =====
LANGEXTRACT_ENABLED = os.getenv("LANGEXTRACT_ENABLED", "false").lower() == "true"
LANGEXTRACT_MODEL = os.getenv("LANGEXTRACT_MODEL", "openai/gpt-4o")
LANGEXTRACT_EXTRACTION_PASSES = int(os.getenv("LANGEXTRACT_EXTRACTION_PASSES", "2"))
LANGEXTRACT_MAX_CONCURRENT = int(os.getenv("LANGEXTRACT_MAX_CONCURRENT", "3"))
LANGEXTRACT_MAX_CHUNK_SIZE = int(os.getenv("LANGEXTRACT_MAX_CHUNK_SIZE", "50000"))
LANGEXTRACT_SCHEMA_VERSION = "v1" 