import mysql.connector
from mysql.connector import Error
import os

class mySQLManager:
    """
    Class for managing MySQL database operations.
    """

    def __init__(self, host='localhost', database='pdf_chunks', user='root', password=None):
        """
        Initializes the MySQLManager instance.

        Args:
            host (str, optional): MySQL host. Defaults to 'localhost'.
            database (str, optional): Database name. Defaults to 'pdf_chunks'.
            user (str, optional): MySQL user. Defaults to 'root'.
            password (str, optional): MySQL password. Defaults to None (retrieved from environment variable).
        """
        self.host = host
        self.database = database
        self.user = user
        self.password = password or os.getenv('MYSQL_PASS')
        self.connection = self.connect_to_database()

    def connect_to_database(self):
        """
        Connects to the MySQL database.

        Returns:
            mysql.connector.connection.MySQLConnection: MySQL connection object.
        """
        try:
            # Connect to MySQL database
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            if connection.is_connected():
                    print("Connected to MySQL server.")
                    return connection
        except Error as e:
            print(f"Error: {e}")
            return None

    def create_database_and_table(self):
        """
        Creates the database and table if they do not exist. We drop the table if already exists to prevent duplicate
        data 
        """
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()

                # Create database
                cursor.execute("CREATE DATABASE IF NOT EXISTS pdf_chunks;")
                print("Database `pdf_chunks` created or already exists.")

                # Select the newly created database
                cursor.execute("USE pdf_chunks;")
                
                 # Drop table if exists
                cursor.execute("DROP TABLE IF EXISTS chunks_1;")
                print("Table `chunks_1` dropped if existed.")

                # Create table if not exists
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks_1 (
                    element_id VARCHAR(255) PRIMARY KEY,
                    content TEXT
                );
                """)

                print("Table `chunks_1` created.")

        except Error as e:
            print(f"Error: {e}")

    def query_chunk_by_ids(self, element_id_and_scores,printing=False):
        """
        Retrieves chunks by element IDs.

        Args:
            element_id_and_scores (list): List of tuples containing element IDs and scores.

        Returns:
            list: List of chunk dictionaries.
        """
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor(dictionary=True)
                element_ids = [id for id,distance in element_id_and_scores ]
                # Create a string of placeholders for element_ids
                placeholders = ', '.join(['%s'] * len(element_id_and_scores))

                # Query to retrieve the chunks by element_ids
                sql_select_query = f"SELECT * FROM chunks_1 WHERE element_id IN ({placeholders})"
                cursor.execute(sql_select_query, element_ids)

                # Fetch all the results
                results = cursor.fetchall()

                if results:
                    for i,result in enumerate(results):
                        if printing:
                            print('-'*50)
                            print('distance',element_id_and_scores[i])
                            print(f"Element ID: {result['element_id']}")
                            print(f"Content: {result['content']}")
                            print('-'*50)
                    return results
                else:
                    print("No chunks found with the given element IDs.")

        except Error as e:
            print(f"Error: {e}")

    def insert_chunk(self, element_id, content):
        """
        Inserts a chunk into the database.

        Args:
            element_id (str): Element ID.
            content (str): Content of the chunk.
        """
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()

                # Insert chunk into the table
                sql_insert_query = """
                INSERT INTO chunks_1 (element_id, content)
                VALUES (%s, %s);
                """
                cursor.execute(sql_insert_query, (element_id, content))
                self.connection.commit()
            else:
                print('Connection is not connected')
        except Error as e:
            print(f"Error: {e}")

    def view_table_contents(self):
        """
        Retrieves all rows from the table.

        Returns:
            list: List of dictionaries representing table rows.
        """
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor(dictionary=True)

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

    def close_connection(self):
        """
        Closes the MySQL connection.
        """
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MySQL connection is closed.")

