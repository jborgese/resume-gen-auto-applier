# Resume Generator & Auto-Applicator - Environment Configuration
# Copy this file to .env and fill in your actual values

# =============================================================================
# REQUIRED CREDENTIALS
# =============================================================================

# LinkedIn Credentials (REQUIRED)
LINKEDIN_EMAIL=your.email@example.com
LINKEDIN_PASSWORD=your_linkedin_password

# =============================================================================
# OPTIONAL API KEYS
# =============================================================================

# OpenAI API Key (for resume tailoring)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Anthropic API Key (backup LLM provider)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================

# Debug mode (true/false)
DEBUG=false

# Maximum number of jobs to scrape (1-100)
MAX_JOBS=15

# Enable LinkedIn Easy Apply automation (true/false)
AUTO_APPLY=true

# Default resume template filename
DEFAULT_TEMPLATE=base_resume.html

# Portfolio website URL (optional)
PORTFOLIO=https://your-portfolio.com

# =============================================================================
# BROWSER CONFIGURATION
# =============================================================================

# Run browser in headless mode (true/false)
HEADLESS_MODE=false

# Enable browser connection monitoring (true/false)
ENABLE_BROWSER_MONITORING=false

# Suppress harmless browser console warnings (true/false)
SUPPRESS_CONSOLE_WARNINGS=true

# =============================================================================
# LLM CONFIGURATION
# =============================================================================

# LLM model to use (gpt-3.5-turbo, gpt-4, claude-3-sonnet, etc.)
LLM_MODEL=gpt-3.5-turbo

# LLM temperature (0.0-2.0)
LLM_TEMPERATURE=0.7

# Maximum tokens for LLM responses (100-4000)
LLM_MAX_TOKENS=1000

# =============================================================================
# TIMEOUT CONFIGURATION (milliseconds)
# =============================================================================

# Page load timeout
TIMEOUT_PAGE_LOAD=30000

# Login timeout
TIMEOUT_LOGIN=30000

# Search page timeout
TIMEOUT_SEARCH_PAGE=45000

# Job page timeout
TIMEOUT_JOB_PAGE=30000

# Job title extraction timeout
TIMEOUT_JOB_TITLE=15000

# Modal wait timeout
TIMEOUT_MODAL_WAIT=20000

# Easy Apply click timeout
TIMEOUT_EASY_APPLY_CLICK=5000

# Login success detection timeout
TIMEOUT_LOGIN_SUCCESS=5000

# Job list loading timeout
TIMEOUT_JOB_LIST=10000

# Job cards loading timeout
TIMEOUT_JOB_CARDS=10000

# Total jobs count timeout
TIMEOUT_TOTAL_JOBS=5000

# DOM refresh timeout
TIMEOUT_DOM_REFRESH=3000

# Radio button click timeout
TIMEOUT_RADIO_CLICK=3000

# =============================================================================
# RETRY CONFIGURATION
# =============================================================================

# Maximum retry attempts
MAX_RETRY_ATTEMPTS=3

# Retry delay in seconds
RETRY_DELAY=1.0

# Maximum scroll passes
MAX_SCROLL_PASSES=15

# Maximum Easy Apply steps
MAX_EASY_APPLY_STEPS=10

# =============================================================================
# SCROLL CONFIGURATION
# =============================================================================

# Base scroll speed
SCROLL_BASE_SPEED=350

# Minimum scroll speed
SCROLL_MIN_SPEED=150

# Maximum scroll speed
SCROLL_MAX_SPEED=500

# Pause between scrolls (seconds)
SCROLL_PAUSE_BETWEEN=1.0

# Scroll jitter range
SCROLL_JITTER_RANGE=20

# Upward scroll frequency
SCROLL_UPWARD_FREQUENCY=4

# =============================================================================
# DELAY CONFIGURATION (seconds)
# =============================================================================

# Login processing delay
DELAY_LOGIN_PROCESSING=3.0

# UI stability delay
DELAY_UI_STABILITY=0.2

# Easy Apply hover delay
DELAY_EASY_APPLY_HOVER=0.5

# Modal wait delay
DELAY_MODAL_WAIT=1.2

# Step processing delay
DELAY_STEP_PROCESSING=1.0

# DOM refresh delay
DELAY_DOM_REFRESH=3.0

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Log file path (optional, leave empty for console only)
LOG_FILE=

# =============================================================================
# SYSTEM CONFIGURATION
# =============================================================================

# Python encoding
PYTHONIOENCODING=utf-8

# Python path (automatically set by scripts)
# PYTHONPATH=src
