import openai
import streamlit as st

# Initialize the chat messages history
def initialize_messages():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "How can I help?"}
        ]

# Display chat messages
def display_chat_messages():
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant"):
                st.write(message["content"])

# Process user input and generate response
def process_user_input():
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.spinner("Thinking..."):
            r = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            )
            response = r.choices[0].message.content

        with st.chat_message("user"):
            message = {"role": "user", "content": st.session_state.messages[-1]["content"]}
            st.session_state.messages.append(message)
            st.write(st.session_state.messages[-1]["content"])
        

        with st.chat_message("assistant"):
            message = {"role": "assistant", "content": response}
            st.write(response)
            st.session_state.messages.append(message)

# Login page
def show_login_page():
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if email == "abc" and password == "123":
            st.session_state.logged_in = True
            st.experimental_rerun()  # Rerun the app to show the chat application
        else:
            st.error("Wrong credentials. Please try again.")

# Chatbot application
def show_chat_app():
    st.title("☃️ Frosty - Chatbot Application")
    st.write(f"Welcome to the chat application, {st.session_state.email}!")

    initialize_messages()
    display_chat_messages()
     
    prompt = st.chat_input("Say something")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        process_user_input()

    if st.button("Logout"):
        st.session_state.logged_in = False

# Main function
def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        show_login_page()
    else:
        if st.session_state.logged_in:
            st.session_state.email = "abc"  # Set the email
            show_chat_app()

if __name__ == "__main__":
    main()
