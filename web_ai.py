from openai import OpenAI
import streamlit as st
import time
import base64
from io import BytesIO
from gtts import gTTS  # 文本转语音库

# --- 1. 页面基础配置 ---
st.set_page_config(
    page_title="我的AI聊天机器人",
    page_icon="🤖",
    layout="centered"
)

# --- 2. 自定义白色极简样式 ---
st.markdown("""
    <style>
    /* 全局白色背景 */
    .stApp {
        background-color: #FFFFFF;
    }
    /* 消息气泡样式 */
    .stChatMessage {
        background-color: #F7F9FC;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 8px;
        border: 1px solid #E2E8F0;
    }
    /* 用户消息气泡 */
    [data-testid="stChatMessage"][data-testid="user"] {
        background-color: #E6F7FF;
        border-color: #91D5FF;
    }
    /* AI消息气泡 */
    [data-testid="stChatMessage"][data-testid="assistant"] {
        background-color: #F6FFED;
        border-color: #B7EB8F;
    }
    /* 输入框区域 */
    .stChatInputContainer {
        background-color: #FFFFFF;
        border: 1px solid #D9D9D9;
        border-radius: 8px;
        padding: 6px;
    }
    /* 标题样式 */
    .main-title {
        font-size: 1.8rem;
        color: #262626;
        text-align: center;
        font-weight: 600;
        margin-bottom: 15px;
    }
    /* 文字颜色 */
    .stMarkdown {
        color: #262626;
    }
    /* 朗读按钮样式 */
    .stButton > button {
        border-radius: 20px;
        background-color: #f0f2f6;
        border: none;
        padding: 5px 12px;
        font-size: 14px;
    }
    .stButton > button:hover {
        background-color: #e6e8eb;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 文本转语音函数 ---
def text_to_speech(text, lang='zh-CN'):
    """将文本转换为语音并返回可播放的HTML音频"""
    tts = gTTS(text=text, lang=lang, slow=False)
    fp = BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    # 转换为base64以便在网页中播放
    b64 = base64.b64encode(fp.read()).decode()
    audio_html = f"""
    <audio controls autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    
    """
    return audio_html

# --- 4. 连接 SiliconFlow API ---
client = OpenAI(
    api_key=st.secrets["SILICONFLOW_API_KEY"],
    base_url="https://api.siliconflow.cn/v1",
    timeout=60.0
)

# --- 5. 侧边栏设置 ---
with st.sidebar:
    st.title("⚙️ 对话设置")
    st.divider()
    
    temperature = st.slider("回答创意度", 0.0, 1.0, 0.7, 0.05)
    st.caption("数值越高越创意，越低越严谨。")
    
    max_tokens = st.slider("回答最大长度", 512, 4096, 2048, 128)
    st.caption("限制AI回复的字数。")
    
    auto_read = st.checkbox("自动朗读AI回复", value=True)
    st.caption("开启后AI回复后自动播放语音")
    
    st.divider()
    if st.button("🗑️ 清空当前对话"):
        if "messages" in st.session_state:
            st.session_state.messages = [st.session_state.messages[0]]
        st.success("对话已清空！")
        time.sleep(0.5)
        st.rerun()

# --- 6. 主界面标题 ---
st.markdown('<h1 class="main-title">🤖 我的免费公网AI助手</h1>', unsafe_allow_html=True)

# --- 7. 初始化聊天记录 ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": "你是一个温柔、有趣、聪明的AI助手，会耐心回答用户的问题，语气友好，你的名字是毛豆。"
        }
    ]

# --- 8. 显示历史聊天消息（带朗读按钮） ---
for i, msg in enumerate(st.session_state.messages):
    if msg["role"] != "system":
        with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])
            # 只给AI的回复添加朗读按钮
            if msg["role"] == "assistant":
                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button("🔊 朗读", key=f"read_{i}"):
                        st.markdown(text_to_speech(msg["content"]), unsafe_allow_html=True)

# --- 9. 底部输入框 & 流式输出 ---
if user_input := st.chat_input("想聊点什么？"):
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant", avatar="🤖"):
        try:
            with st.spinner("AI 正在思考中... ⏳"):
                response_stream = client.chat.completions.create(
                    model="Qwen/Qwen2.5-7B-Instruct",
                    messages=st.session_state.messages,
                    stream=True,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                full_response = st.write_stream(response_stream)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # 如果开启自动朗读，就播放语音
            if auto_read:
                st.markdown(text_to_speech(full_response), unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"😱 出错啦！错误信息：{str(e)[:100]}")
            st.info("建议检查 API Key 是否配置正确，或者稍后重试。")
