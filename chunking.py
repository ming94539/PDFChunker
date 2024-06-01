from unstructured.chunking.basic import chunk_elements
from unstructured.chunking.title import chunk_by_title

from openai import OpenAI
import os 
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_KEY)

'''
Alternative strategy since a lot of list items are misclassified as NarrativeText is to chunk by title if we find any lists in the pdf
'''

def smart_chunking(elements):
    paragraph_elements = []
    other_elements = []

    for e in elements:
        if e.to_dict()['type'] in ['NarrativeText']:
            paragraph_elements.append(e)
        else:
            other_elements.append(e)
    print('number of paragraphs',len(paragraph_elements))
    print('number of non-paragraph elements',len(other_elements))
    paragraph_chunks = chunk_elements(elements=paragraph_elements,max_characters=1000,new_after_n_chars=0)
    other_chunks = chunk_by_title(elements=other_elements,max_characters=1000)
    final_chunks = paragraph_chunks + other_chunks
    return final_chunks

def cheat_chunking(elements):
    chunk_with_title = False
    for e in elements:
        if e.to_dict()['type'] not in ['Title','NarrativeText','UncategorizedText']:
            chunk_with_title = True
    if chunk_with_title == True:
        return chunk_by_title(elements=elements,max_characters=1000)
    else:
        return chunk_elements(elements=elements,max_characters=1000,new_after_n_chars=0)
    
def openai_summarize_string(text):
    prompt = f"Summarize the given string (this can be a piece of text or html of a table) concisely in less than 50 characters: " + text
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Give what the user needs right away."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content

def get_global_context_with_titles(elements):
    # Adding Global Context
    file_title =''
    element_metadata= elements[0].to_dict()
    if element_metadata['type'] == 'Title':
        file_title = elements[0].text
    file_name = element_metadata['metadata']['filename']
    header_injection = "Under \'"+file_title+"\' in file name \'"+file_name+'\''
    return header_injection

def add_titles_string(elements):
    # Adding a special chunk that gives the 'table of contents' by adding all titles
    titles_text = ""
    for e in elements:
        if e.to_dict()['type'] in ['Title']:
            titles_text+=e.to_dict()['text']
    return titles_text

def prepend_chunk_text(chunks,prepend_text):
    for c in chunks:
        c.text = prepend_text+' \n'+c.text


def custom_chunking_methods(chunks,elements,use_ai_summary=False):
    # Make sure for Tables, the text that will be vectorized later on is the summary of the table
    # not the html too semantically more dense
    for c in chunks:
        c_data = c.to_dict()
        if c_data['type'] == "Table":
            c.text = openai_summarize_string(c_data['metadata']['text_as_html'])

    global_context_prepend = None
    if use_ai_summary:
        # use chatgpt summary of the full document
        full_doc_text = '\n'.join([e.text for e in elements])
        global_context_prepend = openai_summarize_string(full_doc_text)
    else: 
        #get global context by the file name and titles
        global_context_prepend = get_global_context_with_titles(elements)

    # get global context by the summary 
    prepend_chunk_text(chunks,global_context_prepend)

# def find_desired_chunking_length(elements):
#     max_length = 10000
#     paragraph_lengths = []
#     for e in elements:
#         metadata = e.to_dict()
#         if metadata['type'] =='NarrativeText':
#             paragraph_lengths.append(len(metadata['text']))
#     return min(paragraph_lengths)
            
# print(find_desired_chunking_length(elements))

# If we do chunk by title and don't make new_after_n_chars=0 it will try to fill up the max_characters window which will split addresses.pdf into 4 big chunks.
# if we do specify 0 for new_after_n_chars,  each element to appear in a chunk by itself, works well work doc3.pdf and office addresses.pdf but doesnt work well for lists.
# Chunking by title

# chunk_elements_pdf = chunk_elements(
#     elements=elements,
#     max_characters=1000,
#     new_after_n_chars=0
# )

# def page_chunking(elements):
#     final_chunks = []
#     paragraph_elements = []
#     other_elements = []

#     page_counter = 1
#     page_start = 0
#     use_chunk_by_title = False
#     for page_end in range(len(elements)):
#         print(page_end)
#         page_number = elements[page_end].to_dict()['metadata']['page_number']
#         if page_number > page_counter: 
#             print('new page',page_number,' go through prev page elements')
#             for e in range(page_start,page_end):
#                if elements[e].to_dict()['type'] != "NarrativeText":
#                    use_chunk_by_title = True
#                    break
#             if use_chunk_by_title:
#                 other_elements.extend(elements[page_start,page_end])
#             else:
#                 paragraph_elements.extend(elements[page_start,page_end])
            
#             page_counter+=1
#             page_start=page_end+1
#             use_chunk_by_title=False