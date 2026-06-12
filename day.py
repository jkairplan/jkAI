# 综合 AI 工具应用 - 支持函数调用的多工具助手
import streamlit as st
import json
import requests
from datetime import datetime
from openai import OpenAI

# ==================== 配置 ====================
# 请替换为您的有效 API 信息（也可使用环境变量）
API_BASE_URL = "https://aigc-api.aitoolcore.com/api/v1"
API_KEY = "sk-aigc-6d84addde1f7c03f09f5dac558d0e095be33fd23"  # 建议改为您的真实密钥
MODEL_NAME = "qwen3.5-flash"  # 需支持 function calling

client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

# ==================== 工具定义 ====================
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "获取指定城市的实时天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称，如北京"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "default": "celsius"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_news_headlines",
            "description": "获取今日新闻头条",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "enum": ["general", "tech", "sports"], "description": "新闻类别"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "执行数学计算（加减乘除、幂运算等）",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式，如 '2 + 3 * 4'"}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前日期和时间",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {"type": "string", "description": "时区，如 Asia/Shanghai"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "查询股票实时价格（模拟数据）",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "股票代码，如 AAPL, 600036"}
                },
                "required": ["symbol"]
            }
        }
    }
]

# ==================== 工具实现 ====================
def get_current_weather(city, unit="celsius"):
    """模拟天气API，实际可替换为真实服务"""
    # 这里使用免费天气API示例（wttr.in）需要网络
    try:
        url = f"https://wttr.in/{city}?format=j1"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            current = data["current_condition"][0]
            temp = current["temp_C"] if unit == "celsius" else current["temp_F"]
            desc = current["weatherDesc"][0]["value"]
            return f"{city}当前天气：{desc}，温度：{temp}°{'C' if unit=='celsius' else 'F'}"
        else:
            return f"无法获取{city}的天气信息"
    except:
        # 降级模拟数据
        return f"{city}当前天气：晴，25°C"

def get_news_headlines(category="general"):
    """模拟新闻头条，可使用NewsAPI（需注册密钥）"""
    # 为简化演示，返回模拟数据
    headlines = {
        "general": ["科技巨头达成AI安全协议", "国际油价上涨2%", "新一代载人飞船成功试飞"],
        "tech": ["OpenAI发布GPT-5预览版", "量子计算取得突破", "脑机接口临床试验获批"],
        "sports": ["欧冠决赛皇马夺冠", "中国女排3:0战胜对手", "马拉松世界纪录被打破"]
    }
    items = headlines.get(category, headlines["general"])
    return "今日新闻头条：\n" + "\n".join(f"• {item}" for item in items[:3])

def calculate(expression):
    """安全计算数学表达式"""
    try:
        # 限制可用函数和变量，避免危险操作
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误：{str(e)}"

def get_current_time(timezone=None):
    """返回当前时间"""
    now = datetime.now()
    return f"当前时间：{now.strftime('%Y-%m-%d %H:%M:%S')}"

def get_stock_price(symbol):
    """模拟股票价格查询"""
    # 实际可用 yfinance 等库
    mock_prices = {"AAPL": 175.34, "GOOGL": 140.56, "600036": 32.45}
    price = mock_prices.get(symbol.upper(), 100.00)
    return f"股票 {symbol.upper()} 当前价格：${price}"

# 工具名称到函数的映射
tool_functions = {
    "get_current_weather": get_current_weather,
    "get_news_headlines": get_news_headlines,
    "calculate": calculate,
    "get_current_time": get_current_time,
    "get_stock_price": get_stock_price
}

# ==================== 核心对话逻辑 ====================
def call_tool(tool_call):
    """执行工具并返回结果"""
    func_name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    func = tool_functions.get(func_name)
    if func:
        result = func(**args)
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        }
    else:
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": f"未知工具：{func_name}"
        }

# Streamlit UI
st.set_page_config(page_title="多工具AI助手", page_icon="🛠️")
st.title("🛠️ 多工具AI助手")
st.markdown("我可以帮你：查天气 📍、看新闻 📰、算数学 📐、查时间 ⏰、查股票 💹 等。")

# 初始化聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "你是一个有用的助手，可以调用工具来回答用户问题。使用中文回复。"}
    ]

# 显示历史消息（跳过system消息）
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# 用户输入
if prompt := st.chat_input("请说点什么..."):
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # 调用模型（可能多次函数调用）
    with st.chat_message("assistant"):
        # 第一次请求
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=st.session_state.messages,
            tools=tools,
            tool_choice="auto"
        )
        assistant_msg = response.choices[0].message

        # 处理工具调用循环
        while assistant_msg.tool_calls:
            # 将助手的工具调用请求加入消息历史
            st.session_state.messages.append(assistant_msg.model_dump())
            # 执行每个工具调用
            for tool_call in assistant_msg.tool_calls:
                tool_result = call_tool(tool_call)
                st.session_state.messages.append(tool_result)
                # 在UI上展示工具调用过程（可选）
                with st.status(f"正在调用工具：{tool_call.function.name}..."):
                    st.write(f"参数：{tool_call.function.arguments}")
                    st.write(f"结果：{tool_result['content']}")
            # 再次请求模型，传入工具结果
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=st.session_state.messages,
                tools=tools,
                tool_choice="auto"
            )
            assistant_msg = response.choices[0].message

        # 最终文本回复
        final_reply = assistant_msg.content
        if final_reply:
            st.write(final_reply)
            st.session_state.messages.append({"role": "assistant", "content": final_reply})
        else:
            st.write("（助手没有生成回复）")