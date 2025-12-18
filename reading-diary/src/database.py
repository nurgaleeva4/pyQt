import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import json


class Database:
    def __init__(self, db_path: str = "reading_diary.db"):
        self.db_path = db_path
        self.connection = None

    def connect(self):
        """Устанавливает соединение с базой данных"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        return self.connection

    def close(self):
        """Закрывает соединение с базой данных"""
        if self.connection:
            self.connection.close()

    def init_db(self):
        """Инициализирует базу данных (создает таблицы если их нет)"""
        with self.connect() as conn:
            cursor = conn.cursor()

            # Таблица жанров
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS genres (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            ''')

            # Таблица книг
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    genre_id INTEGER,
                    status TEXT CHECK(status IN ('Хочу прочитать', 'Читаю', 'Прочитано', 'Отложено')),
                    start_date TEXT,
                    finish_date TEXT,
                    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                    review TEXT,
                    cover_image BLOB,
                    pages INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (genre_id) REFERENCES genres (id)
                )
            ''')

            # Добавляем стандартные жанры если их нет
            default_genres = [
                'Роман', 'Фантастика', 'Детектив', 'Фэнтези', 'Научная литература',
                'Биография', 'Историческая', 'Поэзия', 'Драма', 'Комедия',
                'Триллер', 'Ужасы', 'Приключения', 'Научно-популярная', 'Справочная'
            ]

            for genre in default_genres:
                cursor.execute(
                    "INSERT OR IGNORE INTO genres (name) VALUES (?)",
                    (genre,)
                )

            conn.commit()

    def add_book(self, book_data: Dict[str, Any]) -> int:
        """Добавляет новую книгу в базу данных"""
        with self.connect() as conn:
            cursor = conn.cursor()

            # Получаем ID жанра по имени
            genre_id = None
            if book_data.get('genre'):
                cursor.execute("SELECT id FROM genres WHERE name = ?", (book_data['genre'],))
                result = cursor.fetchone()
                if result:
                    genre_id = result['id']

            # Вставляем книгу
            cursor.execute('''
                INSERT INTO books 
                (title, author, genre_id, status, start_date, finish_date, 
                 rating, review, cover_image, pages)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                book_data['title'],
                book_data['author'],
                genre_id,
                book_data['status'],
                book_data['start_date'],
                book_data['finish_date'],
                book_data['rating'],
                book_data['review'],
                book_data.get('cover_image'),
                book_data.get('pages', 0)
            ))

            book_id = cursor.lastrowid
            conn.commit()
            return book_id

    def update_book(self, book_id: int, book_data: Dict[str, Any]) -> bool:
        """Обновляет данные книги"""
        with self.connect() as conn:
            cursor = conn.cursor()

            # Получаем ID жанра по имени
            genre_id = None
            if book_data.get('genre'):
                cursor.execute("SELECT id FROM genres WHERE name = ?", (book_data['genre'],))
                result = cursor.fetchone()
                if result:
                    genre_id = result['id']

            cursor.execute('''
                UPDATE books 
                SET title = ?, author = ?, genre_id = ?, status = ?, 
                    start_date = ?, finish_date = ?, rating = ?, review = ?,
                    cover_image = ?, pages = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                book_data['title'],
                book_data['author'],
                genre_id,
                book_data['status'],
                book_data['start_date'],
                book_data['finish_date'],
                book_data['rating'],
                book_data['review'],
                book_data.get('cover_image'),
                book_data.get('pages', 0),
                book_id
            ))

            conn.commit()
            return cursor.rowcount > 0

    def delete_book(self, book_id: int) -> bool:
        """Удаляет книгу из базы данных"""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_book(self, book_id: int) -> Optional[Dict[str, Any]]:
        """Получает информацию о книге по ID"""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT b.*, g.name as genre_name 
                FROM books b
                LEFT JOIN genres g ON b.genre_id = g.id
                WHERE b.id = ?
            ''', (book_id,))

            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_all_books(self, search_text: str = "") -> List[Dict[str, Any]]:
        """Получает список всех книг с возможностью поиска"""
        with self.connect() as conn:
            cursor = conn.cursor()

            if search_text:
                search_pattern = f"%{search_text}%"
                cursor.execute('''
                    SELECT b.*, g.name as genre_name 
                    FROM books b
                    LEFT JOIN genres g ON b.genre_id = g.id
                    WHERE b.title LIKE ? OR b.author LIKE ?
                    ORDER BY b.created_at DESC
                ''', (search_pattern, search_pattern))
            else:
                cursor.execute('''
                    SELECT b.*, g.name as genre_name 
                    FROM books b
                    LEFT JOIN genres g ON b.genre_id = g.id
                    ORDER BY b.created_at DESC
                ''')

            return [dict(row) for row in cursor.fetchall()]

    def get_all_genres(self) -> List[Dict[str, Any]]:
        """Получает список всех жанров"""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genres ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict[str, Any]:
        """Получает статистику по книгам"""
        with self.connect() as conn:
            cursor = conn.cursor()

            # Общая статистика
            cursor.execute("SELECT COUNT(*) as total FROM books")
            total = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as read_count FROM books WHERE status = 'Прочитано'")
            read_count = cursor.fetchone()['read_count']

            cursor.execute("SELECT COUNT(*) as reading_count FROM books WHERE status = 'Читаю'")
            reading_count = cursor.fetchone()['reading_count']

            cursor.execute("SELECT COUNT(*) as wishlist_count FROM books WHERE status = 'Хочу прочитать'")
            wishlist_count = cursor.fetchone()['wishlist_count']

            cursor.execute("SELECT AVG(rating) as avg_rating FROM books WHERE rating IS NOT NULL")
            avg_rating = cursor.fetchone()['avg_rating'] or 0

            cursor.execute("SELECT SUM(pages) as total_pages FROM books WHERE pages > 0")
            total_pages = cursor.fetchone()['total_pages'] or 0

            # Статистика по жанрам
            cursor.execute('''
                SELECT g.name as genre, COUNT(b.id) as count
                FROM genres g
                LEFT JOIN books b ON g.id = b.genre_id
                GROUP BY g.name
                HAVING COUNT(b.id) > 0
                ORDER BY count DESC
            ''')
            genres_stats = [dict(row) for row in cursor.fetchall()]

            # Статистика по оценкам
            cursor.execute('''
                SELECT rating, COUNT(*) as count
                FROM books
                WHERE rating IS NOT NULL
                GROUP BY rating
                ORDER BY rating
            ''')
            ratings_stats = [dict(row) for row in cursor.fetchall()]

            # Книги по месяцам
            cursor.execute('''
                SELECT strftime('%Y-%m', finish_date) as month, COUNT(*) as count
                FROM books
                WHERE finish_date IS NOT NULL
                GROUP BY strftime('%Y-%m', finish_date)
                ORDER BY month
            ''')
            monthly_stats = [dict(row) for row in cursor.fetchall()]

            # Книги по годам
            cursor.execute('''
                SELECT strftime('%Y', finish_date) as year, COUNT(*) as count
                FROM books
                WHERE finish_date IS NOT NULL
                GROUP BY strftime('%Y', finish_date)
                ORDER BY year
            ''')
            yearly_stats = [dict(row) for row in cursor.fetchall()]

            return {
                'total': total,
                'read_count': read_count,
                'reading_count': reading_count,
                'wishlist_count': wishlist_count,
                'avg_rating': round(avg_rating, 2) if avg_rating else 0,
                'total_pages': total_pages,
                'genres_stats': genres_stats,
                'ratings_stats': ratings_stats,
                'monthly_stats': monthly_stats,
                'yearly_stats': yearly_stats
            }

    def export_to_csv(self, file_path: str) -> bool:
        """Экспортирует данные в CSV файл"""
        try:
            import csv
            books = self.get_all_books()

            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'title', 'author', 'genre', 'status',
                              'start_date', 'finish_date', 'rating', 'pages', 'review']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for book in books:
                    writer.writerow({
                        'id': book['id'],
                        'title': book['title'],
                        'author': book['author'],
                        'genre': book.get('genre_name', ''),
                        'status': book['status'],
                        'start_date': book['start_date'],
                        'finish_date': book['finish_date'],
                        'rating': book['rating'] or '',
                        'pages': book['pages'] or 0,
                        'review': book['review'] or ''
                    })

            return True
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False