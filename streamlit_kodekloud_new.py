import os
import json
import uuid
import base64
from datetime import datetime

import streamlit as st
from openai import OpenAI

##########################################################################
# CONFIG
##########################################################################

st.set_page_config(
    page_title="KodeKloud LLM Playground",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_URL = "https://api.ai.kodekloud.com/v1"

CHAT_FOLDER = "chat_history"

os.makedirs(CHAT_FOLDER, exist_ok=True)

##########################################################################
# MODELS
##########################################################################

MODELS = {
    "Claude Sonnet 5": "claude-sonnet-5",
    "Claude Haiku 4.5": "claude-haiku-4-5-20251001",
    "Claude Opus 4.8": "claude-opus-4-8",
    "Claude Opus 5" : "claude-opus-5",
    "Claude Fable 5": "claude-fable-5",

    "GPT 5.5": "gpt-5.5",
    "GPT 5.4": "gpt-5.4",
    "GPT 5.4 Mini": "gpt-5.4-mini",
    "GPT 5.6 Sol": "gpt-5.6-sol",
    "GPT OSS": "gpt-oss-120b",


    "Gemini 3.5 Flash": "google/gemini-3.5-flash",
    "Gemini 3 Flash Preview": "google/gemini-3-flash-preview",
    "Gemini 3.1 Flash Lite": "google/gemini-3.1-flash-lite",
    "Gemini 3.1 Pro Preview": "google/gemini-3.1-pro-preview",

    "DeepSeek V4 Flash": "deepseek/deepseek-v4-flash",
    "DeepSeek V4 Pro": "deepseek/deepseek-v4-pro",
    "DeepSeek V3.2": "deepseek/deepseek-V3.2",

    "MiniMax M3": "minimax/minimax-m3",
    "MiniMax M2.5": "minimax/MiniMax-M2.5",

    "MiMo V2.5": "xiaomi/MiMo-V2.5",
    "MiMo V2.5 Pro": "xiaomi/MiMo-V2.5-Pro",

    "Moonshot Kimi K2.5": "moonshot/kimi-k2.5",
    "Moonshot Kimi K3": "moonshot/kimi-k3",

    "GLM 5.1": "zai/glm-5.1",
    "Grok 4.3": "xai/grok-4.3"
}

##########################################################################
# HELPERS
##########################################################################

def content_to_text(content):
    """Return plain text from a message 'content' that may be a string
    (old format) or a multimodal parts list (new format)."""

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                return part.get("text", "")

    return ""

##########################################################################
# CSS
##########################################################################

st.markdown("""

<style>

html,
body,
[class*="css"]{
    font-family:Arial;
}

.block-container{

    padding-top:1rem;
    padding-bottom:2rem;
    max-width:1400px;

}

div[data-testid="stSidebar"]{

    width:340px;

}

.chat-card{

    padding:15px;
    border-radius:10px;
    border:1px solid #dcdcdc;
    margin-bottom:15px;

}

.user-msg{

    background:#2563eb;
    color:white;
    padding:14px;
    border-radius:12px;
    margin-top:15px;
    margin-bottom:15px;

}

.assistant-msg{

    background:#f5f5f5;
    padding:14px;
    border-radius:12px;
    margin-bottom:20px;

}

.response-box{

    border:1px solid #ddd;
    padding:18px;
    border-radius:10px;
    background:#fafafa;

}

.stButton>button{

    width:100%;
    height:48px;
    border-radius:10px;
    font-size:18px;

}

</style>

""", unsafe_allow_html=True)

##########################################################################
# SESSION STATE
##########################################################################

defaults = {

    "current_chat":None,

    "messages":[],

    "processing":False,

    "system_prompt":"",

    "temperature":0.2,

    "model":"Claude Sonnet 5",

    "memory":True,

    "thinking":False,

    "reasoning_effort":"medium",

    "last_reasoning":""

}

for k,v in defaults.items():

    if k not in st.session_state:

        st.session_state[k]=v

##########################################################################
# CHAT UTILITIES
##########################################################################

def create_chat():

    chat_id=str(uuid.uuid4())

    data={

        "id":chat_id,

        "title":"New Chat",

        "created":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "model":"Claude Sonnet 5",

        "messages":[],

        "system_prompt":"",

        "memory":True

    }

    path=os.path.join(CHAT_FOLDER,f"{chat_id}.json")

    with open(path,"w",encoding="utf-8") as f:

        json.dump(data,f,indent=4)

    return chat_id


def save_chat():

    if st.session_state.current_chat is None:

        return

    path=os.path.join(

        CHAT_FOLDER,

        f"{st.session_state.current_chat}.json"

    )

    if os.path.exists(path):

        with open(path,"r",encoding="utf-8") as f:

            data=json.load(f)

    else:

        data={}

    data["messages"]=st.session_state.messages
    data["model"]=st.session_state.model
    data["system_prompt"]=st.session_state.system_prompt
    data["memory"]=st.session_state.memory

    if len(st.session_state.messages)>0:

        first=content_to_text(st.session_state.messages[0]["content"])

        title=first.replace("\n"," ")

        if len(title)>40:

            title=title[:40]+"..."

        if not title.strip():

            title="New Chat"

        data["title"]=title

    with open(path,"w",encoding="utf-8") as f:

        json.dump(data,f,indent=4)


def load_chat(chat_id):

    path=os.path.join(CHAT_FOLDER,f"{chat_id}.json")

    with open(path,"r",encoding="utf-8") as f:

        data=json.load(f)

    st.session_state.current_chat=chat_id
    st.session_state.messages=data.get("messages",[])
    st.session_state.model=data.get("model","Claude Sonnet 5")
    st.session_state.system_prompt=data.get("system_prompt","")
    st.session_state.memory=data.get("memory",True)


def list_chats():

    chats=[]

    for file in os.listdir(CHAT_FOLDER):

        if file.endswith(".json"):

            with open(os.path.join(CHAT_FOLDER,file),"r",encoding="utf-8") as f:

                data=json.load(f)

            chats.append(data)

    chats.sort(

        key=lambda x:x["created"],

        reverse=True

    )

    return chats


def delete_chat(chat_id):

    path=os.path.join(CHAT_FOLDER,f"{chat_id}.json")

    if os.path.exists(path):

        os.remove(path)

##########################################################################
# INITIAL CHAT
##########################################################################

if st.session_state.current_chat is None:

    chats = list_chats()

    if len(chats) == 0:

        st.session_state.current_chat = create_chat()

    else:

        st.session_state.current_chat = chats[0]["id"]

    load_chat(st.session_state.current_chat)

##########################################################################
# SIDEBAR
##########################################################################

with st.sidebar:

    st.title("🤖 KodeKloud")

    st.caption("LLM Playground")

    st.divider()

    ############################################################
    # NEW CHAT
    ############################################################

    if st.button("➕  New Chat"):

        new_chat = create_chat()

        st.session_state.current_chat = new_chat

        st.session_state.messages = []

        st.session_state.system_prompt = ""

        st.session_state.memory = True

        st.rerun()

    st.divider()

    ############################################################
    # API KEY
    ############################################################

    api_key = st.text_input(

        "API Key",

        type="password",

        placeholder="Enter API Key"

    )

    ############################################################
    # MODEL
    ############################################################

    model_names = list(MODELS.keys())

    current_index = 0

    if st.session_state.model in model_names:

        current_index = model_names.index(

            st.session_state.model

        )

    selected_model = st.selectbox(

        "Model",

        model_names,

        index=current_index

    )

    st.session_state.model = selected_model

    ############################################################
    # TEMPERATURE
    ############################################################

    st.session_state.temperature = st.slider(

        "Temperature",

        min_value=0.0,

        max_value=1.0,

        value=float(st.session_state.temperature),

        step=0.05

    )

    ############################################################
    # MEMORY
    ############################################################

    st.session_state.memory = st.toggle(

        "Conversation Memory",

        value=st.session_state.memory,

        help="If disabled every request starts fresh."

    )

    ############################################################
    # THINKING / REASONING
    ############################################################

    st.session_state.thinking = st.toggle(

        "🧠 Extended Thinking",

        value=st.session_state.thinking,

        help="Ask reasoning-capable models to think before answering."

    )

    if st.session_state.thinking:

        st.session_state.reasoning_effort = st.select_slider(

            "Thinking Effort",

            options=["low", "medium", "high"],

            value=st.session_state.reasoning_effort

        )

    st.divider()

    ############################################################
    # CHAT HISTORY
    ############################################################

    st.subheader("💬 Chats")

    chats = list_chats()

    if len(chats) == 0:

        st.info("No Chats")

    else:

        for chat in chats:

            c1, c2 = st.columns([8,1])

            with c1:

                if st.button(

                    f"🗨️ {chat['title']}",

                    key=chat["id"],

                    use_container_width=True

                ):

                    load_chat(chat["id"])

                    st.rerun()

            with c2:

                if st.button(

                    "🗑️",

                    key="delete_"+chat["id"]

                ):

                    delete_chat(chat["id"])

                    st.session_state.current_chat = None

                    st.rerun()

##########################################################################
# MAIN HEADER
##########################################################################

st.title("🤖 KodeKloud LLM Playground")

st.caption(
    "OpenAI Compatible Interface | ChatGPT Style"
)

##########################################################################
# SYSTEM PROMPT
##########################################################################

st.subheader("System Prompt (Optional)")

system_prompt = st.text_area(

    "",

    value=st.session_state.system_prompt,

    height=180,

    placeholder="Optional system prompt..."

)

st.session_state.system_prompt = system_prompt

##########################################################################
# USER PROMPT
##########################################################################

st.subheader("User Prompt")

user_prompt = st.text_area(

    "",

    height=220,

    placeholder="Ask anything..."

)

##########################################################################
# FILES
##########################################################################

uploaded_files = st.file_uploader(

    "Upload Files (Maximum 3)",

    accept_multiple_files=True

)

if uploaded_files:

    if len(uploaded_files) > 3:

        st.error("Maximum 3 files allowed.")

        st.stop()

    st.success(

        f"{len(uploaded_files)} file(s) selected"

    )

    for file in uploaded_files:

        size = round(file.size / 1024,2)

        st.caption(

            f"📄 {file.name}   ({size} KB)"

        )

##########################################################################
# SUBMIT
##########################################################################

submit = st.button(

    "🚀 Submit",

    disabled=st.session_state.processing,

    use_container_width=True

)

##########################################################################
# BUILD USER MESSAGE
##########################################################################

def build_user_message():

    # No files -> keep it as a simple string (original behavior)
    if not uploaded_files:

        return user_prompt

    # With files -> build a multimodal "parts" list.
    # The first part is always the text prompt.
    parts = [{"type": "text", "text": user_prompt}]

    for file in uploaded_files:

        data = file.read()

        mime = file.type or ""

        # ---- IMAGES (PNG / JPG / etc.) ----
        if mime.startswith("image/"):

            b64 = base64.b64encode(data).decode("utf-8")

            parts.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime};base64,{b64}"
                    }
                }
            )

        # ---- PDF ----
        elif mime == "application/pdf":

            b64 = base64.b64encode(data).decode("utf-8")

            parts.append(
                {
                    "type": "file",
                    "file": {
                        "filename": file.name,
                        "file_data": f"data:application/pdf;base64,{b64}"
                    }
                }
            )

        # ---- TEXT-LIKE FILES (txt / md / py / csv ...) ----
        else:

            try:

                text = data.decode("utf-8", errors="ignore")

            except:

                text = str(data)

            parts[0]["text"] += f"""

================================================

FILE NAME : {file.name}

================================================

{text}

"""

    return parts

##########################################################################
# BUILD MESSAGE LIST
##########################################################################

def build_messages(user_message):

    messages = []

    # Optional System Prompt
    if st.session_state.system_prompt.strip():

        messages.append(
            {
                "role": "system",
                "content": st.session_state.system_prompt
            }
        )

    # Conversation Memory
    if st.session_state.memory:

        for msg in st.session_state.messages:

            messages.append(msg)

    # Latest User Message
    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    return messages


##########################################################################
# CALL LLM
##########################################################################

def call_llm(user_message):

    client = OpenAI(

        api_key=api_key,

        base_url=BASE_URL

    )

    # Build kwargs so we only send the thinking option when it is ON.
    # (Sending it unconditionally could break models that don't support it.)
    kwargs = {
        "model": MODELS[st.session_state.model],
        "temperature": st.session_state.temperature,
        "messages": build_messages(user_message),
    }

    if st.session_state.thinking:

        kwargs["reasoning_effort"] = st.session_state.reasoning_effort

    response = client.chat.completions.create(**kwargs)

    msg = response.choices[0].message

    # Some providers return the thinking trace on a separate field.
    # OpenAI hides it, but Claude / DeepSeek style proxies often expose it.
    reasoning = (
        getattr(msg, "reasoning_content", None)
        or getattr(msg, "reasoning", None)
        or ""
    )

    st.session_state.last_reasoning = reasoning or ""

    return msg.content


##########################################################################
# RENDER CHAT
##########################################################################

st.divider()

st.subheader("Conversation")

if len(st.session_state.messages) == 0:

    st.info("Start a conversation...")

else:

    for message in st.session_state.messages:

        if message["role"] == "user":

            with st.chat_message("user"):

                st.markdown(content_to_text(message["content"]))

        else:

            with st.chat_message("assistant"):

                text = content_to_text(message["content"])

                try:

                    parsed = json.loads(text)

                    st.json(parsed)

                except:

                    st.markdown(text)

##########################################################################
# PROCESS SUBMIT
##########################################################################

if submit:

    if api_key.strip() == "":

        st.error("API Key required.")

        st.stop()

    if user_prompt.strip() == "":

        st.warning("Please enter a prompt.")

        st.stop()

    st.session_state.processing = True

    user_message = build_user_message()

    # Show user immediately

    with st.chat_message("user"):

        st.markdown(content_to_text(user_message))

    with st.spinner("Thinking..."):

        try:

            answer = call_llm(user_message)

        except Exception as e:

            st.session_state.processing = False

            st.error(str(e))

            st.stop()

    with st.chat_message("assistant"):

        if st.session_state.thinking and st.session_state.last_reasoning:

            with st.expander("🧠 Thinking"):

                st.markdown(st.session_state.last_reasoning)

        try:

            parsed = json.loads(answer)

            st.json(parsed)

        except:

            st.markdown(answer)

    ##################################################################
    # SAVE MEMORY
    ##################################################################

    st.session_state.messages.append(

        {

            "role":"user",

            "content":user_message

        }

    )

    st.session_state.messages.append(

        {

            "role":"assistant",

            "content":answer

        }

    )

    save_chat()

    st.session_state.processing = False

    st.rerun()


##########################################################################
# FOOTER
##########################################################################

st.divider()

col1,col2,col3 = st.columns(3)

with col1:

    st.caption(f"💬 Chats : {len(list_chats())}")

with col2:

    st.caption(f"🧠 Memory : {'ON' if st.session_state.memory else 'OFF'}")

with col3:

    st.caption(f"🤖 {st.session_state.model}")

##########################################################################
# EXTRA UTILITIES
##########################################################################

def export_markdown():

    text = ""

    for msg in st.session_state.messages:

        if msg["role"] == "user":

            text += "\n\n# USER\n\n"

        else:

            text += "\n\n# ASSISTANT\n\n"

        text += content_to_text(msg["content"])

        text += "\n"

    return text


def clear_chat():

    st.session_state.messages = []

    save_chat()


def rename_chat(new_title):

    if st.session_state.current_chat is None:

        return

    path = os.path.join(

        CHAT_FOLDER,

        f"{st.session_state.current_chat}.json"

    )

    if not os.path.exists(path):

        return

    with open(path, "r", encoding="utf-8") as f:

        data = json.load(f)

    data["title"] = new_title

    with open(path, "w", encoding="utf-8") as f:

        json.dump(data, f, indent=4)


##########################################################################
# SIDEBAR TOOLS
##########################################################################

with st.sidebar:

    st.divider()

    st.subheader("Utilities")

    ############################################################

    search_text = st.text_input(

        "Search Chats"

    )

    ############################################################

    if search_text:

        st.caption("Matching Chats")

        chats = list_chats()

        for c in chats:

            if search_text.lower() in c["title"].lower():

                if st.button(

                    c["title"],

                    key="search_"+c["id"]

                ):

                    load_chat(c["id"])

                    st.rerun()

    ############################################################

    new_title = st.text_input(

        "Rename Current Chat"

    )

    if st.button(

        "Rename Chat"

    ):

        if new_title.strip():

            rename_chat(new_title)

            st.success("Renamed")

            st.rerun()

    ############################################################

    if st.button(

        "🧹 Clear Conversation"

    ):

        clear_chat()

        st.rerun()

##########################################################################
# EXPORT
##########################################################################

if len(st.session_state.messages) > 0:

    st.divider()

    c1,c2,c3 = st.columns(3)

    ############################################################

    with c1:

        st.download_button(

            "⬇ Download Markdown",

            data=export_markdown(),

            file_name="conversation.md",

            mime="text/markdown",

            use_container_width=True

        )

    ############################################################

    with c2:

        st.download_button(

            "⬇ Download Text",

            data=export_markdown(),

            file_name="conversation.txt",

            mime="text/plain",

            use_container_width=True

        )

    ############################################################

    with c3:

        if st.button(

            "🔄 Retry Last Prompt",

            use_container_width=True

        ):

            if len(st.session_state.messages)>=2:

                last=None

                for m in reversed(st.session_state.messages):

                    if m["role"]=="user":

                        last=m["content"]

                        break

                if last:

                    with st.spinner("Retrying..."):

                        ans=call_llm(last)

                    st.session_state.messages.append(

                        {

                            "role":"assistant",

                            "content":ans

                        }

                    )

                    save_chat()

                    st.rerun()

##########################################################################
# RESPONSE TOOLS
##########################################################################

if len(st.session_state.messages)>0:

    st.divider()

    st.subheader("Latest Response")

    latest=None

    for msg in reversed(st.session_state.messages):

        if msg["role"]=="assistant":

            latest=content_to_text(msg["content"])

            break

    if latest:

        st.code(

            latest,

            language="markdown"

        )

        st.download_button(

            "Download Latest Response",

            latest,

            file_name="response.md",

            mime="text/plain"

        )

##########################################################################
# CHAT STATISTICS
##########################################################################

st.divider()

user_count=0
assistant_count=0
characters=0

for m in st.session_state.messages:

    if m["role"]=="user":

        user_count+=1

    else:

        assistant_count+=1

    characters+=len(content_to_text(m["content"]))

c1,c2,c3,c4=st.columns(4)

c1.metric(

    "User Messages",

    user_count

)

c2.metric(

    "Assistant Messages",

    assistant_count

)

c3.metric(

    "Characters",

    characters

)

c4.metric(

    "Current Model",

    st.session_state.model

)

##########################################################################
# OPTIONAL STREAMING (ChatGPT Typing Effect)
##########################################################################

def stream_llm(user_message):

    client = OpenAI(
        api_key=api_key,
        base_url=BASE_URL
    )

    stream_kwargs = {
        "model": MODELS[st.session_state.model],
        "temperature": st.session_state.temperature,
        "messages": build_messages(user_message),
        "stream": True,
    }

    if st.session_state.thinking:

        stream_kwargs["reasoning_effort"] = st.session_state.reasoning_effort

    stream = client.chat.completions.create(**stream_kwargs)

    placeholder = st.empty()

    full_response = ""

    for chunk in stream:

        try:

            delta = chunk.choices[0].delta.content

            if delta:

                full_response += delta

                placeholder.markdown(full_response + "▌")

        except:

            pass

    placeholder.markdown(full_response)

    return full_response


##########################################################################
# STREAMING BUTTON
##########################################################################

st.divider()

streaming = st.checkbox(
    "Use Streaming Response",
    value=True
)




##########################################################################
# QUICK COPY BOX
##########################################################################

if len(st.session_state.messages):

    last_response = ""

    for msg in reversed(st.session_state.messages):

        if msg["role"] == "assistant":

            last_response = content_to_text(msg["content"])

            break

    if last_response:

        with st.expander("Latest Response"):

            st.text_area(
                "Copy Response",
                value=last_response,
                height=250
            )


##########################################################################
# ABOUT
##########################################################################

st.divider()

st.caption(
    "Built with Streamlit + OpenAI SDK + KodeKloud OpenAI Compatible API"
)
