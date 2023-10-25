import openai
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

import consent_text

st.write("#")
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

if "login" not in st.session_state:
    st.session_state.login = False
if "over_max" not in st.session_state:
    st.session_state.over_max = False
if "name_cell" not in st.session_state:
    st.session_state.name_cell = False
if "num_transcripts" not in st.session_state:
    st.session_state.num_transcripts = 0
if "create_nickname" not in st.session_state:
    st.session_state.create_nickname = False
if "demo_survey" not in st.session_state:
    st.session_state.demo_survey = False
if "consent_check" not in st.session_state:
    st.session_state.consent_check = False
if "not_eligible" not in st.session_state:
    st.session_state.not_eligible = False

if st.session_state.over_max is True:
    st.write(
        "You have submitted the maximum number of transcripts. Thank you for participating!"
    )

elif st.session_state.not_eligible is True:
    st.write(
        "You are not eligible for this study. Thank you very much for your interest!"
    )


def consent_callback():
    # need to check if the user has actually checked the consent checkbox!
    if st.session_state.consent_check is False:
        st.subheader(":red[Please check the consent box to participate in the study.]")
    else:
        st.session_state.demo_survey = True


def demo_callback():
    # disqualify user if they've answered a qualifying question wrong
    if (
        st.session_state.use_chatbots == "No"
        or st.session_state.related_fields == "Yes"
    ):
        st.session_state.not_eligible = True
        st.session_state.demo_survey = False
    else:
        new_row = [
            st.session_state.gender_1,
            st.session_state.gender_2,
            st.session_state.gender_3,
            st.session_state.gender_4,
            st.session_state.gender_5,
            st.session_state.gender_6,
            st.session_state.gender_7,
            st.session_state.gender_8,
            st.session_state.trans,
            st.session_state.trans_2,
            st.session_state.race_1,
            st.session_state.race_2,
            st.session_state.race_3,
            st.session_state.race_4,
            st.session_state.race_5,
            st.session_state.race_6,
            st.session_state.race_7,
            st.session_state.race_8,
            st.session_state.race_9,
            st.session_state.race_10,
            st.session_state.US,
            st.session_state.orientation_1,
            st.session_state.orientation_2,
            st.session_state.orientation_3,
            st.session_state.orientation_4,
            st.session_state.orientation_5,
            st.session_state.orientation_6,
            st.session_state.orientation_7,
            st.session_state.orientation_8,
            st.session_state.orientation_9,
            st.session_state.orientation_10,
            st.session_state.orientation_11,
            st.session_state.orientation_12,
            st.session_state.age,
            st.session_state.education,
            st.session_state.orientation_1,
            st.session_state.use_chatbots,
            st.session_state.related_fields,
            st.session_state.factual,
            st.session_state.helpful,
            st.session_state.purpose,
            st.session_state.strategy,
            st.session_state.computer,
            st.session_state.computer_2,
            st.session_state.other_thoughts,
        ]
        sh_1.append_row(new_row, table_range="A1:AS1")
        # move to nickname creation step
        st.session_state.create_nickname = True


def login_callback():
    # check if user is present in sh3
    st.session_state.name_cell = sh_3.find(st.session_state.existing_nickname)
    # if so, set submitted to True and continue to chat
    if st.session_state.name_cell is not None:
        st.session_state.num_transcripts = int(
            sh_3.cell(st.session_state.name_cell.row, 3).value
        )
        # if over max, boot them from app
        if st.session_state.num_transcripts >= transcript_max:
            st.session_state.over_max = True
        else:
            st.session_state.login = True
    # if not present, tell the user they misspelled their nickname
    # (or they are a new user) and return them to landing page
    else:
        st.subheader(
            ":red[You may have misspelled your nickname, or you may not have signed up yet. Try again below!]"
        )


def nickname_callback():
    # check if nickname is already present in sh3
    already_exists = sh_3.find(st.session_state.new_nickname)
    if already_exists:
        st.write(
            ":red[This nickname is taken. Please try again with a new unique nickname.]"
        )
    else:
        # write user to user sheet
        # TRUE is fine here because they have to have checked the consent box to get here
        sh_3.append_row([st.session_state.new_nickname, "TRUE", 0])
        st.session_state.login = True


if st.session_state.login:
    with st.sidebar:
        if st.button("Submit transcript"):
            sh_2.append_row([str(st.session_state.messages)], table_range="A1:A1")
            # increment num_transcripts
            st.session_state.num_transcripts += 1
            # if over max, boot them from app
            if st.session_state.num_transcripts >= transcript_max:
                st.session_state.over_max = True
                st.session_state.login = False
            sh_3.update_cell(
                st.session_state.name_cell.row, 3, st.session_state.num_transcripts
            )
            del st.session_state["messages"]
        st.write(
            "This will submit your chat transcript to the researcher and restart your chat"
        )

    # TODO: add note saying they may experience errors and to try again later
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

elif st.session_state.over_max:
    pass

elif st.session_state.create_nickname:
    with st.form("nickname_form"):
        # add more explanation here?
        st.write("Next, choose a unique nickname to login.")
        st.text_input("Choose a unique nickname", key="new_nickname")
        nickname_form = st.form_submit_button(
            "Create nickname",
            on_click=nickname_callback,
        )

elif st.session_state.demo_survey:
    with st.form("demo_survey_form"):
        st.write("#")
        st.header("Demographic survey")
        st.write("1. Which best describes your gender? Choose all that apply.")
        st.checkbox("Woman", key="gender_1")
        st.checkbox("Man", key="gender_2")
        st.checkbox("Non-binary", key="gender_3")
        st.checkbox("Genderqueer", key="gender_4")
        st.checkbox("Agender", key="gender_5")
        st.checkbox("Something else", key="gender_6")
        st.text_input("Specify", key="gender_7")
        st.checkbox("Prefer not to answer", key="gender_8")
        st.radio(
            "Do you identify as transgender or cisgender?",
            ("Transgender", "Cisgender", "Prefer not to answer", "Something else"),
            key="trans",
        )
        st.text_input("Something else", key="trans_2")
        st.write(
            "Which of the following best represents your racial/ ethnic heritage? Choose all that apply."
        )
        st.checkbox("Asian", key="race_1")
        st.checkbox("African / Black", key="race_2")
        st.checkbox("Hispanic / Latine", key="race_3")
        st.checkbox("Middle Eastern / North African", key="race_4")
        st.checkbox("Native American", key="race_5")
        st.checkbox("Native Hawaiian / Pacific Islander", key="race_6")
        st.checkbox("White / European", key="race_7")
        st.checkbox("Something else", key="race_8")
        st.text_input("Specify", key="race_9")
        st.checkbox("Prefer not to answer", key="race_10")
        st.radio(
            "Did you spend most of your childhood in the US, or in another country?",
            ("In the US", "In another country"),
            key="US",
        )
        st.write("Which best describes your sexual orientation? Choose all that apply.")
        st.checkbox("Asexual", key="orientation_1")
        st.checkbox("Bisexual", key="orientation_2")
        st.checkbox("Gay", key="orientation_3")
        st.checkbox("Lesbian", key="orientation_4")
        st.checkbox("Heterosexual", key="orientation_5")
        st.checkbox("Pansexual", key="orientation_6")
        st.checkbox("Queer", key="orientation_7")
        st.checkbox("Sexually fluid", key="orientation_8")
        st.checkbox("Asexual", key="orientation_9")
        st.checkbox("Something else", key="orientation_10")
        st.text_input("Specify", key="orientation_11")
        st.checkbox("Prefer not to answer", key="orientation_12")
        st.radio(
            "Age",
            (
                "18-24",
                "25-34",
                "35-44",
                "45-54",
                "55-64",
                "65-74",
                "75-84",
                "85+",
                "Prefer not to answer",
            ),
            key="age",
        )
        st.radio(
            "What is the highest degree or level of school you have completed? (If you’re currently enrolled in school, please indicate the highest degree you have received.)",
            (
                "Some high school",
                "High school degree or equivalent",
                "Some college",
                "Associate degree (AA, AS)",
                "Bachelor’s degree (BA, BS)",
                "Master’s degree (MA, MS, MEd)",
                "Professional degree (MD, DDS, DVM)",
                "Doctorate (PhD, EdD)",
                "Prefer not to answer",
            ),
            key="education",
        )
        st.radio(
            "Do you use “generative AI” chatbots? (Examples include ChatGPT, Bard, and Bing Chat)",
            ("Yes", "No"),
            key="use_chatbots",
        )
        st.write(
            "(If you respond 'No', you will not be able to participate in this study.)"
        )
        st.radio(
            "Do you work or study in natural language processing, computational linguistics, machine learning, artificial intelligence, or computer science?",
            ("Yes", "No"),
            key="related_fields",
        )
        st.write(
            "(If you respond 'Yes', you will not be able to participate in this study.)"
        )
        st.radio(
            "How often do you think the outputs of “generative AI” chatbots are factual/true?",
            (
                "1 Never",
                "2 Rarely",
                "3 Occasionally",
                "4 Sometimes",
                "5 Frequently",
                "6 Usually",
                "7 Always",
            ),
            key="factual",
        )
        st.radio(
            "Do you find the outputs of “generative AI” chatbots useful/helpful?",
            (
                "1 Very unhelpful",
                "2 Unhelpful",
                "3 Somewhat unhelpful",
                "4 Neither helpful nor unhelpful",
                "5 Somewhat helpful",
                "6 Helpful",
                "7 Very helpful",
            ),
            key="helpful",
        )
        st.text_area(
            "What purpose do you usually use “generative AI” chatbots for?",
            key="purpose",
        )
        st.text_area(
            "When using “generative AI” chatbots, what strategies do you use to generate the responses you want or achieve your goals?",
            key="strategy",
        )
        st.radio(
            "What level of computer user do you consider yourself?",
            ("Beginning", "Intermediate", "Advanced"),
            key="computer",
        )
        st.text_input("Something else", key="computer_2")
        st.text_area(
            "If you have any other thoughts about this study, “generative AI” chatbots, or any other topic, please share them here.",
            key="other_thoughts",
        )

        submit = st.form_submit_button(
            "Submit demographic survey",
            on_click=demo_callback,
        )


else:
    st.header("Landing page")
    st.write("Existing users, enter your unique nickname to begin chatting!")
    with st.form("existing_user"):
        st.text_input("Enter nickname", key="existing_nickname")
        login = st.form_submit_button("Log in", on_click=login_callback)
    st.write(
        "New users, please fill out the consent form and demographic survey below before participating."
    )
    with st.form("consent_form"):
        st.header("Consent Form")
        st.subheader(consent_text.title)
        st.write(consent_text.header_1)
        st.write(consent_text.subtitle)
        st.write(consent_text.text_1)
        st.write(consent_text.text_2)
        st.write(consent_text.text_3)
        st.subheader(consent_text.header_2)
        st.write(consent_text.text_4)
        st.write(consent_text.text_5)
        st.subheader(consent_text.header_3)
        st.write(consent_text.text_6)
        st.markdown("- " + consent_text.bullet_1)
        st.markdown("- " + consent_text.bullet_2)
        st.write(consent_text.text_7)
        st.subheader(consent_text.header_4)
        st.write(consent_text.text_8)
        st.write(consent_text.text_9)
        st.write(consent_text.text_10)
        st.subheader(consent_text.header_5)
        st.write(consent_text.text_11)
        st.write(consent_text.text_12)
        st.write("Check below if you agree to this consent form:")
        consent_check = st.checkbox("I agree", key="consent_check")
        st.form_submit_button(
            "Submit consent form",
            on_click=consent_callback,
        )
