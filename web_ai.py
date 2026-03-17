from openai import OpenAI
import streamlit as st
import time

# --- 1. 页面基础配置（优化移动端适配与主题） ---
st.set_page_config(
    page_title="我的AI聊天机器人",
    page_icon="✨", # 改个更闪亮的图标
    layout="wide", # 宽屏模式，看着更舒服
    initial_sidebar_state="expanded" # 默认展开侧边栏
)

# --- 2. 自定义 CSS 样式（主打深色质感，告别灰白） ---
# 这一段是美化的核心，让界面看起来更高级
st.markdown("""
    <style>
    /* 全局背景色 */
    .stApp {
        background: linear-gradient(160deg, #0b1020 0%, #10152b 100%);
    }
    /* 消息气泡样式 */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 12px;
        margin-bottom: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    /* 用户消息气泡特殊颜色 */
    [data-testid="stChatMessage"][data-testid="stChatMessage"] {
        background: linear-gradient(90deg, rgba(63,94,251,0.2) 0%, rgba(177,49,253,0.2) 100%);
    }
    /* 输入框区域 */
    .stChatInputContainer {
        background-color: rgba(30, 30, 60, 0.8);
        border-radius: 12px;
        padding: 8px;
    }
    /* 标题美化 */
    .main-title {
        font-size: 2rem;
        color: #FFFFFF;
        text-align: center;
        font-weight: 800;
        margin-bottom: 20px;
        text-shadow: 0 0 15px rgba(114, 137, 218, 0.5);
    }
    /* 滚动条美化 */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-thumb {
        background-color: #444;
        border-radius: 3px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 连接 SiliconFlow API（保留你的原配置） ---
# 增加了超时设置，防止网络慢时卡住
client = OpenAI(
    api_key=st.secrets["SILICONFLOW_API_KEY"],
    base_url="https://api.siliconflow.cn/v1",
    timeout=60.0
)

# --- 4. 侧边栏设置（增加可调参数，更灵活） ---
with st.sidebar:
    st.title("⚙️ 对话设置")
    st.divider()
    
    # 温度参数：控制创意度
    temperature = st.slider("回答创意度", 0.0, 1.0, 0.7, 0.05)
    st.caption("数值越高越创意，越低越严谨。")
    
    # 最大长度参数
    max_tokens = st.slider("回答最大长度", 512, 4096, 2048, 128)
    st.caption("限制AI回复的字数。")
    
    st.divider()
    # 清空对话按钮
    if st.button("🗑️ 清空当前对话"):
        if "messages" in st.session_state:
            st.session_state.messages = [st.session_state.messages[0]] # 保留系统提示
        st.success("对话已清空！")
        time.sleep(0.5)
        st.rerun() # 刷新页面

# --- 5. 主界面标题 ---
st.markdown('<h1 class="main-title">🚀 我的免费公网AI助手</h1>', unsafe_allow_html=True)

# --- 6. 初始化聊天记录（保留你的逻辑） ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": "你是一个温柔、有趣、聪明的AI助手，会耐心回答用户的问题，语气友好。"
        }
    ]

# --- 7. 显示历史聊天消息 ---
for msg in st.session_state.messages:
    if msg["role"] != "system":  # 不显示系统提示词
        with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])

# --- 8. 底部输入框 & 流式输出（核心逻辑优化） ---
if user_input := st.chat_input("想聊点什么？"):
    # 1. 显示用户发送的消息
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 2. 调用 AI 并流式输出回复
    with st.chat_message("assistant", avatar="🤖"):
        try:
            # 显示加载动画，提升等待体验
            with st.spinner("AI 正在思考中... ⏳"):
                response_stream = client.chat.completions.create(
                    model="Qwen/Qwen2.5-7B-Instruct",
                    messages=st.session_state.messages,
                    stream=True,
                    temperature=temperature, # 使用滑块参数
                    max_tokens=max_tokens     # 使用滑块参数
                )
                # 使用 write_stream 实现打字机效果
                full_response = st.write_stream(response_stream)
            
            # 3. 把 AI 回复存入聊天记录
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            # 增加异常处理，报错时给友好提示
            st.error(f"😱 出错啦！错误信息：{str(e)[:100]}")
            st.info("建议检查 API Key 是否配置正确，或者稍后重试。")
