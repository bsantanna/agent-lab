import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
LOG_FILE = "app.log"
LOG_LEVEL = logging.DEBUG

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, LOG_FILE), maxBytes=10485760, backupCount=3
)
console_handler = logging.StreamHandler()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[file_handler, console_handler],
)

logger = logging.getLogger(__name__)
