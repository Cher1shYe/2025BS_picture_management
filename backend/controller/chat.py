# controller/chat.py
from flask import Blueprint, request, jsonify
import asyncio
from openai import OpenAI
import json
import os
import sys
# 引入 MCP 客户端库
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

# DeepSeek 配置
client = OpenAI(
    api_key="sk-44f9c1ff1d724ce7b147f7b63d58f67e", #DeepSeek Key
    base_url="https://api.deepseek.com"
)

# 定义 MCP 服务器的启动参数
# 这里我们让主程序去启动同目录下的 mcp_server.py
server_params = StdioServerParameters(
    command=sys.executable, # 使用当前的 python 解释器
    args=["mcp_server.py"], # 脚本路径
    env=None # 如果需要环境变量可以在这里加
)

async def run_chat_session(user_message, history):
    """
    异步函数：负责连接 MCP Server 并与 DeepSeek 交互
    """
    # 建立与 MCP Server 的连接
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 1. 初始化 MCP 会话
            await session.initialize()
            
            # 2. 获取 MCP Server 里的所有工具
            tools_list = await session.list_tools()
            
            # 3. 将 MCP 工具转换为 OpenAI 格式
            openai_tools = []
            for tool in tools_list.tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema # MCP 的 inputSchema 兼容 JSON Schema
                    }
                })

            # 4. 准备发送给 DeepSeek 的消息
            messages = [{"role": "system", "content": "你是一个图片检索助手。如果用户想找图，必须使用工具。"}]
            # 简单处理历史记录
            messages.extend(history) 
            messages.append({"role": "user", "content": user_message})

            # 5. 调用 DeepSeek
            print(">>> 正在请求 DeepSeek...")
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                tools=openai_tools,
                tool_choice="auto" 
            )

            msg = response.choices[0].message
            
            # 6. 处理工具调用
            if msg.tool_calls:
                tool_call = msg.tool_calls[0]
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                print(f">>> DeepSeek 决定调用 MCP 工具: {tool_name} 参数: {tool_args}")
                
                # --- 关键点：通过 MCP 协议调用 mcp_server.py ---
                result = await session.call_tool(tool_name, tool_args)
                
                # result.content 是一个 TextContent 或 ImageContent 的列表
                # 我们之前在 mcp_server 里返回的是 JSON 字符串，所以解析它
                content_text = result.content[0].text
                
                # 解析图片数据
                try:
                    images_data = json.loads(content_text)
                    return {
                        "text": f"找到 {len(images_data)} 张相关图片。",
                        "images": images_data
                    }
                except:
                    # 如果返回的不是 JSON（比如报错信息）
                    return {
                        "text": f"查询结果: {content_text}",
                        "images": []
                    }
            
            # 如果没有调用工具（闲聊）
            return {
                "text": msg.content,
                "images": []
            }

@chat_bp.route('/ask', methods=['POST'])
def chat_entry():
    data = request.json
    user_msg = data.get('message', '')
    history = data.get('history', [])
    
    # 过滤一下 history，防止把之前的图片数据也发给 LLM，太大了
    clean_history = []
    for h in history:
        clean_history.append({
            "role": h['role'],
            "content": h['content'] # 假设前端发来的是纯文本content
        })

    try:
        # Flask 是同步的，这里用 asyncio.run 运行异步逻辑
        # Windows下可能需要设置 selector policy，但在 Linux/Docker 应该没问题
        result = asyncio.run(run_chat_session(user_msg, clean_history))
        return jsonify({"code": 200, "data": result})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"code": 500, "msg": str(e)})
