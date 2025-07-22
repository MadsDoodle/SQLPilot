import streamlit as st
import pandas as pd
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from module.query_engine import get_sql_query
from module.sql_utils import execute_sql_query, get_current_schema
from module.download_utils import download_button

load_dotenv()

st.set_page_config(page_title="Text-to-SQL Chat Assistant", layout="wide")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Sidebar: Table creator
st.sidebar.title(" SQLite Table Creator")
sql_input = st.sidebar.text_area("Enter SQL to create or insert into tables:", height=200)
if st.sidebar.button("Execute SQL"):
    result, _ = execute_sql_query(sql_input)
    if isinstance(result, str) and result.startswith("SQL Error"):
        st.sidebar.error(result)
    else:
        st.sidebar.success("SQL executed successfully!")

# Chat interface
st.title("💬 Text2SQL LLM Chain")
st.markdown("Ask ques about your database in natural language")

user_input = st.chat_input("Ask a question about your data")
if user_input:
    # Append user message
    st.session_state.chat_history.append(("user", user_input))

    # Get current schema dynamically
    schema = get_current_schema()

    # Generate SQL
    with st.spinner("Generating SQL..."):
        sql_query = get_sql_query(user_input, schema)
        st.session_state.chat_history.append(("assistant", sql_query))

    # Execute SQL
    with st.spinner("Running query..."):
        result, columns = execute_sql_query(sql_query)
        if isinstance(result, str) and result.startswith("SQL Error"):
            st.session_state.chat_history.append(("error", result))
        else:
            st.session_state.chat_history.append(("result", (result, columns)))

# Display Chat History
for role, content in st.session_state.chat_history:
    if role == "user":
        with st.chat_message("user"):
            st.markdown(content)
    elif role == "assistant":
        with st.chat_message("assistant"):
            st.code(content, language="sql")
    elif role == "error":
        with st.chat_message("assistant"):
            st.error(content)
    elif role == "result":
        result, columns = content  # from session state

        with st.chat_message("assistant"):
            if isinstance(result, str):  # Error string
                st.error(result)
            elif result:
                try:
                    df = pd.DataFrame(result, columns=columns)
                    st.dataframe(df, use_container_width=True)
                except Exception as e:
                    st.error(f"Data display error: {e}")
            else:
                st.markdown("No results found.")



# download option:
download_button(st.session_state.chat_history)