import sqlite3


def create_table():
    try:
        sqlitr_connection = sqlite3.connect('Vkinder')
        cursor = sqlitr_connection.cursor()

        sqlite_create_table_query = '''CREATE TABLE IF NOT EXISTS user (                            
                                user_id INTEGER,
                                customer_id,
                                is_like BOOLEAN,
                                CONSTRAINT pk PRIMARY KEY (user_id, customer_id));
                                '''
        cursor.execute(sqlite_create_table_query)
        sqlitr_connection.commit()
        cursor.close()
    except sqlite3.Error:
        pass
    finally:
        if (sqlitr_connection):
            sqlitr_connection.close()


def record_user(id, client_id):
    try:
        sqlitr_connection = sqlite3.connect('Vkinder')
        cursor = sqlitr_connection.cursor()

        sqlite_add_user_query = f'''INSERT INTO user (user_id, customer_id) 
                                    VALUES ({id}, {client_id});
                                '''
        cursor.execute(sqlite_add_user_query)
        sqlitr_connection.commit()
        cursor.close()
        return True
    except sqlite3.Error:
        return False
    finally:
        if (sqlitr_connection):
            sqlitr_connection.close()


def set_favorite(id_user, client_id):
    try:
        sqlitr_connection = sqlite3.connect('Vkinder')
        cursor = sqlitr_connection.cursor()

        sqlite_add_favorite_query = f'''UPDATE user
                                    SET is_like  = True
                                    WHERE customer_id = {client_id} AND user_id = {id_user} ;
                                '''
        cursor.execute(sqlite_add_favorite_query)
        sqlitr_connection.commit()
        cursor.close()
    except sqlite3.Error:
        pass
    finally:
        if (sqlitr_connection):
            sqlitr_connection.close()


def show_favorite(client_id):
    try:
        sqlitr_connection = sqlite3.connect('Vkinder')
        cursor = sqlitr_connection.cursor()

        sqlite_show_favorite_query = f'''SELECT * FROM user
                                    WHERE is_like = True AND customer_id = {client_id};
                                '''
        cursor.execute(sqlite_show_favorite_query)
        record = cursor.fetchall()
        users_list = []
        for user_id in record:
            users_list.append(user_id[0])
        sqlitr_connection.commit()
        cursor.close()
        return users_list
    except sqlite3.Error:
        pass
    finally:
        if (sqlitr_connection):
            sqlitr_connection.close()