from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # 应用配置
    APP_NAME: str = "帽子天气"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 60245
    APP_V1_PREFIX: str = "/api"

    # 密钥
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1天

    # MySQL
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "maozi_weather"
    DB_ECHO: bool = False

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    # CORS 允许的前端来源（逗号分隔），例如: http://localhost:5173,https://web.maozi.com
    # 生产环境必填；留空时开发环境(APP_DEBUG=True)放行全部来源，生产环境(APP_DEBUG=False)必须显式配置
    CORS_ORIGINS: str = ""

    # CMA 气象数据网
    CMA_APPID: str = ""
    CMA_APPSECRET: str = ""
    CMA_BASE_URL: str = "http://data.cma.cn/api"

    # CMA 限流
    CMA_QPS_LIMIT: int = 10
    CMA_MAX_RETRIES: int = 3
    CMA_RETRY_DELAY: int = 2

    # 和风天气 (QWeather) - Ed25519 JWT 认证
    QWEATHER_KEY: str = ""  # 和风天气 API Key（可选，用于增强数据）
    QWEATHER_CRED_ID: str = ""  # 凭据 ID（如 T4B99P5557）
    QWEATHER_USER_ID: str = ""  # User ID（如 46E5G85Q4G）
    QWEATHER_API_HOST: str = ""  # 自定义 API Host（如 ng6yw3hg4y.re.qweatherapi.com）
    QWEATHER_PRIVATE_KEY_PATH: str = ""  # Ed25519 私钥文件路径

    # 数据源配置
    WEATHER_PRIMARY_SOURCE: str = "open_meteo"  # 主数据源: open_meteo / qweather
    WEATHER_FALLBACK_ENABLED: bool = True  # 是否启用自动备份切换

    # 日志
    LOG_LEVEL: str = "INFO"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        password = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{password}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings = Settings()
