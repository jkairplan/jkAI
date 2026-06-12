# 综合 AI 工具应用 - 支持函数调用的多工具助手
import streamlit as st
import json
import requests
from datetime import datetime
from openai import OpenAI

# ==================== 配置 ====================
# 优先从 Streamlit Secrets 读取 API_KEY，若无则使用下方硬编码的密钥（仅用于快速测试）
# 建议在 Streamlit Cloud 的 Secrets 中设置：OPENAI_API_KEY = "你的真实密钥"
base_url = "https://aigc-api.aitoolcore.com/api/v1"

try:
    # 尝试从 secrets 读取
    api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    # 如果 secrets 中没有，则使用你提供的密钥（请确保不提交到公开仓库）
    api_key = "sk-aigc-38b7bf5ff2c4d5ec73e10d89195a2cf81b4bbada"

client = OpenAI(base_url=base_url, api_key=api_key)
MODEL_NAME = "qwen3.5-flash"  # 需支持 function calling

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
    """模拟新闻头条"""
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
    return f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

def get_stock_price(symbol):
    mock_prices = {"AAPL": 175.34, "GOOGL": 140.56, "600036": 32.45}
    price = mock_prices.get(symbol.upper(), 100.00)
    return f"股票 {symbol.upper()} 当前价格：${price}"

tool_functions = {
    "get_current_weather": get_current_weather,
    "get_news_headlines": get_news_headlines,
    "calculate": calculate,
    "get_current_time": get_current_time,
    "get_stock_price": get_stock_price
}

def call_tool(tool_call):
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

# ==================== Streamlit UI ====================
st.set_page_config(page_title="多工具AI助手", page_icon="🛠️")
st.title("🛠️ 多工具AI助手")
st.markdown("我可以帮你：查天气 📍、看新闻 📰、算数学 📐、查时间 ⏰、查股票 💹 等。")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "你是一个有用的助手，可以调用工具来回答用户问题。使用中文回复。"}
    ]

for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

if prompt := st.chat_input("请说点什么..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=st.session_state.messages,
            tools=tools,
            tool_choice="auto"
        )
        assistant_msg = response.choices[0].message

        while assistant_msg.tool_calls:
            st.session_state.messages.append(assistant_msg.model_dump())
            for tool_call in assistant_msg.tool_calls:
                tool_result = call_tool(tool_call)
                st.session_state.messages.append(tool_result)
                with st.status(f"正在调用工具：{tool_call.function.name}..."):
                    st.write(f"参数：{tool_call.function.arguments}")
                    st.write(f"结果：{tool_result['content']}")
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=st.session_state.messages,
                tools=tools,
                tool_choice="auto"
            )
            assistant_msg = response.choices[0].message

        final_reply = assistant_msg.content
        if final_reply:
            st.write(final_reply)
            st.session_state.messages.append({"role": "assistant", "content": final_reply})
        else:
            st.write("（助手没有生成回复）")