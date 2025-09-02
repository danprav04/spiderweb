from sqlalchemy import create_engine, text
import psycopg2

# Create a connection to the postgres database
conn = psycopg2.connect(
    host="localhost",
    database="postgres",
    user="postgres",
    password="***REMOVED***",
    port=5433  # Specify the correct port number
)

# Drop the database
conn.autocommit = True
cur = conn.cursor()
cur.execute('DROP DATABASE IF EXISTS spiderweb')

# Create the database
cur.execute('CREATE DATABASE spiderweb')

# Close the connection
conn.close()
