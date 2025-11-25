import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger():
    """
    Sets up the application logger.
    Logs are written to 'app.log' in the root directory.
    Rotates logs at 1MB, keeping 3 backups.
    """
    log_file = "app.log"
    
    # Create logger
    logger = logging.getLogger("Kakeibo")
    logger.setLevel(logging.DEBUG)
    
    # Check if handler already exists to avoid duplicate logs
    if not logger.handlers:
        # Create rotating file handler
        handler = RotatingFileHandler(
            log_file, 
            maxBytes=1*1024*1024, # 1MB
            backupCount=3,
            encoding='utf-8'
        )
        handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        
    return logger
