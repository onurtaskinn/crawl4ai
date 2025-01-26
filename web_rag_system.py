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

    def _create_chunks(self, text: str, chunk_size: int = 1000) -> list[str]:
        """Create chunks of approximately equal size while preserving word boundaries"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            word_size = len(word) + 1  # +1 for space
            if current_size + word_size > chunk_size and current_chunk:
                # Join words with original whitespace and add to chunks
                chunks.append(' '.join(current_chunk).strip())
                current_chunk = [word]
                current_size = word_size
            else:
                current_chunk.append(word)
                current_size += word_size
        
        # Add the last chunk if it exists
        if current_chunk:
            chunks.append(' '.join(current_chunk).strip())
        
        return chunks

    async def store_content(self, url: str):
        # Crawl and store content
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            
            # Create balanced chunks
            chunks = self._create_chunks(result.markdown)
            
            # Print chunk lengths for verification
            chunk_lengths = [len(chunk) for chunk in chunks]
            print(f"Chunk lengths: {chunk_lengths}")
            
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
            model="gpt-4o",
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
        try:
            self.client.close()
        except:
            pass