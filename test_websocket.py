#!/usr/bin/env python3
"""WebSocket连接测试脚本"""

import asyncio
import json
try:
    import websockets
except ImportError:
    print("websockets库未安装，跳过WebSocket测试")
    exit(0)

async def test_websocket():
    """测试WebSocket连接"""
    try:
        # 连接WebSocket
        uri = "ws://localhost:8000/websocket/ws/test_user"
        print(f"连接到: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功")
            
            # 发送测试消息
            test_message = {
                "type": "ping",
                "message": "test"
            }
            await websocket.send(json.dumps(test_message))
            print("📤 发送测试消息")
            
            # 接收响应
            response = await websocket.recv()
            print(f"📥 收到响应: {response}")
            
    except Exception as e:
        print(f"❌ WebSocket测试失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔌 开始WebSocket连接测试")
    result = asyncio.run(test_websocket())
    if result:
        print("✅ WebSocket测试通过")
    else:
        print("❌ WebSocket测试失败")