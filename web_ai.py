from openai import OpenAI
import streamlit as st
import base64
import edge_tts
import tempfile
import os

# ------------------------------
# 页面配置
# ------------------------------
st.set_page_config(
    page_title="AI助手",
    page_icon="🤖",
    layout="centered"
)

# ------------------------------
# 界面样式
# ------------------------------
st.markdown("""
<style>
.stApp { background-color:#FFFFFF; }
.stChatMessage { border-radius:12px; padding:12px; margin:5px 0; }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# 语音朗读
# ------------------------------
def text_to_speech(text):
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name
    tts = edge_tts.Communicate(text, voice="zh-CN-XiaoxiaoNeural", rate="+0%")
    tts.save_sync(tmp_path)
    with open(tmp_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    os.unlink(tmp_path)
    return f"""<audio controls autoplay><source src="data:audio/mp3;base64,{b64}">"""

# ------------------------------
# AI连接
# ------------------------------
client = OpenAI(
    api_key=st.secrets["SILICONFLOW_API_KEY"],
    base_url="https://api.siliconflow.cn/v1"
)

# ------------------------------
# 角色设定
# ------------------------------
ROLES = {
    "温柔助手": "你是温柔有礼貌的AI，文明对话，不骂人，耐心回答",
    "编程老师": "你是极简编程老师，只给简单代码，讲大白话",
    "学习助手": "你是学习助手，总结、讲解、答题、简单易懂",
}

# ------------------------------
# 侧边栏
# ------------------------------
with st.sidebar:
    st.title("设置")
    role = st.selectbox("AI角色", list(ROLES.keys()))
    auto_play = st.checkbox("自动朗读", value=True)
    uploaded_file = st.file_uploader("上传图片/文件", type=["png","jpg","jpeg","txt","md","py"])
    if st.button("清空对话"):
        st.session_state.messages = [{"role":"system","content":ROLES[role]}]
        st.rerun()

# ------------------------------
# 记忆初始化
# ------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role":"system","content":ROLES[role]}]

if st.session_state.get("last_role") != role:
    st.session_state.messages = [{"role":"system","content":ROLES[role]}]
    st.session_state["last_role"] = role

# ------------------------------
# 展示聊天
# ------------------------------
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ------------------------------
# 图片转base64（识图核心）
# ------------------------------
def img_to_base64(img_file):
    return base64.b64encode(img_file.read()).decode("utf-8")

# ------------------------------
# 发送消息
# ------------------------------
if prompt := st.chat_input("输入消息"):
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # ---------------
    # 核心：处理图片
    # ---------------
    messages_api = st.session_state.messages.copy()
    if uploaded_file is not None:
        file_type = uploaded_file.type
        # 图片处理
        if "image" in file_type:
            img_b64 = img_to_base64(uploaded_file)
            messages_api[-1] = {
                "role": "user",
                "content": [
                    {"type":"text","text":prompt},
                    {"type":"image_url","image_url":{"url":f"data:{file_type};base64,{img_b64}"}}
                ]
            }
            st.success("📷 图片读取成功")

    # ---------------
    # AI回复
    # ---------------
    with st.chat_message("assistant"):
        with st.spinner("思考中"):
            res = client.chat.completions.create(
                model="Qwen/Qwen2.5-VL-7B-Instruct",
                messages=messages_api,
                stream=True,
                temperature=0.6
            )
            ans = st.write_stream(res)

    st.session_state.messages.append({"role":"assistant","content":ans})

    # 朗读
    if auto_play:
        st.markdown(text_to_speech(ans), unsafe_allow_html=True)
