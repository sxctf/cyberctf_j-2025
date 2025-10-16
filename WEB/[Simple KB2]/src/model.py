import sqlite3, os.path, uuid
from logs import *


setup_logging()
logger = logging.getLogger("db_logs")

def create_table():
    if os.path.exists('./data.db'):
        return "Database exist"
    else:
        # Create table
        try:
            
            # Users 
            sqliteConnection = sqlite3.connect('./data.db')
            sqlite_create_table_query = '''CREATE TABLE IF NOT EXISTS users (
                                            id INTEGER PRIMARY KEY,
                                            username VARCHAR(255) NOT NULL UNIQUE,
                                            password VARCHAR(255) NOT NULL,
                                            role VARCHAR(255) NOT NULL
                                            );'''
            cursor = sqliteConnection.cursor()
            logger.debug('Successfully Connected to SQLite')
            cursor.execute(sqlite_create_table_query)
            sqliteConnection.commit()
            logger.debug('SQLite table users created')
            
            # Entity 
            sqlite_create_table_query = '''CREATE TABLE IF NOT EXISTS entity (
                                            id VARCHAR(255) PRIMARY KEY,
                                            user_id VARCHAR(255) NOT NULL,
                                            name VARCHAR(255) NOT NULL,
                                            description VARCHAR(255) NOT NULL,
                                            image VARCHAR(255) NOT NULL
                                            );'''
            cursor = sqliteConnection.cursor()
            logger.debug('Successfully Connected to SQLite')
            cursor.execute(sqlite_create_table_query)
            sqliteConnection.commit()
            logger.debug('SQLite table users created')
            
        except sqlite3.Error as error:
            logger.error(f'Error while creating a sqlite table {error}')
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                logger.debug('sqlite connection is closed')
                    

def insert_user(username, password, role):
    # Insert data
    try:
        sqliteConnection = sqlite3.connect('./data.db')
        cursor = sqliteConnection.cursor()
        logger.debug('Successfully Connected to SQLite')
        cursor.execute("INSERT INTO users (username, password, role) VALUES ((?), (?), (?))", (username, password, role, ) )
        sqliteConnection.commit()
        logger.debug(f'Data successfully inserted {cursor.rowcount}')
        # print("Data successfully inserted", cursor.rowcount)
        cursor.close()
        return True

    except sqlite3.Error as error:
        logger.error(f'Error while inserting data in users table {error} trying insert username:{username}')
        return False
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            logger.debug('sqlite connection is closed')
            
            
def insert_entity(user_id, name, description, image):
    # Insert data
    
    try:
            sqliteConnection = sqlite3.connect('./data.db')
            cursor = sqliteConnection.cursor()
            logger.debug('Connected to SQLite')

            if name == "SecretObject":
                # Проверяем только для SecretObject
                cursor.execute("SELECT 1 FROM entity WHERE name = ? LIMIT 1", (name,))
                exists = cursor.fetchone()
                if exists:
                    logger.debug("Flag already exists, skipping insert")
                    return True  # Уже вставлен
                else:
                    logger.debug("Flag not found, inserting now")

            insert_query = """
                INSERT INTO entity (id, user_id, name, description, image)
                VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(insert_query, (
                str(uuid.uuid4()),
                str(user_id),
                name,
                description,
                image
            ))
            sqliteConnection.commit()
            logger.debug(f"Entity '{name}' inserted successfully")
            cursor.close()
            
    except sqlite3.Error as error:
        logger.error(f'Error while inserting data in entity table {error} data:{"name: ", name, " description: ", description, " image: ", image}')
        return False
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            logger.debug('sqlite connection is closed')
            


def get_passwd(username):
    
    try:
        sqliteConnection = sqlite3.connect('./data.db')
        cursor = sqliteConnection.cursor()
        logger.debug('Successfully Connected to SQLite')
        cursor.execute("SELECT * FROM users WHERE username = ?", (username, ))
        records = cursor.fetchall()
        logger.debug(f'Get content {records} for user with username {username}')
        # print(records)
        cursor.close()
        
        return records
    
    except sqlite3.Error as error:
        logger.error(f'Error while getting data from users {error} trying get data for username:{username}')
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            logger.debug('sqlite connection is closed')

def get_content(user_id):
    
    elements = []
    data = []
    
    try:
        sqliteConnection = sqlite3.connect('./data.db')
        cursor = sqliteConnection.cursor()
        logger.debug('Successfully Connected to SQLite')
        cursor.execute("SELECT * FROM entity WHERE user_id = ?", (str(user_id), ))
        records = cursor.fetchall()

        for row in records:
            elements.append(row[0])
            elements.append(row[2])
            elements.append(row[3])
            elements.append(row[4])
            data.append(elements)
            elements = []   
        cursor.close()
        
        return records
    
    except sqlite3.Error as error:
        logger.error(f'Error while getting data from entity {error} for user_id {user_id}')
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            logger.debug('sqlite connection is closed')