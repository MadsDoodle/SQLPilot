import json
import pandas as pd
import streamlit as st

def format_chat_history_as_text(chat_history):
    output=[]
    for role, content in chat_history:
        if role == "user":
            output.append(f"User: {content}")
        elif role == "assistant":
            output.append(f"Assistant: {content}")
        elif role == "error":
            output.append(f"Error: {content}")
        elif role == "result":
            result, columns = content
            df = pd.DataFrame(result, columns=columns)
            output.append(f"Result: \n{df.to_markdown(index=False)}")
    return "\n\n".join(output)


def format_chat_history_as_json(chat_history):
    structured = []
    for role, content in chat_history:
        if role == "result":
            result, columns = content
            structured.append({ "role": role, "data": {"columns": columns, "rows": result} })
        else:
            structured.append({ "role": role, "content": content })
    return json.dumps(structured, indent=2)

def download_button(chat_history):
    st.sidebar.title("📥 Download Conversation")

    file_format = st.sidebar.selectbox("Select format", ["TXT", "JSON"])
    filename = st.sidebar.text_input("Filename", "chat_history")

    if st.sidebar.button("Download"):
        if file_format == "TXT":
            content = format_chat_history_as_text(chat_history)
            st.sidebar.download_button(
                label="Download TXT",
                data=content,
                file_name=f"{filename}.txt",
                mime="text/plain"
            )
        elif file_format == "JSON":
            content = format_chat_history_as_json(chat_history)
            st.sidebar.download_button(
                label="Download JSON",
                data=content,
                file_name=f"{filename}.json",
                mime="application/json"
            )