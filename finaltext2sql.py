from dotenv import load_dotenv
import streamlit as st
from module.config import OPENAI_API_KEY

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage    
from langchain_core.runnables import RunnablePassthrough
from langchain_community.utilities import SQLDatabase

from module.query_engine import get_sql_query
from module.sql_utils import execute_sql_query, get_current_schema
from module.download_utils import download_button

from langchain_openai import ChatOpenAI
#from langchain_groq import ChatGroq
load_dotenv()

##============================ for the SQL Playground ===============
import streamlit as st

import pandas as pd

st.set_page_config(page_title="SQL Playground", layout="wide")

# --- Sidebar: SQLite Playground Setup ---
st.sidebar.markdown("## ⚙️ Settings")
use_sqlite = st.sidebar.toggle("Use SQLite Playground", value=True)
if use_sqlite:
    sqlite_name = st.sidebar.text_input("SQLite DB Name (e.g., `mydb.db`)", "playground.db")
    if st.sidebar.button("Create SQLite DB"):
        st.session_state["db_path"] = sqlite_name
        st.sidebar.success(f"SQLite DB `{sqlite_name}` ready.")

# --- SQL Playground Section ---
with st.expander("🛠️ SQL Playground", expanded=True):
    st.subheader("Enter raw SQL commands to interact with your SQLite DB.")

    # --- Raw SQL Text Area ---
    sql_code = st.text_area("Write SQL:", height=150, key="sql_playground")
    
    if st.button("Execute SQL"):
        db_ref = st.session_state.get("db_path", None)
        if not db_ref:
            st.error("Please connect to a database first via the sidebar.")
        else:
            result, columns = execute_sql_query(sql_code)
            if isinstance(result, str) and result.startswith("Error"):
                st.error(result)
            else:
                st.success("SQL executed successfully!")
                if result and columns:
                    df = pd.DataFrame(result, columns=columns)
                    st.dataframe(df)
                else:
                    st.info("Query ran but returned no data.")

    st.markdown("---")
    st.subheader("Ask a question about your database...")

    # --- Natural Language SQL Chat Interface ---
    user_input = st.text_input("Ask a question about your database:", key="natural_query")

    if user_input:
        schema = get_current_schema()
        with st.spinner("Generating SQL..."):
            sql_query = get_sql_query(user_input, schema)
            st.code(sql_query, language="sql")

        with st.spinner("Running query..."):
            result, columns = execute_sql_query(sql_query)
            if isinstance(result, str) and result.startswith("Error"):
                st.error(result)
            else:
                st.success("Query executed successfully!")
                if result and columns:
                    df = pd.DataFrame(result, columns=columns)
                    st.dataframe(df)
                else:
                    st.info("Query ran but returned no data.")



#============================


##2Building the SQL Chain 

##SQL Database Connection
def init_database(user:str, password:str, host:str, port:int, database:str)->SQLDatabase:
    """
    Initialize the SQL database connection.
    """
    db_uri= f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
    return SQLDatabase.from_uri(db_uri)

def get_sql_chain(db):
    """
    Create a SQL chain with the given database.
    """

    template = """
        You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
        Based on the table schema below, write a SQL query that would answer the user's question. Take the conversation history into account.
        
        <SCHEMA>{schema}</SCHEMA>
        
        Conversation History: {chat_history}
        
        Write only the SQL query and nothing else. Do not wrap the SQL query in any other text, not even backticks.
        
        For example:
        Question: which 3 artists have the most tracks?
        SQL Query: SELECT ArtistId, COUNT(*) as track_count FROM Track GROUP BY ArtistId ORDER BY track_count DESC LIMIT 3;
        Question: Name 10 artists
        SQL Query: SELECT Name FROM Artist LIMIT 10;
        
        Your turn:
        
        Question: {question}
        SQL Query:
        """
    prompt = ChatPromptTemplate.from_template(template)

    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=OPENAI_API_KEY,
        temperature=0.0,
        max_tokens=1000,
    )

    def get_schema(_):
        return db.get_table_info()
    
    return (
        RunnablePassthrough().assign(schema=get_schema) 
        | prompt 
        | llm 
        | StrOutputParser()
    )

##3 makingt the response chain which will exceute the SQL query and return the result
def get_response(user_query: str, model_choice: str, temperature: float, max_tokens: int, db: SQLDatabase, chat_history: list):
    sql_chain= get_sql_chain(db)

    template= """
        You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
        Based on the table schema below, question, sql query, and sql response, write a natural language response.
        <SCHEMA>{schema}</SCHEMA>

        Conversation History: {chat_history}
        SQL Query: <SQL>{query}</SQL>
        User question: {question}
        SQL Response: {response}"""
    
    prompt = ChatPromptTemplate.from_template(template)

    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=OPENAI_API_KEY,
        temperature=0.0,
        max_tokens=1000,
    )

    chain = (
        RunnablePassthrough.assign(query=sql_chain).assign(
        schema=lambda _: db.get_table_info(),
        response=lambda vars: db.run(vars["query"]),
        )
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain.invoke({
        "question": user_query,
        "chat_history": chat_history
    })

    

##1 initialise chat hsitory to be shown on the screen

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(
            content="Welcome to the Text2SQL Chat Assistant! Ask me anything about your database.")
    ]

load_dotenv()

st.set_page_config(page_title="Text-to-SQL Chain Assistant", page_icon="🤖", layout="wide")
st.title("Text-to-SQL Chain Assistant")

def sidebar_config():
    with st.sidebar:
        st.subheader("Settings")
        model_choice = st.selectbox("Select Model", ["gpt-4o", "groq-1.5-8b"])
        temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.1)
        max_tokens = st.slider("Max Tokens", 100, 2000, 1000, 100)

        st.text_input("Host", value="localhost", key="Host")
        st.text_input("Port", value="3306", key="Port")
        st.text_input("User", value="root", key="User")
        st.text_input("Password", value="admin", type="password", key="Password")
        st.text_input("Database", value="chinook", key="Database")

        if st.button("Connect to Database"):
            db = init_database(
                user=st.session_state.User,
                password=st.session_state.Password,
                host=st.session_state.Host,
                port=int(st.session_state.Port),
                database=st.session_state.Database
            )
            st.session_state.db = db
            st.success("Connected to the database successfully!")
    return model_choice, temperature, max_tokens

# Call it
model_choice, temperature, max_tokens = sidebar_config()


for message in st.session_state.chat_history:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(message.content)

user_query = st.chat_input("Enter your query...")
if user_query is not None and user_query.strip() != "":
    st.session_state.chat_history.append(HumanMessage(content=user_query))

    with st.chat_message("user"):  # <- use "user" here
        st.markdown(user_query)

    with st.chat_message("assistant"):
        if "db" not in st.session_state:
            st.error("Please connect to the database first from the sidebar.")
        else:
            response = get_response(
                user_query,
                model_choice,
                temperature,
                max_tokens,
                st.session_state.db,
                st.session_state.chat_history
            )
            st.markdown(response)

            st.session_state.chat_history.append(AIMessage(content=response))

# download option:
download_button(st.session_state.chat_history)
