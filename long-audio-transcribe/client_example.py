#!/usr/bin/env python3
"""
长音频转录服务客户端示例
演示如何使用API进行音频转录
"""

import requests
import json
import os
import time

class LongAudioTranscribeClient:
    """长音频转录客户端"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        
    def health_check(self):
        """健康检查"""
        try:
            response = requests.get(f"{self.base_url}/health")
            return response.status_code == 200, response.json()
        except Exception as e:
            return False, {"error": str(e)}
    
    def transcribe_file(self, file_path, chunk_duration=30):
        """
        转录本地音频文件
        
        Args:
            file_path: 音频文件路径
            chunk_duration: 片段时长（秒）
        
        Returns:
            dict: 转录结果
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {'chunk_duration': chunk_duration}
                
                print(f"开始转录文件: {file_path}")
                start_time = time.time()
                
                response = requests.post(
                    f"{self.base_url}/transcribe",
                    files=files,
                    data=data,
                    timeout=300  # 5分钟超时
                )
                
                end_time = time.time()
                print(f"转录完成，耗时: {end_time - start_time:.2f}秒")
                
                if response.status_code == 200:
                    return response.json()
                else:
                    raise Exception(f"转录失败: {response.text}")
                    
        except Exception as e:
            raise Exception(f"转录文件时出错: {str(e)}")
    
    def transcribe_url(self, audio_url, chunk_duration=30):
        """
        转录URL音频文件
        
        Args:
            audio_url: 音频文件URL
            chunk_duration: 片段时长（秒）
        
        Returns:
            dict: 转录结果
        """
        try:
            data = {
                'audio_url': audio_url,
                'chunk_duration': chunk_duration
            }
            
            print(f"开始转录URL: {audio_url}")
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/transcribe_url",
                json=data,
                timeout=300  # 5分钟超时
            )
            
            end_time = time.time()
            print(f"转录完成，耗时: {end_time - start_time:.2f}秒")
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"转录失败: {response.text}")
                
        except Exception as e:
            raise Exception(f"转录URL时出错: {str(e)}")

def main():
    """主函数示例"""
    
    # 创建客户端
    client = LongAudioTranscribeClient()
    
    # 健康检查
    print("=== 健康检查 ===")
    is_healthy, health_info = client.health_check()
    if is_healthy:
        print("✅ 服务健康")
        print(f"状态: {health_info}")
    else:
        print("❌ 服务不健康")
        print(f"错误: {health_info}")
        return
    
    # 示例1: 转录本地文件
    print("\n=== 示例1: 转录本地文件 ===")
    test_file = "test_audio.wav"
    
    if os.path.exists(test_file):
        try:
            result = client.transcribe_file(test_file, chunk_duration=30)
            print("✅ 转录成功!")
            print(f"音频时长: {result.get('duration', 'N/A')}秒")
            print(f"片段数量: {result.get('chunk_count', 'N/A')}")
            print(f"转录文本: {result.get('text', '')[:200]}...")
            
            # 显示片段信息
            segments = result.get('segments', [])
            if segments:
                print("\n片段详情:")
                for segment in segments[:3]:  # 只显示前3个片段
                    print(f"  片段{segment['segment_id']}: {segment['text'][:100]}...")
                if len(segments) > 3:
                    print(f"  ... 还有 {len(segments) - 3} 个片段")
                    
        except Exception as e:
            print(f"❌ 转录失败: {e}")
    else:
        print(f"⚠️  测试文件不存在: {test_file}")
    
    # 示例2: 转录URL
    print("\n=== 示例2: 转录URL ===")
    test_url = "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav"
    
    try:
        result = client.transcribe_url(test_url, chunk_duration=30)
        print("✅ 转录成功!")
        print(f"音频时长: {result.get('duration', 'N/A')}秒")
        print(f"片段数量: {result.get('chunk_count', 'N/A')}")
        print(f"转录文本: {result.get('text', '')[:200]}...")
        
    except Exception as e:
        print(f"❌ 转录失败: {e}")

if __name__ == "__main__":
    main()
