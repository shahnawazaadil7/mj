import os
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
import trafilatura

class WebQuery:
    def __init__(self):
        # Default OpenAI API Key
        default_api_key = "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"
        self.embeddings = OpenAIEmbeddings(openai_api_key=default_api_key)
        os.environ["OPENAI_API_KEY"] = default_api_key
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.llm = OpenAI(temperature=0, openai_api_key=default_api_key)
        self.chain = None
        self.db = None

        # Pre-ingest URLs
        pre_ingested_urls = [
            "https://en.wikipedia.org/wiki/Artificial_intelligence"]
        self.ingest_urls(pre_ingested_urls)

    def ask(self, question: str) -> str:
        if not self.chain or not self.db:
            return "No document has been ingested. Please ingest a document first."

        # Retrieve relevant documents and generate a response
        docs = self.db.similarity_search(question, k=5)
        return self.chain.run(input_documents=docs, question=question)

    def ingest(self, url: str) -> str:
        try:
            # Fetch content from the URL
            raw_content = trafilatura.fetch_url(url)
            if not raw_content:
                return "Failed to fetch URL content."

            result = trafilatura.extract(raw_content)
            if not result:
                return "No readable text found at the URL."

            # Process and split the text into documents
            documents = [Document(page_content=result, metadata={"source": url})]
            splitted_docs = self.text_splitter.split_documents(documents)

            # Initialize or update FAISS vector store
            if not self.db:
                self.db = FAISS.from_documents(splitted_docs, self.embeddings)
            else:
                self.db.add_documents(splitted_docs)

            # Initialize the QA chain if not already done
            if not self.chain:
                self.chain = load_qa_chain(self.llm, chain_type="stuff")
            
            return f"URL content from {url} ingested successfully."
        except Exception as e:
            return f"Error during ingestion: {str(e)}"

    def ingest_urls(self, urls: list):
        """Ingest a list of URLs."""
        for url in urls:
            self.ingest(url)

    def forget(self):
        """Forget the current database and chain."""
        self.db = None
        self.chain = None