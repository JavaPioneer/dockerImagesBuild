from flask import Flask, request, jsonify
import os
import tempfile
import librosa
import numpy as np
from pydub import AudioSegment
import requests
import json
from werkzeug.utils import secure_filename
import logging

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 默认配置
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a', 'flac', 'ogg'}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
VLLM_WHISPER_URL = "http://localhost:8000/v1/audio/transcriptions"

# 应用配置
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    allowed_extensions = app.config.get('ALLOWED_EXTENSIONS', ALLOWED_EXTENSIONS)
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def split_audio(audio_path, chunk_duration=30):
    """
    将长音频文件分割成指定时长的片段
    
    Args:
        audio_path: 音频文件路径
        chunk_duration: 每个片段的时长（秒）
    
    Returns:
        list: 临时文件路径列表
    """
    try:
        # 加载音频文件
        audio = AudioSegment.from_file(audio_path)
        
        # 计算需要分割的片段数
        total_duration = len(audio) / 1000  # 转换为秒
        chunk_duration_ms = chunk_duration * 1000
        
        temp_files = []
        
        for i in range(0, len(audio), chunk_duration_ms):
            # 提取片段
            chunk = audio[i:i + chunk_duration_ms]
            
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(
                suffix='.wav', 
                delete=False,
                dir=app.config['UPLOAD_FOLDER']
            )
            
            # 导出片段
            chunk.export(temp_file.name, format='wav')
            temp_files.append(temp_file.name)
            
            logger.info(f"创建音频片段 {len(temp_files)}: {temp_file.name}")
        
        return temp_files
    
    except Exception as e:
        logger.error(f"分割音频时出错: {str(e)}")
        raise

def transcribe_chunk(audio_file_path):
    """
    使用vLLM Whisper服务转录单个音频片段
    
    Args:
        audio_file_path: 音频文件路径
    
    Returns:
        str: 转录文本
    """
    try:
        with open(audio_file_path, 'rb') as audio_file:
            files = {'file': audio_file}
            
            # 发送请求到vLLM Whisper服务
            vllm_url = app.config.get('VLLM_WHISPER_URL', VLLM_WHISPER_URL)
            timeout = app.config.get('REQUEST_TIMEOUT', 60)
            response = requests.post(
                vllm_url,
                files=files,
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('text', '')
            else:
                logger.error(f"转录请求失败: {response.status_code} - {response.text}")
                return ""
                
    except Exception as e:
        logger.error(f"转录片段时出错: {str(e)}")
        return ""

def cleanup_temp_files(temp_files):
    """清理临时文件"""
    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
                logger.info(f"删除临时文件: {temp_file}")
        except Exception as e:
            logger.error(f"删除临时文件失败: {temp_file} - {str(e)}")

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'message': '长音频转录服务运行正常'
    })

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """
    长音频转录端点
    
    请求参数:
    - file: 音频文件（支持wav, mp3, m4a, flac, ogg格式）
    - chunk_duration: 可选，每个片段的时长（秒），默认30秒
    
    返回:
    - text: 完整转录文本
    - segments: 每个片段的转录结果
    - duration: 音频总时长
    """
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件格式'}), 400
        
        # 获取可选参数
        chunk_duration = int(request.form.get('chunk_duration', 30))
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        logger.info(f"收到音频文件: {filename}")
        
        try:
            # 分割音频
            temp_files = split_audio(file_path, chunk_duration)
            
            # 转录每个片段
            segments = []
            full_text = ""
            
            for i, temp_file in enumerate(temp_files):
                logger.info(f"正在转录片段 {i+1}/{len(temp_files)}")
                
                text = transcribe_chunk(temp_file)
                segments.append({
                    'segment_id': i + 1,
                    'text': text,
                    'start_time': i * chunk_duration,
                    'end_time': (i + 1) * chunk_duration
                })
                
                full_text += text + " "
            
            # 清理临时文件
            cleanup_temp_files(temp_files)
            
            # 获取音频总时长
            audio = AudioSegment.from_file(file_path)
            total_duration = len(audio) / 1000
            
            # 删除上传的原始文件
            os.unlink(file_path)
            
            return jsonify({
                'success': True,
                'text': full_text.strip(),
                'segments': segments,
                'duration': total_duration,
                'chunk_count': len(segments),
                'chunk_duration': chunk_duration
            })
            
        except Exception as e:
            # 清理临时文件
            if 'temp_files' in locals():
                cleanup_temp_files(temp_files)
            
            # 删除上传的原始文件
            if os.path.exists(file_path):
                os.unlink(file_path)
            
            logger.error(f"转录过程中出错: {str(e)}")
            return jsonify({'error': f'转录失败: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"处理请求时出错: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

@app.route('/transcribe_url', methods=['POST'])
def transcribe_audio_url():
    """
    通过URL转录长音频
    
    请求参数:
    - audio_url: 音频文件URL
    - chunk_duration: 可选，每个片段的时长（秒），默认30秒
    """
    try:
        data = request.get_json()
        
        if not data or 'audio_url' not in data:
            return jsonify({'error': '缺少audio_url参数'}), 400
        
        audio_url = data['audio_url']
        chunk_duration = int(data.get('chunk_duration', 30))
        
        logger.info(f"开始下载音频文件: {audio_url}")
        
        # 下载音频文件
        response = requests.get(audio_url, stream=True)
        response.raise_for_status()
        
        # 保存到临时文件
        temp_file = tempfile.NamedTemporaryFile(
            suffix='.wav',
            delete=False,
            dir=app.config['UPLOAD_FOLDER']
        )
        
        for chunk in response.iter_content(chunk_size=8192):
            temp_file.write(chunk)
        
        temp_file.close()
        
        try:
            # 分割音频
            temp_files = split_audio(temp_file.name, chunk_duration)
            
            # 转录每个片段
            segments = []
            full_text = ""
            
            for i, chunk_file in enumerate(temp_files):
                logger.info(f"正在转录片段 {i+1}/{len(temp_files)}")
                
                text = transcribe_chunk(chunk_file)
                segments.append({
                    'segment_id': i + 1,
                    'text': text,
                    'start_time': i * chunk_duration,
                    'end_time': (i + 1) * chunk_duration
                })
                
                full_text += text + " "
            
            # 清理临时文件
            cleanup_temp_files(temp_files)
            os.unlink(temp_file.name)
            
            # 获取音频总时长
            audio = AudioSegment.from_file(temp_file.name)
            total_duration = len(audio) / 1000
            
            return jsonify({
                'success': True,
                'text': full_text.strip(),
                'segments': segments,
                'duration': total_duration,
                'chunk_count': len(segments),
                'chunk_duration': chunk_duration
            })
            
        except Exception as e:
            # 清理临时文件
            if 'temp_files' in locals():
                cleanup_temp_files(temp_files)
            os.unlink(temp_file.name)
            
            logger.error(f"转录过程中出错: {str(e)}")
            return jsonify({'error': f'转录失败: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"处理URL转录请求时出错: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
