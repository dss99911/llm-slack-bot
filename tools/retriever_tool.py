from langchain_core.prompts import PromptTemplate
from langchain_core.tools import create_retriever_tool

from utils.imports import *
from tools.data_loader import get_documents

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


def get_retriever():
    documents = get_documents()
    if not documents:
        return None
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(documents, embeddings)
    retriever = vectorstore.as_retriever()
    return retriever


retriever = get_retriever()
retrieve_data_tool = create_retriever_tool(
    retriever,
    "retrieve_data",
    "search and return information",
    document_prompt=PromptTemplate.from_template("{page_content}\nSource: {source_link}"),
    document_separator="\n========\n"
) if retriever is not None else None
