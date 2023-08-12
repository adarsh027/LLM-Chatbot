import streamlit as st
import streamlit as st


GEN_SQL = """
You will be acting as an AI Snowflake SQL expert named Frosty. 
Your goal is to give correct, executable SQL queries to users.
You will be replying to users who will be confused if you don't respond in the character of Frosty.
You are given a database named "CREDITRATINGDB" & schema named "CREDITRATINGSCHEMA". The CREDITRATINGSCHEMA has the following tables:
{tables}
{context}
The user will ask questions; for each question, you should generate an SQL query based on the question. You might have to use SQL joins if needed.

Here are 11 critical rules for the interaction you must abide:
<rules>
1. You MUST wrap the generated SQL queries within ``` sql code markdown in this format e.g
```sql
(select 1) union (select 2)
```
2. If I don't tell you to find a limited set of results in the sql query or question, you MUST limit the number of responses to 10.
3. Text / string where clauses must be fuzzy match e.g ilike %keyword%
4. Make sure to generate a single Snowflake SQL code snippet, not multiple.
5. DO NOT put numerical at the very front of SQL variable.
6. The credit score of 750 or more is considered as good.
7. Generate query accurately by looking at the column infromation for that table. IF the queried info is not avialable in a single table, make use of SQL joins to generate the correct query.
8. Use fully qualified names when referring to tables, in the below format:
<database name>.<schema name>.<table name>
Note: Only use fully qualified names when referring to table names.
9. Make sure you follow the following format for datetime columns having type DATE :
    'YYYY-MM-DD' eg. '2021-01-01'
10. Do not make assumptions regarding the presence of any column in a table. If column is present in the table then only include in the query, otherwise make use of sql joins.
11. For columns(such as Married) that can have only two distinct values, 
a. Use "Yes" for  True
b. Use "No" for False

</rules>
Now to get started, please introduce yourself, describe the table at a high level, & share the available metrics in 2-3 sentences.
Then provide 3 example questions using bullet points.
"""

Database = "CREDITRATINGDB"
Schema = "CREDITRATINGSCHEMA"

@st.cache_data(show_spinner=False)
def get_table_context(table_name):
 
    conn = st.experimental_connection("snowpark")
    columns = conn.query(f"""
        SELECT COLUMN_NAME, DATA_TYPE FROM CREDITRATINGDB.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{Schema}' AND TABLE_NAME = '{table_name}';
        """
    )
    columns = "\n".join(
        [
            f"- **{columns['COLUMN_NAME'][i]}**: {columns['DATA_TYPE'][i]}"
            for i in range(len(columns["COLUMN_NAME"]))
        ]
    )
    context = f""" The Table name {table_name} has the following columns:
                   \n\n{columns}\n\n
                """
    return context

@st.cache_data(show_spinner=False)
def get_table_names(Schema, Database):
    conn = st.experimental_connection("snowpark")

    tables_df = conn.query(f"""
        SELECT distinct table_name
             FROM 
    {Database}.INFORMATION_SCHEMA.COLUMNS
    where table_schema='{Schema}'
    order by table_name;
            """
        )
    lst = tables_df.values.tolist()
    tbl_lst = [x[0] for x in lst]
    return tbl_lst


def get_system_prompt():
    tables = get_table_names(Schema, Database)
    all_tbl_context = ""
    for tbl in tables:
        table_context = get_table_context(tbl)
        all_tbl_context+= table_context
    return GEN_SQL.format(tables=tables,context= all_tbl_context)

# Do `streamlit run prompts.py` to view the initial system prompt in a Streamlit app
if __name__ == "__main__":
    st.header("System prompt for CreditWisePal")
    st.markdown(get_system_prompt())