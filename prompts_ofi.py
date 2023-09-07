import streamlit as st

GEN_SQL = """
You will be acting as an AI Snowflake SQL expert named OFI-ChatBot.
Your goal is to give correct, executable SQL queries to end-users, depending upon whether the logged-in user has role of "end_user", "enterprise_user".

You are given a database named "OFI_DB" & schema named "OFI_SCHEMA". The OFI_SCHEMA has the following:

{tables}
{context}

The logged in user has username= "{username}" which has a role= "{role}". If the username has role = "user", do not generate query if the information asked involves fetching information pertaining to other username/customer and display a message display a message saying: "Sorry, we don't have this information".

Here are 11 critical rules for the interaction you must abide:
<rules>
1. If the username has role = "end_user", only generate sql query which filter's data using where clause by username who is logged in.
2. If the username has role = "enterprise_user", generate sql queries without any restrictions.
3. You MUST wrap the generated SQL queries within ``` sql code markdown in this format e.g
```sql
(select 1) union (select 2)
```
4. Do not add any information regarding what the query will do. Only generate the sql query and nothing else.
5. If I don't tell you to find a limited set of results in the sql query or question, you MUST limit the number of responses to 10.
6. Text / string where clauses must be fuzzy match e.g ilike %keyword%
7. Make sure to generate a single Snowflake SQL code snippet, not multiple.
8. DO NOT put numerical at the very front of SQL variable.
9. ALWAYS include fully qualified table names in every SQL query. eg. "OFI_DB.OFI_SCHEMA.CONSUMERS"
10. All results should be in ascending order based on first column.
11. Make sure you follow the following format for the columns of type DATE : 'YYYY-MM-DD'
"""

DATABASE = "OFI_DB"
SCHEMA = "OFI_SCHEMA"

# Get the table names from the database
@st.cache_data(show_spinner=False)
def get_table_names(DATABASE, SCHEMA):
    conn = st.experimental_connection("snowpark")
    tables_df = conn.query(
        f"""
        SELECT DISTINCT TABLE_NAME
        FROM {DATABASE}.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA ='{SCHEMA}'
        ORDER BY TABLE_NAME;
        """
    )
    list = tables_df.values.tolist()
    tables_list = [x[0] for x in list]
    return tables_list


# Get the table context from the database
@st.cache_data(show_spinner=False)
def get_table_context(table):
    conn = st.experimental_connection("snowpark")
    columns = conn.query(
        f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM {DATABASE}.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{SCHEMA}'
        AND TABLE_NAME = '{table}';
        """,
    )
    columns = "\n".join(
        [
            f"- **{columns['COLUMN_NAME'][i]}**: {columns['DATA_TYPE'][i]}"
            for i in range(len(columns["COLUMN_NAME"]))
        ],
    )
    context = f"""
        The table name {table} has the following columns with their data types:
        \n{columns}\n
        """
    return context


# Get the system prompt
def get_system_prompt(username,role):
    tables = get_table_names(DATABASE, SCHEMA)
    all_tables_context = ""
    for table in tables:
        table_context = get_table_context(table)
        all_tables_context += table_context
    return GEN_SQL.format(tables=tables, context=all_tables_context, username=username,role=role)


if __name__ == "__main__":
    st.header("System prompt for OFI-ChatBot")
    st.markdown(get_system_prompt())