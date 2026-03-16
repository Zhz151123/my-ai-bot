from openai import OpenAI
import streamlit as st

# 页面配置
st.set_page_config(page_title="我的AI聊天机器人", page_icon="🤖", layout="centered")

# 初始化 SiliconFlow 客户端
client = OpenAI(
    api_key=st.secrets["SILICONFLOW_API_KEY"],
    base_url="https://api.siliconflow.cn/v1"
)

# 页面标题
st.title("🤖 我的免费公网AI助手")

# 初始化聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "你是一个温柔、有趣、聪明的AI助手，会耐心回答用户的问题。"}
    ]

# 显示历史消息
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# 输入框
prompt = st.chat_input("想聊点什么？")

if prompt:
    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 调用 AI 并显示回复
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct",
            messages=st.session_state.messages,
            stream=True,
            temperature=0.7
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
