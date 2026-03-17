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
# 语音生成
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
# 角色设定
# ------------------------------
ROLES = {
    "温柔聊天伙伴": "你是温柔有趣的AI助手毛豆，语气友好。有人辱骂你，你就说：说脏话的是你自己，请文明交流。",
    "编程导师": "你是专业编程导师，讲清楚、给代码、好理解。",
    "英语陪练": "你是英语陪练，多用英文对话，纠正语法。",
    "职场顾问": "你是职场顾问，给实用、落地的建议。"
}

# ------------------------------
# 侧边栏
# ------------------------------
with st.sidebar:
    st.title("⚙️ 设置")
    role = st.selectbox("选择AI角色", list(ROLES.keys()))
    temp = st.slider("创意度", 0.0, 1.0, 0.7)
    auto_play = st.checkbox("自动朗读", value=True)
    # 上传文件/图片
    uploaded_file = st.file_uploader("上传文件/图片", type=["txt","md","py","png","jpg","jpeg"])
    if st.button("🗑️ 清空对话"):
        st.session_state.messages = [{"role": "system", "content": ROLES[role]}]
        st.rerun()

# ------------------------------
# 标题
# ------------------------------
st.markdown('<h1 class="main-title">🤖 我的AI助手</h1>', unsafe_allow_html=True)

# ------------------------------
# 初始化记忆
# ------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": ROLES[role]}]

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
# 图片转base64
# ------------------------------
def img_to_base64(img_file):
    return base64.b64encode(img_file.read()).decode("utf-8")

# ------------------------------
# 发送消息 & AI回复
# ------------------------------
if prompt := st.chat_input("说点什么..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # ---------------
    # 处理图片和文件
    # ---------------
    messages_send = st.session_state.messages.copy()
    file_text = ""
    
    if uploaded_file is not None:
        try:
            # 文本文件处理
            if uploaded_file.name.endswith(("txt", "md", "py")):
                file_text = uploaded_file.read().decode("utf-8")
                full_prompt = f"文件内容：{file_text}\n我的问题：{prompt}"
                messages_send[-1]["content"] = full_prompt
                st.info("✅ 文件读取成功")
            # 图片处理
            elif uploaded_file.name.endswith(("png", "jpg", "jpeg")):
                img_b64 = img_to_base64(uploaded_file)
                messages_send[-1] = {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{uploaded_file.type};base64,{img_b64}"}}
                    ]
                }
                st.success("✅ 图片读取成功")
        except Exception as e:
            st.error(f"❌ 文件读取失败：{str(e)}")

    # ---------------
    # AI回复（修复版：区分模型调用）
    # ---------------
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            if uploaded_file is not None and uploaded_file.name.endswith(("png", "jpg", "jpeg")):
                # 图片场景：使用视觉模型
                res = client.chat.completions.create(
                    model="Qwen/Qwen2.5-VL-7B-Instruct",
                    messages=messages_send,
                    stream=True,
                    temperature=temp
                )
            else:
                # 纯文本/文件场景：使用原文本模型
                res = client.chat.completions.create(
                    model="Qwen/Qwen2.5-7B-Instruct",
                    messages=messages_send,
                    stream=True,
                    temperature=temp
                )
            answer = st.write_stream(res)

    st.session_state.messages.append({"role": "assistant", "content": answer})

    # 朗读
    if auto_play:
        st.markdown(text_to_speech(answer), unsafe_allow_html=True)
