import openai
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("Common Ground demo")

openai.api_key = st.secrets["OPENAI_API_KEY"]

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


skey = st.secrets["gcp_service_account"]
credentials = Credentials.from_service_account_info(
    skey,
    scopes=scopes,
)
client = gspread.authorize(credentials)
sh_1 = client.open("common_ground_demo").worksheet("Sheet1")
sh_2 = client.open("chat_transcripts").worksheet("Sheet1")
sh_3 = client.open("common_ground_users").worksheet("Sheet1")

transcript_max = 20

# Use this for demo password
# TODO: actual nickname system
# def check_password():
#     """Returns `True` if the user had the correct password."""

#     def password_entered():
#         """Checks whether a password entered by the user is correct."""
#         if st.session_state["password"] == st.secrets["password"]:
#             st.session_state["password_correct"] = True
#             del st.session_state["password"]  # don't store password
#         else:
#             st.session_state["password_correct"] = False

#     if "password_correct" not in st.session_state:
#         # First run, show input for password.
#         st.text_input(
#             "Password", type="password", on_change=password_entered, key="password"
#         )
#         return False
#     elif not st.session_state["password_correct"]:
#         # Password not correct, show input + error.
#         st.text_input(
#             "Password", type="password", on_change=password_entered, key="password"
#         )
#         st.error("Password incorrect")
#         return False
#     else:
#         # Password correct.
#         return True


# if check_password():
# if "consent" not in st.session_state:
#     st.session_state.consent = False
if "submit" not in st.session_state:
    st.session_state.submit = False
if "over_max" not in st.session_state:
    st.session_state.over_max = False

# TODO: is this also a good place to check # transcripts?


# def consent_callback():
#     st.session_state.consent = True


def submit_callback():
    # modify to handle checking/creating new nickname
    # step 1: check if nickname is already present in sh3
    # step 2: if present, display message and prompt for different nickname
    # step 3: if not present, write new nickname to sh3 and send user to chat
    new_row = [
        st.session_state.check_1,
        st.session_state.check_2,
        st.session_state.check_3,
        st.session_state.radio_1,
        st.session_state.free_1,
    ]
    sh_1.append_row(new_row, table_range="A1:E1")
    st.session_state.submit = True


def login_callback():
    # check if user is present in sh3
    name_cell = sh_3.find(st.session_state.existing_nickname)
    # if so, set submitted to True and continue to chat
    if name_cell is not None:
        st.session_state.num_transcripts = int(sh_3.cell(name_cell.row, 3).value)
        # if over max, boot them from app
        if st.session_state.num_transcripts >= transcript_max:
            # display message
            st.write(
                "You have already submitted the maximum number of transcripts. Thank you for participating!"
            )
        else:
            st.session_state.submit = True
    # if not present, tell the user they misspelled their nickname
    # (or they are a new user) and return them to landing page
    else:
        st.write(
            ":red[You may have misspelled your nickname, or you may not have signed up yet. Try again below!]"
        )


if st.session_state.submit:
    # TODO: also check num transcripts here to
    # prevent user from continuing to use chat interface?
    with st.sidebar:
        if st.button("Submit transcript"):
            sh_2.append_row([str(st.session_state.messages)], table_range="A1:A1")
            del st.session_state["messages"]
        st.write(
            "This will submit your chat transcript to the researcher and restart your chat"
        )

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
    st.header("Landing page")
    st.write("Existing users, enter your unique nickname to begin chatting")
    with st.form("existing_user"):
        st.text_input("Enter nickname", key="existing_nickname")
        login = st.form_submit_button("Log in", on_click=login_callback)
    st.write(
        "New users, please fill out the consent form and demographic survey before"
    )
    with st.form("demo_survey"):
        st.header("Consent form")
        st.write("Consent form text")
        consent_check = st.checkbox("I agree")
        st.header("Demographic survey")
        check_1 = st.checkbox("Checkbox question 1", key="check_1")
        check_2 = st.checkbox("Checkbox question 2", key="check_2")
        check_3 = st.checkbox("Checkbox question 3", key="check_3")
        radio_1 = st.radio(
            "Radio question",
            ("Option 1", "Option 2", "Option 3"),
            key="radio_1",
        )
        free_1 = st.text_input("Free text question", key="free_1")
        st.text_input("Choose a unique nickname", key="new_nickname")
        # TODO: handle creating new nicknames
        # TODO: handle maximum transcript count
        submit = st.form_submit_button(
            "Submit demographic survey",
            on_click=submit_callback,
        )
