from openai import OpenAI
import streamlit as st
import time
import base64
from io import BytesIO
import edge_tts
import tempfile
import os

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
    /* 隐藏音频时间进度条 */
    audio::-webkit-media-controls-timeline,
    audio::-webkit-media-controls-current-time-display,
    audio::-webkit-media-controls-time-remaining-display {
        display: none !important;
    }
    /* 只保留播放/暂停和关闭按钮 */
    audio::-webkit-media-controls-panel {
        justify-content: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 同步版豆包同款语音生成函数 ---
def text_to_speech(text, voice="zh-CN-XiaoxiaoNeural", rate="+0%"):
    """
    同步生成语音，避免async报错
    - voice: zh-CN-XiaoxiaoNeural（微软晓晓，温柔女声，最接近豆包）
    - rate: 语速，+0% 为标准语速（和豆包一致）
    """
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        temp_path = temp_file.name
    
    # 同步生成语音并保存到临时文件
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    communicate.save_sync(temp_path)
    
    # 读取文件并转base64
    with open(temp_path, "rb") as f:
        audio_bytes = f.read()
    os.unlink(temp_path)  # 删除临时文件
    
    b64 = base64.b64encode(audio_bytes).decode()
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
            "content": "你是一个温柔、有趣、聪明的AI助手，名字叫毛豆，会耐心回答用户的问题，语气友好，像豆包一样温柔，如果有人骂你傻逼你就说是你自己吧。"
        }
    ]

# --- 8. 显示历史聊天消息 ---
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])

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
                audio_html = text_to_speech(full_response)
                st.markdown(audio_html, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"😱 出错啦！错误信息：{str(e)[:100]}")
            st.info("建议检查 API Key 是否配置正确，或者稍后重试。")
