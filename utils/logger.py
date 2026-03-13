"""
Structured Logging Utility
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Create logs directory
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Configure logging
def setup_logger(name: str = "health_chatbot", level: int = logging.INFO):
    """
    Setup structured logger
    
    Args:
        name: Logger name
        level: Logging level
    
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    log_file = LOGS_DIR / f"health_chatbot_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger

# Create default logger
logger = setup_logger()

# Helper functions for specific logging
def log_ai_call(api_name: str, query_type: str, response_time: float, success: bool):
    """Log AI API call"""
    status = "SUCCESS" if success else "FAILED"
    logger.info(
        f"AI_CALL | API: {api_name} | Type: {query_type} | "
        f"Time: {response_time:.2f}s | Status: {status}"
    )

def log_database_query(query_type: str, execution_time: float, rows_returned: int):
    """Log database query"""
    logger.debug(
        f"DB_QUERY | Type: {query_type} | Time: {execution_time:.3f}s | Rows: {rows_returned}"
    )

def log_user_action(session_id: str, action: str, details: str = ""):
    """Log user action"""
    logger.info(f"USER_ACTION | Session: {session_id} | Action: {action} | {details}")

def log_error(error_type: str, error_message: str, context: dict = None):
    """Log error with context"""
    context_str = f" | Context: {context}" if context else ""
    logger.error(f"ERROR | Type: {error_type} | Message: {error_message}{context_str}")

def log_rag_retrieval(query: str, foods_retrieved: int, query_type: str):
    """Log RAG retrieval"""
    logger.info(
        f"RAG_RETRIEVAL | Query: '{query[:50]}...' | "
        f"Foods: {foods_retrieved} | Type: {query_type}"
    )
