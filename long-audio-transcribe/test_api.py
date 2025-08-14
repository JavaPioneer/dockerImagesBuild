#!/usr/bin/env python3
"""
API测试脚本
用于测试长音频转录服务的各个端点
"""

import requests
import json
import os
import time

# 服务配置
BASE_URL = "http://localhost:5000"

def test_health_check():
    """测试健康检查端点"""
    print("=== 测试健康检查端点 ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"健康检查失败: {e}")
        return False

def test_file_upload_transcribe(audio_file_path):
    """测试文件上传转录"""
    print(f"\n=== 测试文件上传转录: {audio_file_path} ===")
    
    if not os.path.exists(audio_file_path):
        print(f"文件不存在: {audio_file_path}")
        return False
    
    try:
        with open(audio_file_path, 'rb') as f:
            files = {'file': f}
            data = {'chunk_duration': 30}
            
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/transcribe",
                files=files,
                data=data,
                timeout=300  # 5分钟超时
            )
            end_time = time.time()
            
            print(f"状态码: {response.status_code}")
            print(f"处理时间: {end_time - start_time:.2f}秒")
            
            if response.status_code == 200:
                result = response.json()
                print(f"转录成功!")
                print(f"音频时长: {result.get('duration', 'N/A')}秒")
                print(f"片段数量: {result.get('chunk_count', 'N/A')}")
                print(f"转录文本: {result.get('text', '')[:200]}...")
                return True
            else:
                print(f"转录失败: {response.text}")
                return False
                
    except Exception as e:
        print(f"文件上传转录失败: {e}")
        return False

def test_url_transcribe(audio_url):
    """测试URL转录"""
    print(f"\n=== 测试URL转录: {audio_url} ===")
    
    try:
        data = {
            'audio_url': audio_url,
            'chunk_duration': 30
        }
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/transcribe_url",
            json=data,
            timeout=300  # 5分钟超时
        )
        end_time = time.time()
        
        print(f"状态码: {response.status_code}")
        print(f"处理时间: {end_time - start_time:.2f}秒")
        
        if response.status_code == 200:
            result = response.json()
            print(f"转录成功!")
            print(f"音频时长: {result.get('duration', 'N/A')}秒")
            print(f"片段数量: {result.get('chunk_count', 'N/A')}")
            print(f"转录文本: {result.get('text', '')[:200]}...")
            return True
        else:
            print(f"转录失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"URL转录失败: {e}")
        return False

def create_test_audio():
    """创建一个测试音频文件（如果不存在）"""
    test_file = "test_audio.wav"
    if os.path.exists(test_file):
        print(f"测试音频文件已存在: {test_file}")
        return test_file
    
    print("创建测试音频文件...")
    try:
        import numpy as np
        from scipy.io import wavfile
        
        # 创建一个简单的测试音频（10秒，440Hz正弦波）
        sample_rate = 16000
        duration = 10  # 10秒
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio = np.sin(2 * np.pi * 440 * t) * 0.3  # 440Hz正弦波
        
        # 保存为WAV文件
        wavfile.write(test_file, sample_rate, audio.astype(np.float32))
        print(f"测试音频文件已创建: {test_file}")
        return test_file
        
    except ImportError:
        print("scipy未安装，无法创建测试音频文件")
        return None
    except Exception as e:
        print(f"创建测试音频文件失败: {e}")
        return None

def main():
    """主测试函数"""
    print("开始测试长音频转录服务...")
    
    # 测试健康检查
    if not test_health_check():
        print("健康检查失败，服务可能未启动")
        return
    
    # 创建测试音频文件
    test_file = create_test_audio()
    
    # 测试文件上传转录
    if test_file:
        test_file_upload_transcribe(test_file)
    
    # 测试URL转录（使用一个公开的音频URL）
    test_url = "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav"
    test_url_transcribe(test_url)
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()
