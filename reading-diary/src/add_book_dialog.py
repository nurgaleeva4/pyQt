import os
from PyQt6.QtWidgets import QDialog, QMessageBox, QFileDialog, QVBoxLayout
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QPixmap
from PyQt6 import uic


class AddBookDialog(QDialog):
    def __init__(self, db, parent=None, book_id=None):
        super().__init__(parent)
        self.db = db
        self.book_id = book_id
        self.cover_image = None

        ui_path = os.path.join(os.path.dirname(__file__), '..', 'qt', 'add_book_dialog.ui')
        uic.loadUi(ui_path, self)

        self.genres = self.db.get_all_genres()

        self.setup_ui()
        self.setup_signals()

        if book_id:
            self.load_book_data()

    def setup_ui(self):
        # Загружаем список жанров
        self.combo_genre.clear()
        for genre in self.genres:
            self.combo_genre.addItem(genre['name'])

        # Добавляем пустой элемент
        self.combo_genre.addItem("Не указан")

        # Устанавливаем текущую дату
        today = QDate.currentDate()
        self.date_start.setDate(today)
        self.date_finish.setDate(today)

        # Настраиваем рейтинг
        self.rating_buttons = {
            1: self.radio_rating_1,
            2: self.radio_rating_2,
            3: self.radio_rating_3,
            4: self.radio_rating_4,
            5: self.radio_rating_5
        }

        # Настраиваем спинбокс для страниц
        self.spin_pages.setValue(0)

    def setup_signals(self):
        """Настраивает сигналы и слоты"""
        self.btn_load_cover.clicked.connect(self.load_cover)
        self.btn_clear_cover.clicked.connect(self.clear_cover)
        self.buttonBox.accepted.connect(self.save_book)
        self.buttonBox.rejected.connect(self.reject)

    def load_book_data(self):
        """Загружает данные книги для редактирования"""
        book = self.db.get_book(self.book_id)
        if not book:
            return

        # Заполняем поля
        self.edit_title.setText(book['title'])
        self.edit_author.setText(book['author'])

        # Жанр
        genre_name = book.get('genre_name', 'Не указан')
        index = self.combo_genre.findText(genre_name)
        if index >= 0:
            self.combo_genre.setCurrentIndex(index)

        # Статус
        index = self.combo_status.findText(book['status'])
        if index >= 0:
            self.combo_status.setCurrentIndex(index)

        # Даты
        if book['start_date']:
            self.date_start.setDate(QDate.fromString(book['start_date'], "yyyy-MM-dd"))
        if book['finish_date']:
            self.date_finish.setDate(QDate.fromString(book['finish_date'], "yyyy-MM-dd"))

        # Оценка
        if book['rating'] and book['rating'] in self.rating_buttons:
            self.rating_buttons[book['rating']].setChecked(True)
            self.radio_rating_none.setChecked(False)
        else:
            self.radio_rating_none.setChecked(True)

        # Страницы
        if 'pages' in book and book['pages'] is not None:
            self.spin_pages.setValue(book['pages'])
        else:
            self.spin_pages.setValue(0)

        # Отзыв
        self.text_review.setPlainText(book['review'] or "")

        # Обложка
        if book['cover_image']:
            self.cover_image = book['cover_image']
            self.update_cover_preview()

    def load_cover(self):
        """Загружает обложку книги"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )

        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    self.cover_image = f.read()
                self.update_cover_preview()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить изображение: {e}")

    def clear_cover(self):
        """Очищает обложку"""
        self.cover_image = None
        self.lbl_cover_preview.clear()
        self.lbl_cover_preview.setText("Обложка не загружена")

    def update_cover_preview(self):
        """Обновляет превью обложки"""
        if self.cover_image:
            pixmap = QPixmap()
            pixmap.loadFromData(self.cover_image)
            scaled_pixmap = pixmap.scaled(150, 200, Qt.AspectRatioMode.KeepAspectRatio)
            self.lbl_cover_preview.setPixmap(scaled_pixmap)

    def validate_input(self):
        """Проверяет корректность введенных данных"""
        title = self.edit_title.text().strip()
        author = self.edit_author.text().strip()

        if not title:
            QMessageBox.warning(self, "Ошибка", "Введите название книги")
            return False

        if not author:
            QMessageBox.warning(self, "Ошибка", "Введите автора книги")
            return False

        return True

    def save_book(self):
        """Сохраняет книгу в базу данных"""
        if not self.validate_input():
            return

        # Собираем данные
        book_data = {
            'title': self.edit_title.text().strip(),
            'author': self.edit_author.text().strip(),
            'genre': self.combo_genre.currentText() if self.combo_genre.currentText() != "Не указан" else None,
            'status': self.combo_status.currentText(),
            'start_date': self.date_start.date().toString("yyyy-MM-dd"),
            'finish_date': self.date_finish.date().toString("yyyy-MM-dd"),
            'review': self.text_review.toPlainText().strip(),
            'cover_image': self.cover_image,
            'pages': self.spin_pages.value()
        }

        # Определяем рейтинг
        book_data['rating'] = None
        for rating, button in self.rating_buttons.items():
            if button.isChecked():
                book_data['rating'] = rating
                break

        try:
            if self.book_id:
                # Редактируем существующую книгу
                success = self.db.update_book(self.book_id, book_data)
                if not success:
                    raise Exception("Не удалось обновить книгу")
            else:
                # Добавляем новую книгу
                book_id = self.db.add_book(book_data)
                if not book_id:
                    raise Exception("Не удалось добавить книгу")

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {e}")