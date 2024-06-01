from unstructured.partition.pdf import partition_pdf
from unstructured.cleaners.core import clean_bullets, clean_non_ascii_chars, clean_extra_whitespace
from unstructured.embed.openai import OpenAIEmbeddingConfig, OpenAIEmbeddingEncoder
import faiss
import argparse

from chunking import *
from faiss import *
from db_operations import *
import os
from dotenv import load_dotenv
load_dotenv()

embedding_encoder = OpenAIEmbeddingEncoder(config=OpenAIEmbeddingConfig(api_key=os.getenv('OPENAI_API_KEY')))
faiss_index = faiss.IndexFlatL2(ADA_2_DIMENSION)
chunks_index = []

def preprocess_elements(elements):
    for e in elements:
        e.apply(clean_bullets)
        e.apply(clean_non_ascii_chars)
        e.apply(clean_extra_whitespace)
        if len(e.text) == 0:
            elements.remove(e)

def create_embeddings(chunks):
    chunk_embeddings = embedding_encoder.embed_documents(
        elements=chunks,
    )
    print('number of embeddings created by chunks',len(chunk_embeddings))
    print(embedding_encoder.is_unit_vector(), embedding_encoder.num_of_dimensions())
    return chunk_embeddings


def ingest_pdf(pdf_path):
    # only strategy tht does pictures and tables 
    elements = partition_pdf(pdf_path,strategy='hi_res',infer_table_structure=True)
    preprocess_elements(elements)
    for e in elements:
        print(type(e),e)

    chunk_elements_pdf = cheat_chunking(elements)

    print(len(chunk_elements_pdf))
    print(chunk_elements_pdf)

    custom_chunking_methods(chunk_elements_pdf,elements,use_ai_summary=True)

    embedding_chunks = create_embeddings(chunk_elements_pdf)
    print(f"{len(embedding_chunks)} embedding chunks created")

    chunks_index.extend(embedding_chunks)
    store_chunks_in_faiss(faiss_index,embedding_chunks)

    connection = connect_to_database()
    create_database_and_table(connection)

    for chunk in chunk_elements_pdf:
        if chunk.to_dict()['type'] == 'Table':
            print('Table detected - storing raw html instead of text')
            insert_chunk(connection,chunk.id,chunk.to_dict()['metadata']['text_as_html'])
        else:
            insert_chunk(connection, chunk.id, chunk.text)

    print('Finished ingesting PDF into FAISS and mySQL',pdf_path)

def generate_answer(relevant_chunks_text, query):
    prompt = f"Based on the following chunks from the document, answer the query: {query}\n\n" + "\n\n".join(relevant_chunks_text)
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are given documents to help answer queries."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content


def rag_answer(query,chunk_index):
    range_results = range_query_faiss(query, faiss_index, chunk_index, .5, embedding_encoder)
    chunk_ids = [result.id for result, _ in range_results]
    print(chunk_ids)
    connection = connect_to_database()
    chunks = query_chunk_by_ids(connection,chunk_ids)
    relevant_chunks_text = [c['content'] for c in chunks]
    return generate_answer(relevant_chunks_text, query)

def ask_ai(question):
    ai_answer = rag_answer(question,chunks_index)
    # Code to interact with the AI model API and generate response
    return ai_answer


if __name__ == "__main__":
    print("Ingesting pdfs")

    pdf_path = 'docs/table pdf.pdf'
    ingest_pdf(pdf_path)

    parser = argparse.ArgumentParser(description="Ask AI a question")
    parser.add_argument("question", type=str, help="Question to ask AI")
    args = parser.parse_args()

    result = ask_ai(args.question)
    print(result)