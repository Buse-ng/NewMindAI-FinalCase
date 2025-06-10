import os
from pathlib import Path

# Temel dizin yolu
BASE_DIR = Path(__file__).parent.parent.parent

# PDF işlemleri için dizinler
PDF_DIR = Path(os.getenv("PDF_DIR", BASE_DIR / "data" / "pdfs"))
RAW_DATA_DIR = Path(os.getenv("RAW_DATA_DIR", BASE_DIR / "data" / "raw"))
PAPERS_JSON = Path(os.getenv("PAPERS_JSON", RAW_DATA_DIR / "papers.json"))
PROCESSED_DATA_DIR = Path(os.getenv("PROCESSED_DATA_DIR", BASE_DIR / "data" / "processed"))
PROCESSED_PAPERS_JSON = Path(os.getenv("PROCESSED_PAPERS_JSON", BASE_DIR / "data" / "processed" / "processed_papers.json"))

# Dizinler
PDF_DIR.mkdir(parents=True, exist_ok=True)
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
PAPERS_JSON.parent.mkdir(parents=True, exist_ok=True) 