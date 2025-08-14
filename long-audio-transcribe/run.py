#!/usr/bin/env python3
"""
长音频转录服务启动脚本
支持开发、测试和生产环境配置
"""

import os
import sys
from app import app
from config import config

def main():
    """主启动函数"""
    
    # 获取环境配置
    env = os.environ.get('FLASK_ENV', 'development')
    
    if env not in config:
        print(f"错误: 不支持的环境 '{env}'")
        print(f"支持的环境: {', '.join(config.keys())}")
        sys.exit(1)
    
    # 加载配置
    app.config.from_object(config[env])
    
    # 设置日志级别
    import logging
    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 打印启动信息
    print(f"启动长音频转录服务...")
    print(f"环境: {env}")
    print(f"vLLM Whisper URL: {app.config.get('VLLM_WHISPER_URL', 'Not configured')}")
    print(f"最大文件大小: {app.config.get('MAX_CONTENT_LENGTH', 0) / (1024*1024):.1f}MB")
    print(f"默认片段时长: {app.config.get('DEFAULT_CHUNK_DURATION', 30)}秒")
    print(f"服务地址: http://localhost:5000")
    print(f"健康检查: http://localhost:5000/health")
    print("-" * 50)
    
    # 启动服务
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=app.config.get('DEBUG', False)
        )
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"启动服务时出错: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
