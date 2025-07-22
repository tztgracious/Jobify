"""
Project-wide logging configuration for the Jobify backend.

This module provides a centralized logger that can be used across all Django apps.
It creates a rotating file handler that writes to logs/jobify.log with detailed formatting.

Usage:
    from jobify_backend.logger import logger
    
    logger.info("This is an info message")
    logger.error("This is an error message")
    logger.warning("This is a warning message")
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from django.conf import settings


class JobifyLogger:
    """Singleton logger class for the Jobify project."""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JobifyLogger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._logger = self._setup_logger()
    
    def _setup_logger(self):
        """Setup and configure the project logger."""
        logger = logging.getLogger('jobify')
        
        # Prevent duplicate handlers if this function is called multiple times
        if logger.handlers:
            return logger
        
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(settings.BASE_DIR), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create rotating file handler (max 10MB, keep 5 backup files)
        log_file = os.path.join(log_dir, 'jobify.log')
        handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        
        # Create formatter with detailed information
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        
        # Prevent propagation to root logger to avoid duplicate logs
        logger.propagate = False
        
        return logger
    
    @property
    def logger(self):
        """Get the configured logger instance."""
        return self._logger


# Create a singleton instance and expose the logger
_jobify_logger = JobifyLogger()
logger = _jobify_logger.logger

# For backwards compatibility, also provide the setup function
def setup_jobify_logger():
    """
    Setup custom logger that writes to jobify.log file.
    
    This function is maintained for backwards compatibility.
    New code should directly import 'logger' from this module.
    """
    return logger
