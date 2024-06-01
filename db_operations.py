import mysql.connector
import os

def connect_to_database():
    try:
        # Connect to MySQL database
        connection = mysql.connector.connect(
            host='localhost',
            database='pdf_chunks',
            user='root',
            password=os.getenv('MYSQL_PASS')
        )
        return connection
    except Error as e:
        print(f"Error: {e}")

def create_database_and_table(connection):
    try:
        if connection.is_connected():
            cursor = connection.cursor()

            # Create database
            cursor.execute("CREATE DATABASE IF NOT EXISTS pdf_chunks;")
            print("Database `pdf_chunks` created or already exists.")

            # Select the newly created database
            cursor.execute("USE pdf_chunks;")
            # Create table if not exists
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks_1 (
                element_id VARCHAR(255) PRIMARY KEY,
                content TEXT
            );
            """)

            print("Table `chunks_1` created or already exists.")

    except Error as e:
        print(f"Error: {e}")

def query_chunk_by_ids(connection, element_ids):
    try:
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)

            # Create a string of placeholders for element_ids
            placeholders = ', '.join(['%s'] * len(element_ids))

            # Query to retrieve the chunks by element_ids
            sql_select_query = f"SELECT * FROM chunks_1 WHERE element_id IN ({placeholders})"
            cursor.execute(sql_select_query, element_ids)

            # Fetch all the results
            results = cursor.fetchall()

            if results:
                print("Chunks found:")
                for result in results:
                    print(f"Element ID: {result['element_id']}")
                    print(f"Content: {result['content']}")
                return results
            else:
                print("No chunks found with the given element IDs.")

    except Error as e:
        print(f"Error: {e}")

def insert_chunk(connection, element_id, content):
    try:
        if connection.is_connected():
            cursor = connection.cursor()

            # Insert chunk into the table
            sql_insert_query = """
            INSERT INTO chunks_1 (element_id, content)
            VALUES (%s, %s);
            """
            cursor.execute(sql_insert_query, (element_id, content))
            connection.commit()
            print("Chunk inserted successfully.")
        else:
            print('Connection is not connected')
    except Error as e:
        print(f"Error: {e}")

def view_table_contents(connection):
    try:
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)

            # Select all rows from the table
            sql_select_query = "SELECT * FROM chunks_1"
            cursor.execute(sql_select_query)

            # Fetch all rows
            rows = cursor.fetchall()

            if rows:
                return rows
            else:
                print("The table is empty.")
        else:
            print('Not connected')

    except Error as e:
        print(f"Error: {e}")

