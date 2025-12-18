import os
from PyQt6.QtWidgets import (
    QMainWindow, QMessageBox, QFileDialog, QInputDialog,
    QTableWidgetItem, QMenu, QHeaderView
)
from PyQt6.QtCore import Qt, QDate, pyqtSlot
from PyQt6.QtGui import QAction, QPixmap, QImage, QShortcut, QKeySequence
from PyQt6 import uic
from add_book_dialog import AddBookDialog
from statistics_dialog import StatisticsDialog


class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current_book_id = None

        # Загружаем интерфейс из файла .ui
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'qt', 'main_window.ui')
        uic.loadUi(ui_path, self)

        self.setup_ui()
        self.setup_signals()
        self.load_books()

    def setup_ui(self):
        """Настраивает интерфейс"""
        # Настраиваем таблицу книг
        headers = ["ID", "Название", "Автор", "Жанр", "Статус", "Начало", "Конец", "Оценка", "Страниц"]
        self.table_books.setColumnCount(len(headers))
        self.table_books.setHorizontalHeaderLabels(headers)

        # Настраиваем ширину колонок
        self.table_books.hideColumn(0)  # Скрываем ID
        self.table_books.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_books.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        # Устанавливаем заголовки для детальной информации
        self.lbl_cover.setText("")

    def setup_signals(self):
        """Настраивает сигналы и слоты"""
        # Кнопки
        self.btn_add.clicked.connect(self.add_book)
        self.btn_edit.clicked.connect(self.edit_book)
        self.btn_delete.clicked.connect(self.delete_book)
        self.btn_stats.clicked.connect(self.show_statistics)
        self.btn_export.clicked.connect(self.export_data)

        # Поиск
        self.search_input.textChanged.connect(self.load_books)

        # Таблица - используем signal currentCellChanged
        self.table_books.currentCellChanged.connect(self.on_book_selected)
        self.table_books.customContextMenuRequested.connect(self.show_context_menu)
        self.table_books.doubleClicked.connect(self.edit_book)

        # Меню
        self.action_new.triggered.connect(self.add_book)
        self.action_edit.triggered.connect(self.edit_book)
        self.action_delete.triggered.connect(self.delete_book)
        self.action_export.triggered.connect(self.export_data)
        self.action_import.triggered.connect(self.import_data)
        self.action_stats.triggered.connect(self.show_statistics)
        self.action_about.triggered.connect(self.show_about)
        self.action_exit.triggered.connect(self.close)

        # Горячие клавиши
        shortcut_add = QShortcut(QKeySequence("Ctrl+N"), self)
        shortcut_add.activated.connect(self.add_book)

        shortcut_edit = QShortcut(QKeySequence("Ctrl+E"), self)
        shortcut_edit.activated.connect(self.edit_book)

        shortcut_delete = QShortcut(QKeySequence("Delete"), self)
        shortcut_delete.activated.connect(self.delete_book)

        shortcut_search = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_search.activated.connect(self.focus_search)

    def focus_search(self):
        """Переводит фокус на поле поиска"""
        self.search_input.setFocus()
        self.search_input.selectAll()

    def load_books(self):
        """Загружает список книг в таблицу"""
        search_text = self.search_input.text().strip()
        books = self.db.get_all_books(search_text)

        self.table_books.setRowCount(len(books))

        for row, book in enumerate(books):
            # ID
            self.table_books.setItem(row, 0, QTableWidgetItem(str(book['id'])))

            # Название
            self.table_books.setItem(row, 1, QTableWidgetItem(book['title']))

            # Автор
            self.table_books.setItem(row, 2, QTableWidgetItem(book['author']))

            # Жанр
            genre = book.get('genre_name', 'Не указан')
            self.table_books.setItem(row, 3, QTableWidgetItem(genre))

            # Статус
            status_item = QTableWidgetItem(book['status'])
            # Раскрашиваем статусы
            if book['status'] == 'Прочитано':
                status_item.setBackground(Qt.GlobalColor.green)
            elif book['status'] == 'Читаю':
                status_item.setBackground(Qt.GlobalColor.yellow)
            elif book['status'] == 'Хочу прочитать':
                status_item.setBackground(Qt.GlobalColor.blue)
            elif book['status'] == 'Отложено':
                status_item.setBackground(Qt.GlobalColor.red)
            self.table_books.setItem(row, 4, status_item)

            # Дата начала
            start_date = book['start_date'] or ''
            self.table_books.setItem(row, 5, QTableWidgetItem(start_date))

            # Дата окончания
            finish_date = book['finish_date'] or ''
            self.table_books.setItem(row, 6, QTableWidgetItem(finish_date))

            # Оценка
            rating = book['rating'] or ''
            if rating:
                rating_item = QTableWidgetItem("★" * rating)
                rating_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_books.setItem(row, 7, rating_item)
            else:
                self.table_books.setItem(row, 7, QTableWidgetItem(''))

            # Страницы
            pages = book.get('pages', 0) or 0
            self.table_books.setItem(row, 8, QTableWidgetItem(str(pages)))

        # Обновляем статус бар
        self.statusbar.showMessage(f"Найдено книг: {len(books)}")

    def on_book_selected(self, current_row, current_column, previous_row, previous_column):
        """Обрабатывает выбор книги в таблице"""
        if current_row < 0:  # Если строка не выбрана
            return

        book_id_item = self.table_books.item(current_row, 0)
        if not book_id_item:
            return

        book_id = int(book_id_item.text())
        self.current_book_id = book_id

        # Загружаем детальную информацию
        book = self.db.get_book(book_id)
        if book:
            self.show_book_details(book)

    def show_book_details(self, book):
        """Показывает детальную информацию о книге"""
        # Основная информация
        self.lbl_title.setText(book['title'])
        self.lbl_author.setText(book['author'])
        self.lbl_genre.setText(book.get('genre_name', 'Не указан'))

        # Даты
        dates = []
        if book['start_date']:
            dates.append(f"Начало: {book['start_date']}")
        if book['finish_date']:
            dates.append(f"Окончание: {book['finish_date']}")
        self.lbl_dates.setText("\n".join(dates) if dates else "Не указаны")

        # Оценка
        if book['rating']:
            self.lbl_rating.setText("★" * book['rating'])
        else:
            self.lbl_rating.setText("Нет оценки")

        # Статус
        self.lbl_status.setText(book['status'])

        # Страницы
        pages = book.get('pages', 0) or 0
        self.lbl_pages.setText(str(pages))

        # Отзыв
        self.text_review.setText(book['review'] or "")

        # Обложка
        if book['cover_image']:
            pixmap = QPixmap()
            pixmap.loadFromData(book['cover_image'])
            self.lbl_cover.setPixmap(pixmap.scaled(200, 300, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            self.lbl_cover.setText("Нет обложки")

    def add_book(self):
        """Добавляет новую книгу"""
        dialog = AddBookDialog(self.db, self)
        if dialog.exec():
            self.load_books()
            self.statusbar.showMessage("Книга успешно добавлена", 3000)

    def edit_book(self):
        """Редактирует выбранную книгу"""
        if not self.current_book_id:
            QMessageBox.warning(self, "Предупреждение", "Выберите книгу для редактирования")
            return

        dialog = AddBookDialog(self.db, self, self.current_book_id)
        if dialog.exec():
            self.load_books()
            self.statusbar.showMessage("Книга успешно обновлена", 3000)

    def delete_book(self):
        """Удаляет выбранную книгу"""
        if not self.current_book_id:
            QMessageBox.warning(self, "Предупреждение", "Выберите книгу для удаления")
            return

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить эту книгу?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_book(self.current_book_id):
                self.current_book_id = None
                self.load_books()
                self.statusbar.showMessage("Книга успешно удалена", 3000)
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось удалить книгу")

    def show_statistics(self):
        """Показывает диалог статистики"""
        dialog = StatisticsDialog(self.db, self)
        dialog.exec()

    def export_data(self):
        """Экспортирует данные в CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт данных", "", "CSV Files (*.csv)"
        )

        if file_path:
            if self.db.export_to_csv(file_path):
                QMessageBox.information(self, "Успех", f"Данные экспортированы в {file_path}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось экспортировать данные")

    def import_data(self):
        """Импортирует данные из CSV"""
        QMessageBox.information(self, "Информация",
                                "Функция импорта будет реализована в следующей версии")

    def show_about(self):
        """Показывает информацию о программе"""
        about_text = """
        <h2>Читательский дневник</h2>
        <p>Версия 1.0.0</p>
        <p>Программа для ведения учета прочитанных книг.</p>
        <p>Возможности:</p>
        <ul>
            <li>Добавление и редактирование книг</li>
            <li>Ведение отзывов и заметок</li>
            <li>Загрузка обложек книг</li>
            <li>Статистика чтения</li>
            <li>Экспорт данных в CSV</li>
        </ul>
        <p>© 2025 Читательский дневник</p>
        """
        QMessageBox.about(self, "О программе", about_text)

    def show_context_menu(self, position):
        """Показывает контекстное меню для таблицы"""
        # Получаем элемент по позиции
        item = self.table_books.itemAt(position)
        if item:
            # Выделяем строку, на которой было вызвано меню
            self.table_books.selectRow(item.row())

        menu = QMenu()

        add_action = menu.addAction("Добавить книгу")
        edit_action = menu.addAction("Редактировать")
        delete_action = menu.addAction("Удалить")

        action = menu.exec(self.table_books.mapToGlobal(position))

        if action == add_action:
            self.add_book()
        elif action == edit_action:
            self.edit_book()
        elif action == delete_action:
            self.delete_book()