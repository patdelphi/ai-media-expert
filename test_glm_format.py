#!/usr/bin/env python3
"""
测试GLM-4.5V API格式的脚本
"""

import json
from app.core.database import SessionLocal
from app.models.video import AIConfig

def test_glm_format():
    """测试GLM API请求格式"""
    db = SessionLocal()
    
    try:
        # 获取AI配置
        ai_config = db.query(AIConfig).first()
        
        if not ai_config:
            print("❌ 没有找到AI配置")
            return
            
        print(f"🤖 AI配置: {ai_config.name} ({ai_config.model})")
        
        # 模拟构建请求体
        prompt = "请分析这个视频的内容，包括视觉元素、音频特征和整体质量。"
        
        if ai_config.model.lower() in ['glm-4.5v', 'glm-4v']:
            # GLM视频模型格式
            request_data = {
                "model": ai_config.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                "max_tokens": ai_config.max_tokens or 4000,
                "temperature": ai_config.temperature or 0.7,
                "stream": True,
                "thinking": {
                    "type": "enabled"
                }
            }
            print("✅ 使用GLM视频模型格式")
        else:
            # 标准OpenAI格式
            request_data = {
                "model": ai_config.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": ai_config.max_tokens or 4000,
                "temperature": ai_config.temperature or 0.7,
                "stream": True
            }
            print("✅ 使用标准OpenAI格式")
        
        # 生成curl命令
        headers = {
            "Authorization": f"Bearer {ai_config.api_key[:10]}...",  # 只显示前10个字符
            "Content-Type": "application/json"
        }
        
        api_url = ai_config.api_base or "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        
        curl_headers = []
        for key, value in headers.items():
            if key.lower() == 'authorization':
                curl_headers.append(f'-H "{key}: Bearer ***"')
            else:
                curl_headers.append(f'-H "{key}: {value}"')
        
        curl_command = f"curl -X POST {api_url} {' '.join(curl_headers)} -d '{json.dumps(request_data, ensure_ascii=False)}'"
        
        print("\n📋 生成的请求数据:")
        print(json.dumps(request_data, indent=2, ensure_ascii=False))
        
        print("\n💻 生成的Curl命令:")
        print(curl_command)
        
        print(f"\n📊 命令长度: {len(curl_command)} 字符")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🧪 开始GLM格式测试...\n")
    test_glm_format()
    print("\n🏁 测试完成")