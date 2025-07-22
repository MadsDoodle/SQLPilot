from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from module.config import OPENAI_API_KEY

def get_sql_query(user_query: str, schema_description: str) -> str:
    prompt = ChatPromptTemplate.from_template("""
    You are a professional SQL assistant. Given an English question,
    convert it into a valid SQL query using the provided schema.

    Schema:
    {schema_description}

    Guidelines:
    - Use standard SQL syntax only.
    - Always wrap string values in double quotes.
    - Use JOINs where necessary.
    - Do NOT include code fences (e.g., ```).
    - Return only the SQL query as output.

    Question: {user_query}
    SQL Query:
    """)

    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=OPENAI_API_KEY,
        temperature=0.0,
        max_tokens=1000,
    )

    chain = prompt | llm | StrOutputParser()

    return chain.invoke({
        "user_query": user_query,
        "schema_description": schema_description
    }).strip()
