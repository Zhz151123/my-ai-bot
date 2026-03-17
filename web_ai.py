from openai import OpenAI
import streamlit as st
import time
import base64
from io import BytesIO
import edge_tts
import tempfile
import os

# ------------------------------
# 页面配置
# ------------------------------
st.set_page_config(
    page_title="我的AI助手",
    page_icon="🤖",
    layout="centered"
)

# ------------------------------
# 白色简洁样式
# ------------------------------
st.markdown("""
<style>
.stApp { background-color: #FFFFFF; }
.stChatMessage {
    background-color: #F7F9FC;
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 8px;
    border: 1px solid #E2E8F0;
}
[data-testid="stChatMessage"][data-testid="user"] {
    background-color: #E6F7FF;
}
[data-testid="stChatMessage"][data-testid="assistant"] {
    background-color: #F6FFED;
}
.stChatInputContainer {
    background-color: #FFFFFF;
    border: 1px solid #D9D9D9;
    border-radius: 8px;
}
.main-title {
    font-size: 1.8rem;
    color: #262626;
    text-align: center;
    font-weight: 600;
}
audio::-webkit-media-controls-timeline,
audio::-webkit-media-controls-current-time-display,
audio::-webkit-media-controls-time-remaining-display {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------
# 语音生成（豆包同款女声）
# ------------------------------
def text_to_speech(text):
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name
    tts = edge_tts.Communicate(text, voice="zh-CN-XiaoxiaoNeural", rate="+0%")
    tts.save_sync(tmp_path)
    with open(tmp_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    os.unlink(tmp_path)
    return f"""<audio controls autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3">"""

# ------------------------------
# 连接AI
# ------------------------------
client = OpenAI(
    api_key=st.secrets["SILICONFLOW_API_KEY"],
    base_url="https://api.siliconflow.cn/v1"
)

# ------------------------------
# 角色设定（你可以自己加）
# ------------------------------
ROLES = {
    "温柔聊天伙伴": "你是温柔有趣的AI助手毛豆，语气友好。有人辱骂你，你就说：说脏话的是你自己，请文明交流。",
    "编程导师": "你是专业编程导师，讲清楚、给代码、好理解。",
    "英语陪练": "你是英语陪练，多用英文对话，纠正语法。",
    "职场顾问": "你是职场顾问，给实用、落地的建议。"
}

# ------------------------------
# 侧边栏设置
# ------------------------------
with st.sidebar:
    st.title("⚙️ 设置")
    role = st.selectbox("选择AI角色", list(ROLES.keys()))
    temp = st.slider("创意度", 0.0, 1.0, 0.7)
    auto_play = st.checkbox("自动朗读", value=True)
    if st.button("🗑️ 清空对话"):
        st.session_state.messages = [{"role": "system", "content": ROLES[role]}]
        st.rerun()

# ------------------------------
# 标题
# ------------------------------
st.markdown('<h1 class="main-title">🤖 我的AI助手</h1>', unsafe_allow_html=True)

# ------------------------------
# 初始化记忆（关键！）
# ------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": ROLES[role]}]

# 切换角色时重置记忆
if st.session_state.get("last_role") != role:
    st.session_state.messages = [{"role": "system", "content": ROLES[role]}]
    st.session_state["last_role"] = role

# ------------------------------
# 显示聊天记录
# ------------------------------
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ------------------------------
# 发送消息 & AI回复
# ------------------------------
if prompt := st.chat_input("说点什么..."):

    # 把用户说的话存进记忆
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI回复
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            res = client.chat.completions.create(
                model="Qwen/Qwen2.5-7B-Instruct",
                messages=st.session_state.messages,  # 把全部记忆发给AI
                stream=True,
                temperature=temp
            )
            answer = st.write_stream(res)

    # 把AI回答也存进记忆
    st.session_state.messages.append({"role": "assistant", "content": answer})

    # 朗读
    if auto_play:
        st.markdown(text_to_speech(answer), unsafe_allow_html=True)
