from dotenv import load_dotenv
load_dotenv()
from pdf_chunking import *
from vector_store import FaissIndexManager
from db_operations import mySQLManager
import os
import argparse


def generate_answer(relevant_chunks_text, query):
    """
    Generates an answer using GPT-based model completion.

    Args:
        relevant_chunks_text (list): List of relevant chunk texts.
        query (str): Query for which the answer is generated.

    Returns:
        str: Generated answer.
    
    """

    prompt = f"Based on the following chunks from the document, answer the query: {query}\n\n" + "\n\n".join(relevant_chunks_text)
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are given documents to help answer queries."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content


def rag_answer(query,vector_store,db):
    """
    Answers a query using RAG (Retrieve and Generate) method.

    Args:
        query (str): Query to be answered.
        vector_store (FaissIndexManager): Instance of FaissIndexManager.
        db (mySQLManager): Instance of mySQLManager.

    Returns:
        str: Generated answer.
    """
    element_id_and_scores = vector_store.range_query_faiss(query, .5)
    chunks = db.query_chunk_by_ids(element_id_and_scores)
    relevant_chunks_text = [c['content'] for c in chunks]
    return generate_answer(relevant_chunks_text, query)

    
if __name__ == "__main__":
    # OMP: Error #15: Initializing libomp.dylib, but found libomp.dylib already initialized.
    os.environ['KMP_DUPLICATE_LIB_OK']='True'
    vectore_store = FaissIndexManager()
    database = mySQLManager()
    database.create_database_and_table()
    print('*'*20,'Initialized FAISS vector store and mySQL database','*'*20)
    pdf_directory = 'docs'
    for file_name in os.listdir(pdf_directory):
        # Check if the file is a PDF
        if file_name.endswith('.pdf') and 'table' not in file_name:
            print('*'*10,file_name,'*'*10)
            # Construct the full path to the PDF file
            pdf_path = os.path.join(pdf_directory, file_name)

            # Ingest the PDF file
            ingest_pdf(pdf_path, vectore_store, database)
    print('*'*20,'Finished Ingesting PDFs into FAISS and MYSQL','*'*20)

    # Start of Question and Answering
    while True:
        # Ask for a question from the user
        question = input("Ask AI a question (type 'exit' to quit): ")
        
         # Check if user input is empty
        if not question.strip():
            print("Please input a valid question.")
            continue

        # Check if user wants to exit
        if question.lower() == 'exit':
            print("Exiting...")
            break

        # Answer the question using RAG
        answer = rag_answer(question, vectore_store, database)
        print("\n\nAnswer:", answer)