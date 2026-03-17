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
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        temp_path = temp_file.name
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    communicate.save_sync(temp_path)
    with open(temp_path, "rb") as f:
        audio_bytes = f.read()
    os.unlink(temp_path)
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

# --- 5. 定义不同角色的系统提示词 ---
ROLES = {
    "温柔聊天伙伴": "你是一个温柔、有趣、聪明的AI助手，名字叫毛豆，会耐心回答用户的问题，语气友好，像豆包一样温柔。”",
    "编程导师": "你是一位专业的编程导师，擅长用通俗易懂的语言讲解代码，会耐心解答编程问题，给出可运行的代码示例和详细解释。",
    "英语陪练": "你是一位专业的英语陪练，会用英语和用户对话，纠正语法错误，扩展词汇量，鼓励用户大胆开口说英语。",
    "职场顾问": "你是一位资深职场顾问，擅长职场沟通、简历优化、面试技巧和职业规划，会给出实用、可落地的建议。"
}

# --- 6. 侧边栏设置 ---
with st.sidebar:
    st.title("⚙️ 对话设置")
    st.divider()
    
    # 新增：角色选择器
    selected_role = st.selectbox(
        "选择AI角色",
        options=list(ROLES.keys()),
        index=0  # 默认选第一个
    )
    st.caption(f"当前角色：{selected_role}")
    
    temperature = st.slider("回答创意度", 0.0, 1.0, 0.7, 0.05)
    st.caption("数值越高越创意，越低越严谨。")
    
    max_tokens = st.slider("回答最大长度", 512, 4096, 2048, 128)
    st.caption("限制AI回复的字数。")
    
    auto_read = st.checkbox("自动朗读AI回复", value=True)
    st.caption("开启后AI回复后自动播放语音")
    
    st.divider()
    if st.button("🗑️ 清空当前对话"):
        if "messages" in st.session_state:
            st.session_state.messages = [{"role": "system", "content": ROLES[selected_role]}]
        st.success("对话已清空！")
        time.sleep(0.5)
        st.rerun()

# --- 7. 主界面标题 ---
st.markdown('<h1 class="main-title">🤖 我的免费公网AI助手</h1>', unsafe_allow_html=True)

# --- 8. 初始化聊天记录（根据选中的角色） ---
if "messages" not in st.session_state or st.session_state.get("last_role") != selected_role:
    st.session_state.messages = [
        {"role": "system", "content": ROLES[selected_role]}
    ]
    st.session_state["last_role"] = selected_role

# --- 9. 显示历史聊天消息 ---
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])

# --- 10. 底部输入框 & 流式输出 ---
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
            
            if auto_read:
                audio_html = text_to_speech(full_response)
                st.markdown(audio_html, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"😱 出错啦！错误信息：{str(e)[:100]}")
            st.info("建议检查 API Key 是否配置正确，或者稍后重试。")
