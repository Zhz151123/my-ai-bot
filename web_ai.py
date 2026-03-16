from openai import OpenAI
import streamlit as st

st.set_page_config(page_title="我的AI机器人", page_icon="🤖")

# 🔥 从 Streamlit Cloud 密钥读取 API Key
client = OpenAI(
    base_url="https://api.siliconflow.cn/v1",
    api_key=st.secrets["SILICONFLOW_API_KEY"]
)

st.title("🤖 我的免费公网AI机器人")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "你是一个聪明、温柔、有趣的AI助手。"}
    ]

for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

prompt = st.chat_input("请输入消息...")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        res = client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct",
            messages=st.session_state.messages,
            temperature=0.7
        )
        reply = res.choices[0].message.content
        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})