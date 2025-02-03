import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.chroma import Chroma
from typing import List
from agents.blog_team.schema import BlogPost
from agents.blog_team.vectorstore.utils import blog_post_to_document


class VectorStoreHandler:
    def __init__(
        self,
        collection_name: str = "blog_posts",
        persist_directory: str = "./blog_posts_vectorstore",
    ):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection_name = collection_name
        self.embedding_function = OpenAIEmbeddings(model="text-embedding-3-large")
        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            client=self.client,
            embedding_function=self.embedding_function,
        )

    async def process_and_store_blog_posts(
        self, blog_posts: List[BlogPost]
    ) -> List[str]:
        """Process and store blog posts in the vectorstore"""

        documents = [blog_post_to_document(post) for post in blog_posts]

        # Split documents (sync operation)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=100
        )
        split_docs = text_splitter.split_documents(documents)

        ID_list = await self.vectorstore.aadd_documents(split_docs)

        return ID_list

    async def url_exists_in_vectorstore(self, url: str) -> bool:
        """Check if a URL already exists in the vectorstore"""
        # Query the collection's metadata for the URL
        collection = self.client.get_collection(self.collection_name)
        results = collection.get(where={"url": url})

        return len(results["ids"]) > 0
