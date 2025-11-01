"""Application settings using pydantic-settings"""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    API_TITLE: str = "ePDF Analyzer"
    API_VERSION: str = "1.0.0"
    
    # PDF Processing Settings
    PDF_MAX_SIZE_MB: int = 50
    PDF_MAX_PAGES: int = 100
    PDF_DPI: int = 300
    
    # Table Extraction Settings
    TABLE_DETECTION_METHOD: Literal["pdfplumber", "camelot"] = "pdfplumber"
    TABLE_MIN_ROWS: int = 2
    TABLE_MIN_COLS: int = 2
    
    # Export Settings
    EXCEL_MAX_SHEETS: int = 50
    EXCEL_ENGINE: Literal["openpyxl", "xlsxwriter"] = "openpyxl"
    CSV_DELIMITER: str = ","
    CSV_ENCODING: str = "utf-8"
    
    # File Storage
    UPLOAD_FOLDER: str = "./uploads"
    TEMP_FOLDER: str = "./temp"
    AUTO_CREATE_FOLDERS: bool = True
    
    # LLM Settings
    LLM_MODEL_NAME: str = "Qwen/Qwen3-VL-2B-Instruct"  # Vision-language model for text and image processing
    LLM_MAX_TOKENS: int = 256
    LLM_TEMPERATURE: float = 0.1
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    def get_upload_path(self) -> Path:
        """Get upload folder path and create if not exists"""
        path = Path(self.UPLOAD_FOLDER)
        if self.AUTO_CREATE_FOLDERS:
            path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_temp_path(self) -> Path:
        """Get temp folder path and create if not exists"""
        path = Path(self.TEMP_FOLDER)
        if self.AUTO_CREATE_FOLDERS:
            path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes"""
        return self.PDF_MAX_SIZE_MB * 1024 * 1024


# Global settings instance
settings = Settings()

