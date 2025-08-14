import os

class Config:
    """基础配置类"""
    
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    
    # 上传配置
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a', 'flac', 'ogg'}
    
    # vLLM Whisper服务配置
    VLLM_WHISPER_URL = os.environ.get('VLLM_WHISPER_URL') or "http://localhost:8000/v1/audio/transcriptions"
    
    # 音频处理配置
    DEFAULT_CHUNK_DURATION = 30  # 默认片段时长（秒）
    MAX_CHUNK_DURATION = 60      # 最大片段时长（秒）
    
    # 请求超时配置
    REQUEST_TIMEOUT = 60         # 请求超时时间（秒）
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    
    # 生产环境建议设置更严格的限制
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True

# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
