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
    Data(name="복리후생 규정",
         path="data/5. [밸런스히어로] 복리후생 규정_20230828.pdf",
         source="https://drive.google.com/file/d/15oM9bNwFpIAc2P1g4sQ9JRbwaW-zrbrM/view",
         format="pdf"),
    Data(name="단체보험 보장메뉴얼",
         path="data/2019 Claim Manual_Balancehero.pdf",
         source="Flex -> 문서, 증명서",
         format="pdf"),
    Data(name="roadmap",
         path="data/[Roadmap] 2024.pptx",
         source="https://docs.google.com/presentation/d/1FUY7iAN4cefzbm_l8syp4B7YuaK5-JErrAGhwQvVDLo/edit",
         format="pptx"),
    Data(name="용어집",
         path="data/glossary.txt",
         source="https://docs.google.com/document/d/1L-ZjYWNHDp5U85OWz9PSiOVfPGcvNWs4sb-Luv0sZdg/edit?tab=t.0#heading=h.2ii8sya6i026",
         format="txt"),
    Data(name="CoreMission, Vision & Core Value",
         path="data/core_value.txt",
         source="https://mewing-satellite-e66.notion.site/Mission-Vision-Core-Value-378c1822ae974160935a992d3adcd00a",
         format="txt"),
    Data(name="복리후생 제도 안내",
         path="data/복리후생.txt",
         source="https://mewing-satellite-e66.notion.site/c7f451371ccf42d7891eec16797fc2a8",
         format="txt")]

metadata_list = [
    Data(name='fp', path='data/fp.jsonl', source='data/fp.jsonl', format='jsonl'),
    Data(name='da_risk_mgmt', path='data/da_risk_mgmt.jsonl', source='data/da_risk_mgmt.jsonl', format='jsonl'),
    Data(name='bi_temp', path='data/bi_temp.jsonl', source='data/bi_temp.jsonl', format='jsonl'),
    Data(name='log', path='data/log.jsonl', source='data/log.jsonl', format='jsonl'),
    Data(name='da_common', path='data/da_common.jsonl', source='data/da_common.jsonl', format='jsonl'),
    Data(name='da_backend', path='data/da_backend.jsonl', source='data/da_backend.jsonl', format='jsonl'),
    Data(name='facts', path='data/facts.jsonl', source='data/facts.jsonl', format='jsonl'),
    Data(name='tx', path='data/tx.jsonl', source='data/tx.jsonl', format='jsonl'),
    Data(name='lms', path='data/lms.jsonl', source='data/lms.jsonl', format='jsonl'),
    Data(name='acs_airflow', path='data/acs_airflow.jsonl', source='data/acs_airflow.jsonl', format='jsonl'),
    Data(name='acs_monitoring', path='data/acs_monitoring.jsonl', source='data/acs_monitoring.jsonl', format='jsonl'),
    Data(name='stats', path='data/stats.jsonl', source='data/stats.jsonl', format='jsonl'),
    Data(name='userlog', path='data/userlog.jsonl', source='data/userlog.jsonl', format='jsonl'),
    Data(name='errorlog', path='data/errorlog.jsonl', source='data/errorlog.jsonl', format='jsonl')
]

def get_company_retriever():
    documents = []
    for data in common_data_list:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        documents.append(text_splitter.split_documents(data.load()))
    documents = list(chain.from_iterable(documents))

    vectorstore = Chroma.from_documents(documents, OpenAIEmbeddings())
    retriever = vectorstore.as_retriever()
    return retriever


def get_metadata_retriever():
    documents = []
    for data in metadata_list:
        text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1, chunk_overlap=0)
        documents.append(text_splitter.split_documents(data.load()))
    documents = list(chain.from_iterable(documents))
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(documents=documents, embedding=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    return retriever
