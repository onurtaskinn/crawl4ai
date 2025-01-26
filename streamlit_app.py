import streamlit as st
import asyncio
from web_rag_system import RAGSystem

st.set_page_config(page_title="Website RAG System", page_icon="🔍")

@st.cache_resource
def get_rag_system():
    return RAGSystem()

async def process_url(url: str):
    rag = get_rag_system()
    with st.spinner('Crawling and processing webpage...'):
        chunks = await rag.store_content(url)
        st.success(f'Processed {chunks} content chunks from the webpage')

def process_question(question: str):
    rag = get_rag_system()
    with st.spinner('Searching and generating answer...'):
        result = rag.query(question)
        return result

st.title('🔍 Website RAG System')
st.write('Enter a URL to crawl and ask questions about its content.')

# URL input
url = st.text_input('Enter website URL:', 'https://huggingface.co/docs/smolagents/tutorials/building_good_agents')

if st.button('Process Website'):
    asyncio.run(process_url(url))

# Question input
question = st.text_input('Ask a question about the website:')

if question:
    result = process_question(question)
    
    st.write('### Answer')
    st.write(result['answer'])
    
    st.write('### Sources')
    for i, source in enumerate(result['sources'], 1):
        with st.expander(f'Source {i}'):
            st.write(f'**URL:** {source["url"]}')
            st.write(f'**Content:**\n{source["content"]}')