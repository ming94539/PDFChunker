## Intro
This repo illustrates different RAG strategies for PDF documents. It is implemented with custom Chunking/Ingesting functions without using Langchain or Llamaindex. 
PDFs are hard to ingest properly for RAG applications due to lack of structure and high variety of data types (Tables, Forms, Images, Titles, etc.) that are hard to exract out accurately.
This will be a multi-modal RAG app on a folder of given PDFs.

## Install and Run
Put your pdfs in /docs and it will build a SQL Database and FAISS Vector Store using those PDFs.

1. pip install -r requirements.txt
2. python main.py

### PDF Chunking Notes

1. Unstructured chunking always try to fill up the max_characters window which isn't what we want. We want chunks to be individual paragraphs, lists with list items, and other units of information that are semantically together. if we do specify 0 for new_after_n_chars,  each element to appear in a chunk by itself, works well work doc3.pdf and office addresses.pdf but doesnt work well for lists such as Medical insurance.pdf. Therefore in cheat_chunking() I look ahead in the pdf to see if there's any elements that are not just pargraphs and decide whether to set it as 0 or not.
2. Unstructured isn't always accurate in terms of structural labeling. Many titles that should have been identified as titles have become ListItems which make the downstream Chunking to be wrong. This was the biggest bottleneck in accuracy in my experience so far.

### Chunking Strategies

1. **Look ahead chunking**: Evaluate what elements are in the pdf then decide chunking strategy - using infer_table_structure, chunk_by_title, high-res, etc. 
    a. **Pros**: Improve accuracy by using the right methods
    b. **Cons**: If it's a long pdf with a mix of different element types and will be hard that require different strategy, it will be complex to determine which part of the pdf to apply which strategy. E.G. Table, Lists, and Paragraph on the same page
2. **Injecting global context with LLM Summary**: Adding document level summaries to each chunk since chunks lack global concept awareness. For more complex documents with many sub-themes (like chapters of a book) there can even be subdoc summaries to create more hierarchical metadata.
    a. **Pros**: Improve accuracy for questions that require global context. E.G. Summary of an entire doc
    b. **Cons**: It can potentially introduces more noise to your embeddings since all your chunks have the same global context. One remedy to this could be to just have the embedding to be the text without global context but have the corresponding text include the global context but it still might lower the chunk retrieval recall for queries that mention global context explicitly.
3.  **Injecting global context with Table of Contents**: Instead of LLM Summary, use all the titles in the pdf to provide a rough summary or table of content
    a. **Pros**: Way faster and cheaper to compute than a LLM call
    b. **Cons**: May not be as accurate since the pdf titles may not reflect enough of the global context.
4.  **Chunking Tables**: Instead of vectorizing the table directly. We summarize the table beforehand and vectorize that, then pass the raw html format of the table since LLM process that better.
    a. **Pros**: More accurate.
    b. **Cons**: You may not have access to the html format of the table (or at least good quality) depending on your PDF Extraction library.

