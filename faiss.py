import numpy as np

ADA_2_DIMENSION = 1536

def store_chunks_in_faiss(faiss_index,chunks):
    raw_embeddings = []
    for element in chunks:
        raw_embeddings.append(element.embeddings)

    embeddings_np = np.array(raw_embeddings).astype('float32')
    # Create FAISS index
    faiss_index.add(embeddings_np)

    return faiss_index

# Function to query FAISS and retrieve corresponding CompositeElements
def query_faiss(query, faiss_index, composite_elements,embedding_encoder):
    # Generate embedding for the query
    query_embedding = embedding_encoder.embed_query(query=query)
    query_embedding_np = np.array([query_embedding]).astype('float32')

    # Search FAISS index
    distances, indices = faiss_index.search(query_embedding_np, k=5)  # Top 5 matches

    # Retrieve the corresponding CompositeElements
    results = [(composite_elements[idx], distances[0][i]) for i, idx in enumerate(indices[0])]

    return results


def range_query_faiss(query, faiss_index, composite_elements, threshold,embedding_encoder):
    # Generate embedding for the query
    query_embedding = embedding_encoder.embed_query(query=query)
    query_embedding_np = np.array([query_embedding]).astype('float32')

    # Initialize parameters for range search
    radius = threshold
    lims, D, I = faiss_index.range_search(query_embedding_np, radius)

    # Retrieve the corresponding CompositeElements and their distances
    results = []
    for i in range(len(I)):
        if D[i] < threshold:  # Apply additional check to ensure threshold is respected
            results.append((composite_elements[I[i]], D[i]))

    return results
