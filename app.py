import streamlit as st
import zipfile
import os
import tempfile
import networkx as nx
import matplotlib.pyplot as plt
from groq import Groq

# -----------------------------
# API
# -----------------------------
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# -----------------------------
# PAGE SETTINGS
# -----------------------------
st.set_page_config(
    page_title="Codebase Intelligence",
    page_icon="🧠",
    layout="wide"
)

# -----------------------------
# CUSTOM UI
# -----------------------------
st.markdown("""
<style>

.stApp{
background-color:#050505;
color:white;
}

header {visibility:hidden;}
footer {visibility:hidden;}

.metric-card{
background:#0f172a;
padding:20px;
border-radius:12px;
text-align:center;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# AI FUNCTIONS
# -----------------------------

def analyze_repo(files):

    prompt=f"""
You are a senior software architect.

Analyze this repository.

Files:
{files}

Explain:

1. Project purpose
2. Architecture
3. Technologies used
4. Key modules
5. System workflow
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}]
    )

    return response.choices[0].message.content


def ask_repo(question, files):

    context="\n".join(files)

    prompt=f"""
Repository structure:
{context}

Answer question about repository:

{question}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}]
    )

    return response.choices[0].message.content


# -----------------------------
# TITLE
# -----------------------------

st.title("🧠 Codebase Intelligence")

st.write(
"Understand any repository instantly using AI-powered architecture analysis and developer Q&A."
)

# -----------------------------
# FILE UPLOAD
# -----------------------------

uploaded = st.file_uploader("Upload repository ZIP", type=["zip"])

if uploaded:

    with tempfile.TemporaryDirectory() as tmp:

        zip_path=os.path.join(tmp,uploaded.name)

        with open(zip_path,"wb") as f:
            f.write(uploaded.getbuffer())

        with zipfile.ZipFile(zip_path,"r") as zip_ref:
            zip_ref.extractall(tmp)

        total_files=0
        total_dirs=0
        py_files=0
        js_files=0
        md_files=0

        files=[]
        tech=[]

        for root,dirs,fs in os.walk(tmp):

            total_dirs+=len(dirs)
            total_files+=len(fs)

            for file in fs:

                files.append(file)

                lf=file.lower()

                if lf.endswith(".py"):
                    py_files+=1

                if lf.endswith(".js"):
                    js_files+=1

                if lf.endswith(".md"):
                    md_files+=1

                if lf=="dockerfile":
                    tech.append("Docker")

                if lf=="requirements.txt":
                    tech.append("Python Dependencies")

        if py_files>0:
            tech.append("Python")

        tech=list(set(tech))

        # -----------------------------
        # TABS
        # -----------------------------

        tab1,tab2,tab3,tab4=st.tabs(
        ["📊 Dashboard","🧠 Architecture","💬 Chat","📈 Dependency Graph"]
        )

        # -----------------------------
        # DASHBOARD
        # -----------------------------

        with tab1:

            c1,c2,c3,c4=st.columns(4)

            c1.metric("Files",total_files)
            c2.metric("Directories",total_dirs)
            c3.metric("Python Files",py_files)
            c4.metric("Markdown",md_files)

            st.divider()

            col1,col2=st.columns([1,2])

            with col1:

                st.subheader("Detected Stack")

                for t in tech:
                    st.success(t)

            with col2:

                st.subheader("Repository Structure")

                tree=""

                for root,dirs,fs in os.walk(tmp):

                    level=root.replace(tmp,"").count(os.sep)
                    indent=" "*4*level

                    tree+=f"{indent}{os.path.basename(root)}/\n"

                    sub=" "*4*(level+1)

                    for f in fs:
                        tree+=f"{sub}{f}\n"

                st.code(tree[:2000])

        # -----------------------------
        # ARCHITECTURE
        # -----------------------------

        with tab2:

            st.subheader("Architecture Insight")

            if st.button("Generate AI Architecture Analysis"):

                with st.spinner("Analyzing repository..."):

                    try:

                        text="\n".join(files[:1000])

                        result=analyze_repo(text)

                        st.success("Analysis Complete")

                        st.markdown(result)

                    except Exception as e:

                        st.error(e)

        # -----------------------------
        # CHAT
        # -----------------------------

        with tab3:

            st.subheader("Ask AI about this repository")

            if "messages" not in st.session_state:
                st.session_state.messages=[]

            for msg in st.session_state.messages:

                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            prompt=st.chat_input("Ask anything about this repo")

            if prompt:

                st.session_state.messages.append(
                {"role":"user","content":prompt}
                )

                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):

                    with st.spinner("Thinking..."):

                        try:

                            answer=ask_repo(prompt,files[:1000])

                            st.markdown(answer)

                            st.session_state.messages.append(
                            {"role":"assistant","content":answer}
                            )

                        except Exception as e:

                            st.error(e)

        # -----------------------------
        # GRAPH
        # -----------------------------

        with tab4:

            st.subheader("Code Dependency Graph")

            G=nx.Graph()

            for f in files[:50]:
                G.add_node(f)

            for i in range(len(files[:20])-1):
                G.add_edge(files[i],files[i+1])

            fig,ax=plt.subplots()

            nx.draw(G,with_labels=True,node_size=500,font_size=8)

            st.pyplot(fig)