import openai
import re
import streamlit as st
from prompts_ofi import get_system_prompt
import plotly.express as px

DATABASE = "OFI_DB"
SCHEMA = "OFI_SCHEMA"
TABLE = "Consumers"

st.set_page_config(layout="wide")

# Create two columns
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        '<a href="https://www.ofi.com/"><img src="https://media.licdn.com/dms/image/C561BAQGHaVVN7nfKWg/company-background_10000/0/1644563142617?e=1694689200&v=beta&t=TNTeOhQs6GuNG7R1jyLinW1sko9w_8yCdIJHBBNeaAQ" width="300"></a>',
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        '<a href="https://hoonartek.com/"><img src="https://hoonartek.com/wp-content/uploads/2022/01/Hoonartek-logo-light.svg" width="300"></a>',
        unsafe_allow_html=True
    )

# Function to check if a user is authenticated
def isAuthenticated(database, schema, table, username, role, password):
    conn = st.experimental_connection("snowpark")
    results = conn.query(
        f"""
        SELECT Username, Role, Password
        FROM {database}.{schema}.{table}
        WHERE Username = '{username}' AND Role = '{role}' AND Password = '{password}'
        """
    )
    return len(results) > 0

# Function to display the login form and handle authentication
def display_login_form():
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    role = st.sidebar.selectbox("Role", ["end_user", "enterprise_user"])

    if st.sidebar.button("Login"):
        if isAuthenticated(DATABASE, SCHEMA, TABLE, username, role, password):
            st.session_state.username = username
            st.session_state.password = password
            st.session_state.role = role
            st.sidebar.success("Logged in as {}".format(username))
        else:
            st.sidebar.error("Incorrect username, password, or role")
            st.session_state.username = None
            st.session_state.password = None
            st.session_state.role = None

# Function to handle the main chatbot functionality
def chatbot():
    st.title("👨‍💼 OFI-Buddy")
    openai.api_key = st.secrets.OPENAI_API_KEY

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": get_system_prompt(st.session_state.username, st.session_state.role)}
        ]
    with st.chat_message('assistant'):
            st.write(f"Hello {st.session_state.username}, I am OFI-Buddy, your personal assistant on OFI services. How may I assist you today?")
    
    for message in st.session_state.messages:
        if message["role"] == "system":
            continue
        elif message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        if message["role"] == "assistant" and "sql" in message:
            #filtered_content = re.sub(r"```sql\n(.*)\n```", "[SQL Query Hidden]", message["content"], re.DOTALL)
                with st.chat_message("assistant"):
                    if st.session_state.role=='enterprise_user':
                        st.write(message["sql"])
                    st.write(message["results"])
                    if "fig" in message:
                        if message["fig"]:
                            st.write(message["fig"])
        elif message["role"] == "assistant" and "content" in message:
            if message["content"]:
                with st.chat_message("assistant"):
                    st.write(message["content"])

    
    prompt = st.chat_input("Say something")
    if prompt:
        with st.spinner("Thinking..."):
            message = {"role": "user", "content": prompt}
            st.session_state.messages.append(message)

            # Generate assistant response
            response = ""
            for delta in openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                stream=True,
            ):
                response += delta.choices[0].delta.get("content", "")


        if st.session_state.messages[-1]["role"] == "user":
            with st.chat_message("user"):
                st.write(st.session_state.messages[-1]["content"])
            with st.chat_message("assistant"):
                sql_match = re.search(r"```sql\n(.*)\n```", response, re.DOTALL)
                if sql_match:
                    sql = sql_match.group(1)
                    conn = st.experimental_connection("snowpark")
                    try:
                        results = conn.query(sql)
                        message = {"role": "assistant", "content": ""}
                        message["results"] = results
                        message["sql"]=sql
                        if st.session_state.role=='enterprise_user':
                            st.write(sql)
                        if results.empty:
                            results= "The requested data is not available within the database."
                            st.warning(results)
                        else: 
                            st.dataframe(results)
                            message= plot_graph(results,message)
                    except Exception as e:
                        st.write(e)
                        st.write("Unable to fetch this info. Please check the generated SQL query.")
                    finally:
                        st.session_state.messages.append(message)
                else:
                    st.write(response)
                    message = {"role": "assistant", "content": response}
                    st.session_state.messages.append(message)



def plot_graph(df,message):
    fig=""
    # if set(['TRANSACTIONDATE', 'AMOUNT']).issubset(df.columns):
    #     fig = px.bar(df, x=df['TRANSACTIONDATE'], y=df['AMOUNT'])
    #     st.plotly_chart(fig, use_container_width=True, sharing="streamlit", theme="streamlit")
    #     #st.bar_chart(results, x='TRANSACTIONDATE', y='AMOUNT')
    # if set(['INCOME', 'SCORE']).issubset(df.columns):
    #     fig = px.line(df, x=df['INCOME'], y=df['SCORE'])
    #     st.plotly_chart(fig, use_container_width=True, sharing="streamlit", theme="streamlit")
    #     #st.line_chart(results, x='INCOME', y='SCORE')
    # if set(['ETHNICITY', 'CUSTOMER_COUNT']).issubset(df.columns):
    #     fig = px.pie(df, values=df['CUSTOMER_COUNT'], names=df['ETHNICITY'], hole=.3)
    #     st.write(fig)
    message["fig"] = fig
    return message
                                   

# Main function to control the application flow
def main():
    st.image(
        "https://hoonartek.com/wp-content/uploads/2022/01/Hoonartek-logo-light.svg",
        width=200,
    )

    # Session state handling
    if "username" not in st.session_state:
        st.session_state.username = None
        st.write("Please Login to continue")


    if "password" not in st.session_state:
        st.session_state.password = None

    if "role" not in st.session_state:
        st.session_state.role = None

    st.sidebar.title("Authentication")

    if isAuthenticated(
        DATABASE,
        SCHEMA,
        TABLE,
        st.session_state.username,
        st.session_state.role,
        st.session_state.password
    ):
        st.sidebar.success("Logged in as {}".format(st.session_state.username))
        if st.sidebar.button("Logout", key="logout"):
            st.session_state.clear()
            st.experimental_rerun()
    else:
        display_login_form()

    if st.session_state.username:
        chatbot()

if __name__ == "__main__":
    main()