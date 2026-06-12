from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict

class VoiceName(str, Enum):
    Puck = "Puck"       # Male, young and energetic
    Kore = "Kore"       # Female, bright and clear
    Aoede = "Aoede"     # Female, warm and authoritative
    Charon = "Charon"   # Male, deep and authoritative
    Fenrir = "Fenrir"   # Male, gritty and deep
    Leda = "Leda"       # Female, soft and gentle

class Settings(BaseSettings):
    llm_base_url: str = "https://opencode.ai/zen/go/v1"
    llm_api_key: str
    model_name: str = "zai-glm-4.6"
    
    tts_base_url: str = "https://generativelanguage.googleapis.com/v1beta/models"
    google_api_key: str
    tts_model: str = "gemini-3.1-flash-tts-preview"
    
    target_dir: str = "mp3"
    tmp_dir: str = "tmp"
    language: str = "english"
    readspeed: int = 132
    audience: str = "Children"
    length_in_min: int = 8
    chapters: int = 0
    preread_loops: int = 2
    
    voice: VoiceName = VoiceName.Puck
    voice_male: VoiceName = VoiceName.Puck
    voice_female: VoiceName = VoiceName.Kore
    speech_speed: float = 1.0
    
    debug: bool = False
    verbose: bool = False

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore",
        protected_namespaces=('settings_',)
    )

settings = Settings()
