import logging
import sys
from app.core.config import settings

def setup_logging() -> None:
    """Sets up standard application logging."""
    log_level = logging.DEBUG if settings.ENV == "development" else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Silence verbose logs from third-party packages in development/production
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
