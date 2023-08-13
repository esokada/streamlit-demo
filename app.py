import openai
import streamlit as st

st.title("Common Ground demo")

openai.api_key = st.secrets["OPENAI_API_KEY"]


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("Password incorrect")
        return False
    else:
        # Password correct.
        return True


if check_password():
    if "consent" not in st.session_state:
        st.session_state.consent = False
    if "submit" not in st.session_state:
        st.session_state.submit = False

    def consent_callback():
        st.session_state.consent = True

    def submit_callback():
        st.session_state.submit = True

    if st.session_state.submit:
        if "openai_model" not in st.session_state:
            st.session_state["openai_model"] = "gpt-3.5-turbo"

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Send a message"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                for response in openai.ChatCompletion.create(
                    model=st.session_state["openai_model"],
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    stream=True,
                ):
                    full_response += response.choices[0].delta.get("content", "")
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )
    else:
        if st.session_state.consent:
            if not st.session_state.submit:
                with st.form("demo_survey"):
                    st.header("Demographic survey")
                    st.checkbox("Checkbox question 1")
                    st.checkbox("Checkbox question 2")
                    st.checkbox("Checkbox question 3")
                    st.radio("Radio question", ("Option 1", "Option 2", "Option 3"))
                    st.text_input("Free text question")
                    submit = st.form_submit_button(
                        "Submit demographic survey", on_click=submit_callback
                    )

        else:
            with st.form("Consent form"):
                st.header("Consent form")
                st.write("Consent text")
                st.checkbox("I agree [...]")
                consent = st.form_submit_button(
                    "Submit consent form", on_click=consent_callback
                )
