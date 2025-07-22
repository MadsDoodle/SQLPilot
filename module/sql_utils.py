import sqlite3
from module.config import DB_PATH

def execute_sql_query(query: str):
    try:
        with sqlite3.connect(DB_PATH)  as conn:
            cursor=conn.cursor() ##ahha new thing thats
            cursor.execute(query)

            if query.strip().lower().startswith("select"):
                rows=cursor.fetchall()
                col_names=[description[0] for description in cursor.description]
                return rows,col_names
            else:
                conn.commit()
                return [],[]
            
    except sqlite3.Error as e:
        return f"Error: {str(e)}", []
    

def get_current_schema():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        schema_description = ""
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name});")
            cols = cursor.fetchall()
            schema_description+= f"- {table_name}({', '.join([col[1] for col in cols])})\n"
        return schema_description.strip()           