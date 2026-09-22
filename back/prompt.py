# from langchain_groq import ChatGroq
# from dotenv import load_dotenv
# import streamlit as st
# load_dotenv()

# model = ChatGroq(
#     model="llama-3.3-70b-versatile",
#     temperature=1
# )


# st.set_page_config(page_icon='A',page_title='Abx')

# st.write("hello")

# user_input = st.text_input("enter you prompt")

# if st.button('Summarize'):
#     result = model.invoke(user_input)
#     st.text(result.content)

# from langchain_openrouter import ChatOpenRouter
# from dotenv import load_dotenv
# import streamlit as st
# load_dotenv()

# model = ChatOpenRouter(
#     model="openrouter/free",
#     temperature=0
# )

# user_input = st.text_input("enter query")
# if st.button('go'):
#     result = model.invoke(user_input)
#     st.text(result.content)


# from langchain_google_genai import ChatGoogleGenerativeAI
# from dotenv import load_dotenv
# import streamlit as st
# load_dotenv()

# model = ChatGoogleGenerativeAI(
#     model="gemini-3.6-flash",
#     temperature=0
# )

# user_input = st.text_input("enter query")
# if st.button('send'):
#     result = model.invoke(user_input)
#     st.text(result.text)

from langchain_nvidia import ChatNVIDIA
import streamlit as st
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
load_dotenv()


model =ChatNVIDIA(
    model="nvidia/nemotron-3.5-lightning-30b-a3b",
    temperature=0,
    max_completion_tokens=16384
)
parser = StrOutputParser()
chain = model | parser

user_input = st.text_input("enter Query: ")
if st.button('send'):
    result = chain.invoke(user_input)
    st.text(result)