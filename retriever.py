from imports import *
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter

from langchain_community.document_loaders import PyPDFLoader, TextLoader, \
    UnstructuredPowerPointLoader, WebBaseLoader

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma, FAISS
from langchain_community.document_loaders import JSONLoader

@dataclass
class Data:
    name: str
    path: str
    source: str
    format: Literal["pdf", "txt", "pptx", "jsonl", "url"]

    def load(self):
        if self.format == "pdf":
            return PyPDFLoader(self.path).load()
        elif self.format == "txt":
            return TextLoader(self.path).load()
        elif self.format == "jsonl":
            return JSONLoader(file_path=self.path,
                              jq_schema=".",
                              text_content=False,
                              json_lines=True,).load()
        elif self.format == "pptx":
            return UnstructuredPowerPointLoader(self.path).load()
        elif self.format == "url":
            header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"}
            return WebBaseLoader(web_paths=self.path, header_template=header).load()


common_data_list = [
    Data(name="용어집",
         path="data/glossary.txt",
         source="https://some-data.com",
         format="txt"),
]

metadata_list = [
    Data(name='user', path='data/user.jsonl', source='data/user.jsonl', format='jsonl'),
]

def get_company_retriever():
    documents = []
    for data in common_data_list:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        documents.append(text_splitter.split_documents(data.load()))
    documents = list(chain.from_iterable(documents))
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(documents, embeddings)
    retriever = vectorstore.as_retriever()
    #todo roadmap같은 경우, 동일 문서의 다른 파편도 중요한데, 일부만 가져오다보니, 답변에 특별한 정보가 없음
    return retriever


def get_metadata_retriever():
    documents = []
    for data in metadata_list:
        text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1, chunk_overlap=0)
        documents.append(text_splitter.split_documents(data.load()))
    documents = list(chain.from_iterable(documents))
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(documents, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    return retriever
