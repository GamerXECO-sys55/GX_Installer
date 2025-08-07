"""
Centralized logging system for GamerX Installer
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from config.settings import LOGS_DIR

class ColoredFormatter(logging.Formatter):
    """Colored console formatter"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        return super().format(record)

def setup_logging(level=logging.INFO):
    """Setup logging configuration"""
    
    # Create logs directory
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"gxinstall_{timestamp}.log"
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = ColoredFormatter(
        '%(levelname)s | %(name)s | %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for detailed logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Log startup info
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Log file: {log_file}")
    
    return log_file

def get_logger(name):
    """Get a logger instance"""
    return logging.getLogger(name)
