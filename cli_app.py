import asyncio
import os
from dotenv import load_dotenv
import weaviate
import weaviate.classes as wvc
from openai import OpenAI
from crawl4ai import *

class RAGSystem:
    def __init__(self):
        load_dotenv()
        # Initialize Weaviate client
        self.client = weaviate.connect_to_weaviate_cloud(
            cluster_url=os.getenv("WCD_URL"),
            auth_credentials=wvc.init.Auth.api_key(os.getenv("WCD_API_KEY")),
            headers={"X-Cohere-Api-Key": os.getenv("COHERE_APIKEY")}
        )
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._setup_collection()

    def _setup_collection(self):
        try:
            self.client.collections.delete("WebContent")
        except:
            pass
            
        self.collection = self.client.collections.create(
            name="WebContent",
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_cohere(),
            properties=[
                wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="url", data_type=wvc.config.DataType.TEXT),
            ]
        )

    async def store_content(self, url: str):
        # Crawl and store content
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            chunks = [c.strip() for c in result.markdown.split('\n\n') if c.strip()]
            
            with self.collection.batch.dynamic() as batch:
                for chunk in chunks:
                    batch.add_object({
                        "content": chunk,
                        "url": url
                    })
            
            return len(chunks)

    def query(self, question: str, limit: int = 3):
        # Get relevant chunks
        results = self.collection.query.near_text(
            query=question,
            limit=limit,
            return_properties=["content", "url"]
        )

        if not results.objects:
            return {"answer": "No relevant content found.", "sources": []}

        # Format context
        context = "\n\n".join([obj.properties["content"] for obj in results.objects])
        
        # Generate answer using OpenAI
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                {"role": "user", "content": f"""Based on the following context, answer this question: {question}

Context:
{context}

Answer:"""}
            ]
        )

        return {
            "answer": response.choices[0].message.content,
            "sources": [
                {"content": obj.properties["content"], "url": obj.properties["url"]} 
                for obj in results.objects
            ]
        }

    def close(self):
        self.client.close()

async def main():
    rag = None
    try:
        rag = RAGSystem()
        url = "https://huggingface.co/docs/smolagents/tutorials/building_good_agents"
        
        chunks = await rag.store_content(url)
        print(f"Stored {chunks} content chunks from {url}")
        
        query = "What are the key principles of building good agents?"
        result = rag.query(query)
        
        print(f"\nQuestion: {query}")
        print(f"\nAnswer: {result['answer']}")
        print("\nSources:")
        for source in result['sources']:
            print(f"\nFrom URL: {source['url']}")
            print(f"Content: {source['content'][:200]}...")
    
    finally:
        if rag:
            rag.close()

if __name__ == "__main__":
    asyncio.run(main())