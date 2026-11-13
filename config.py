import os

class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dali_gastos_dev_secret_key_2026_uprit")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "gastos.db")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 3600 * 4  # 4 horas de sesión
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_TIME = 300  # 5 minutos

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False

class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # Requiere HTTPS en producción

class TestingConfig(BaseConfig):
    DEBUG = False
    TESTING = True
    DATABASE_PATH = "test_gastos.db"
    SESSION_COOKIE_SECURE = False

config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}
