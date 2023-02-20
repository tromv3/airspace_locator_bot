import sqlite3
from person import Person


class DB:

    def __init__(self):
        self.connection = sqlite3.connect('user.db')
        self.cursor = self.connection.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id INT PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        location GEOGRAPHY,
        aircraft TEXT);
        """)
        self.connection.commit()

    def add_user(self, user: Person) -> bool:
        try:
            with self.connection:
                if self.select_single(user.user_id) is None:
                    self.cursor.execute('INSERT INTO users (user_id, first_name, last_name) VALUES (?, ?, ?)',
                                        (user.user_id,
                                         user.first_name,
                                         user.last_name))
                    self.connection.commit()
            return True
        except:
            return False

    def set_user_location(self, user: Person) -> bool:
        try:
            with self.connection:
                self.cursor.execute('UPDATE users SET location = ? WHERE user_id= ?', (user.location, user.user_id))
                self.connection.commit()
            return True
        except:
            return False

    def set_aircraft(self, user: Person) -> bool:
        try:
            with self.connection:
                self.cursor.execute('UPDATE users SET aircraft = ? WHERE user_id= ?', (user.aircraft, user.user_id))
                self.connection.commit()
            return True
        except:
            return False

    def change_user(self, user: Person):
        try:
            with self.connection:
                self.cursor.execute('UPDATE users SET first_name = ?, last_name= ? '
                                    'WHERE user_id = ?', (user.first_name, user.last_name, user.user_id))
                self.connection.commit()
            return True
        except:
            return False

    def select_single(self, user_id) -> Person:
        """ Получаем одну строку с номером user_id """
        with self.connection:
            user = self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
            return Person(user_id=user[0],
                          first_name=user[1],
                          last_name=user[2],
                          location=user[3],
                          aircraft=user[4]) if user is not None else None

    def select_all(self) -> list:
        """ Получаем все строки """
        with self.connection:
            return self.cursor.execute('SELECT * FROM users').fetchall()

    def count_rows(self) -> int:
        """ Считаем количество строк """
        with self.connection:
            result = self.cursor.execute('SELECT * FROM users').fetchall()
            return len(result)

    def close(self) -> None:
        """ Закрываем текущее соединение с БД """
        self.connection.close()


if __name__ == "__main__":
    db = DB()
    db.close()
