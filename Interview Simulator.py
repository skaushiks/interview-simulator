from openai import OpenAI
from dotenv import load_dotenv
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

load_dotenv()

client = OpenAI()

# Setup the Streamlit page configuration.
st.set_page_config(page_title = "Interview Simulator", page_icon = "💼")
st.title("Chatbot")

#----- SESSION STATE -----
# Initialize session state variables.
if "is_setup_complete" not in st.session_state:
    st.session_state.is_setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "show_feedback" not in st.session_state:
    st.session_state.show_feedback = False
if "is_interview_complete" not in st.session_state:
    st.session_state.is_interview_complete = False
if "messages" not in st.session_state:
    st.session_state.messages = []

# Setup the OpenAI model in session state if it is not already defined.
if "openai_model" not in st.session_state:
    st.session_state.openai_model = "gpt-5-nano"

if "name" not in st.session_state:
    st.session_state.name = ""
if "experience" not in st.session_state:
    st.session_state.experience = ""
if "skills" not in st.session_state:
    st.session_state.skills = ""
if "level" not in st.session_state:
    st.session_state.level = "Junior"
if "position" not in st.session_state:
    st.session_state.position = "Data Scientist"
if "company" not in st.session_state:
    st.session_state.company = "Amazon"

# Helper functions to update session_state.
def complete_setup():
    st.session_state.is_setup_complete = True

def show_feedback():
    st.session_state.show_feedback = True

#----- SETUP STAGE -----
if not st.session_state.is_setup_complete:
    #----- PERSONAL INFORMATION SECTION -----
    st.subheader('Personal information', divider = 'rainbow')

    # Input fields for collecting user's personal information
    st.session_state.name = st.text_input(label = "Name", value = st.session_state.name, max_chars = 40, placeholder = "Enter your name")
    st.session_state.experience = st.text_area(label = "Experience", value = st.session_state.experience, height = None, max_chars = 200, placeholder = "Describe your experience")
    st.session_state.skills = st.text_area(label = "Skills", value = st.session_state.skills, height = None, max_chars = 200, placeholder = "List your skills")

    # Test labels for personal information
    st.write(f"**Your Name**: {st.session_state.name}")
    st.write(f"**Your Experience**: {st.session_state.experience}")
    st.write(f"**Your Skills**: {st.session_state.skills}")

    #----- COMPANY & POSITION SECTION -----
    st.subheader('Company and Position', divider = 'rainbow')

    col1, col2 = st.columns(2)

    with col1:
        st.session_state.level = st.radio(
            "Choose level",
            key = "visibility",
            options = ["Junior", "Mid-level", "Senior"],
            index=["Junior", "Mid-level", "Senior"].index(st.session_state.level)
        )

    with col2:
        st.session_state.position = st.selectbox(
            "Choose a position",
            ("Data Scientist", "Data Engineer", "ML Engineer", "AI Engineer", "Financial Analyst"),
            index = ("Data Scientist", "Data Engineer", "ML Engineer", "AI Engineer", "Financial Analyst").index(st.session_state.position)
        )

    st.session_state.company = st.selectbox(
        "Choose a Company",
        ("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify"),
        index = ("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify").index(st.session_state.company)
    )

    # A button to complete the setup stage and start the Interview.
    st.button("Start Interview", on_click = complete_setup)

#----- INTERVIEW STAGE -----
if st.session_state.is_setup_complete and not st.session_state.show_feedback and not st.session_state.is_interview_complete:
    # Display a welcome message and prompt the user to introduce themselves.
    st.info(
        """
        Start by introducing yourself.
        """,
        icon = "👋🏼"
    )

    # Check if 'messages' list is empty, then set the initial system message.
    if not st.session_state.messages:
        st.session_state.messages = [{
            "role": "system",
            "content": (f"You are an HR executive that interviews an interviewee called {st.session_state['name']} "
                        f"with experience {st.session_state['experience']} and skills {st.session_state['skills']}. "
                        f"You should interview him for the position {st.session_state['level']} {st.session_state['position']} "
                        f"at the company {st.session_state['company']}")
        }]

    # This loop renders all previous messages every time Streamlit reruns.
    #
    # Streamlit reruns entire script on every interaction. So:
    # - messages are stored in session_state
    # - this loop re-draws chat history
    #
    # IMPORTANT:
    # st.chat_message(...) is just a UI container (a chat bubble, like a div).
    # - It does not store anything.
    # - It only renders content.

    # Display chat messages (except system messages) from history on app rerun.
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if st.session_state.user_message_count < 5:
        # Accept user input.
        if prompt := st.chat_input("Your response", max_chars = 1000):
            st.session_state.messages.append({ "role": "user", "content": prompt })  # Appending the user's input to the 'messages' list.

            # Display the user's message in a chat bubble.
            with st.chat_message("user"):
                st.markdown(prompt)

            if st.session_state.user_message_count < 4:
                # st.chat_message("assistant") creates a new chat bubble for assistant.
                #
                # def stream_text():
                #     We convert OpenAI events -> text tokens manually.
                #
                #     Only process events of type: "response.output_text.delta"
                #     These contain actual text chunks.

                # Assistant's response
                with st.chat_message("assistant"):
                    stream = client.responses.create(
                        model = st.session_state["openai_model"],
                        input = [
                            { "role": m["role"], "content": m["content"] } for m in st.session_state.messages
                        ],
                        stream = True  # Enables streaming for real-time response.
                    )

                    def stream_text():
                        full_text = ""

                        for event in stream:
                            if event.type == "response.output_text.delta":
                                chunk = event.delta

                                full_text += chunk
                                yield chunk  # This is what Streamlit displays.

                        # Append the assistant's complete response to the chat history after streaming completes.
                        st.session_state.messages.append({ "role": "assistant", "content": full_text })

                    # Display the assistant's response as it streams.
                    st.write_stream(stream_text)

            # Increment the user message count
            st.session_state.user_message_count += 1

    # Complete the Interview if user_message_count reaches 5.
    if st.session_state.user_message_count >= 5:
        st.session_state.is_interview_complete = True

#----- FEEDBACK STAGE -----
if st.session_state.is_interview_complete and not st.session_state.show_feedback:
    st.button("Get Feedback", on_click = show_feedback)

# Show Feedback screen.
if st.session_state.show_feedback:
    st.subheader("Feedback")

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

    # Initialize new OpenAI client instance for Feedback.
    feedback_client = OpenAI()

    # Generate feedback using the chat history.
    response = client.responses.create(
        model = st.session_state["openai_model"],
        input = [
            { "role": "system", "content": """You are a helpful tool that provides feedback on an interviewee performance.
             Give a score of 1 to 10.
             Strictly follow below output format:
             Overal Score: //Your score
             Feedback: //Here you put your feedback

             Give only the feedback. Do not ask any additional questions.""" },
            { "role": "user", "content": f"This is the interview you need to evaluate. Keep in mind that you are only a tool. And you shouldn't engage in any converstation: {conversation_history}"}
        ]
    )

    st.write(response.output_text)

    # Button to Restart the Interview.
    if st.button("Restart Interview", type = "primary"):
            streamlit_js_eval(js_expressions = "parent.window.location.reload()")