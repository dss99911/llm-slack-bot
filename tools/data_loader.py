from utils.imports import *

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredPowerPointLoader, WebBaseLoader
from langchain_community.document_loaders import JSONLoader


@dataclass
class Data:
    name: str
    path: str
    source: str
    format: Literal["pdf", "txt", "pptx", "jsonl", "url"]
    use_splitter: bool = True

    def load(self):
        if self.format == "pdf":
            return PyPDFLoader(self.path).load()
        elif self.format == "txt":
            return TextLoader(self.path).load()
        elif self.format == "jsonl":
            return JSONLoader(file_path=self.path,
                              jq_schema=".",
                              text_content=False,
                              json_lines=True).load()
        elif self.format == "pptx":
            return UnstructuredPowerPointLoader(self.path).load()
        elif self.format == "url":
            header = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"}
            return WebBaseLoader(web_paths=self.path, header_template=header).load()


common_data_list = [

]


def get_documents():
    documents = []
    for data in common_data_list:
        docs = data.load()
        if data.use_splitter:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            docs = text_splitter.split_documents(docs)

        # add source
        for doc in docs:
            doc.metadata["source_link"] = data.source
        documents.extend(docs)
    return documents
