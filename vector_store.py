import numpy as np
import faiss
from unstructured.embed.openai import OpenAIEmbeddingConfig, OpenAIEmbeddingEncoder
import os

ADA_2_DIMENSION = 1536
FAISS_INDEX = None


class FaissIndexManager:
    """
    Class for managing Faiss index operations.
    """

    def __init__(self, dimension=ADA_2_DIMENSION) -> None:
        """
        Initializes the FaissIndexManager instance.

        Args:
            dimension (int, optional): Dimension of the embeddings. Defaults to ADA_2_DIMENSION.
        """
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.element_id_to_index = {}
        self.embedding_encoder = OpenAIEmbeddingEncoder(config=OpenAIEmbeddingConfig(api_key=os.getenv('OPENAI_API_KEY')))
        self.element_index_counter = 0

    
    def create_embeddings(self, chunks):
        """
        Creates embeddings for the given chunks using OpenAI's embedding encoder.

        Args:
            chunks (list): List of chunks.

        Returns:
            list: List of embeddings.
        """
        chunk_embeddings = self.embedding_encoder.embed_documents(
            elements=chunks,
        )
        print(f'{len(chunk_embeddings)} embeddings created by chunks with dimension {self.embedding_encoder.num_of_dimensions()}')
        return chunk_embeddings
        

    def store_chunks(self, chunks):
        """
        Stores chunks in the Faiss index.

        Args:
            chunks (list): List of chunks.
        """
        embedding_chunks = self.create_embeddings(chunks)
        print(f"{len(embedding_chunks)} embedding chunks created")

        raw_embeddings = [c.embeddings for c in embedding_chunks]

        embeddings_np = np.array(raw_embeddings).astype('float32')
        # Create FAISS index
        self.index.add(embeddings_np)
        element_ids = [c.id for c in embedding_chunks]
        for i, element_id in enumerate(element_ids):
            self.element_id_to_index[self.element_index_counter+i] = element_id
        self.element_index_counter+=len(chunks)

    def query_index(self, query, composite_elements):
        """
        Queries the Faiss index and retrieves corresponding composite elements.

        Args:
            query (str): Query string.
            composite_elements (list): List of composite elements.

        Returns:
            list: List of tuples containing composite elements and their distances.
        """
        query_embedding = self.embedding_encoder.embed_query(query=query)
        query_embedding_np = np.array([query_embedding]).astype('float32')

        distances, indices = self.index.search(query_embedding_np, k=5)  # Top 5 matches

        results = [(composite_elements[idx], distances[0][i]) for i, idx in enumerate(indices[0])]

        return results


    def range_query_faiss(self, query, threshold):
        """
        Performs a range query on the Faiss index.

        Args:
            query (str): Query string.
            threshold (float): Threshold for the range query.

        Returns:
            list: List of tuples containing element IDs and distances.
        """
        query_embedding = self.embedding_encoder.embed_query(query=query)
        query_embedding_np = np.array([query_embedding]).astype('float32')

        radius = threshold
        lims, D, I = self.index.range_search(query_embedding_np, radius)

        results = []
        for idx, dist in zip(I, D):
            if dist < threshold:
                element_id = self.element_id_to_index[idx]
                results.append((element_id, dist))

        return results
