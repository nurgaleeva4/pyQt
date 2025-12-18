import os
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidgetItem, QLabel
from PyQt6.QtCore import Qt
from PyQt6 import uic
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from datetime import datetime


class StatisticsDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db

        # Загружаем интерфейс
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'qt', 'statistics_dialog.ui')
        uic.loadUi(ui_path, self)

        self.setup_ui()
        self.load_statistics()

    def setup_ui(self):
        """Настраивает интерфейс"""
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # Настраиваем таблицы
        self.table_genres.setColumnCount(3)
        self.table_genres.setHorizontalHeaderLabels(["Жанр", "Количество", "%"])

        self.table_ratings.setColumnCount(2)
        self.table_ratings.setHorizontalHeaderLabels(["Оценка", "Количество"])

    def load_statistics(self):
        """Загружает статистику"""
        stats = self.db.get_statistics()

        # Общая статистика
        self.lbl_total_books.setText(str(stats['total']))
        self.lbl_read_books.setText(str(stats['read_count']))
        self.lbl_reading_books.setText(str(stats['reading_count']))
        self.lbl_wishlist_books.setText(str(stats['wishlist_count']))
        self.lbl_avg_rating.setText(str(stats['avg_rating']))
        self.lbl_total_pages.setText(str(stats['total_pages']))

        # Примерные расчеты
        if stats['read_count'] > 0:
            self.lbl_reading_days.setText(str(stats['read_count'] * 14))  # По 14 дней на книгу
            self.lbl_books_this_year.setText(str(stats['read_count']))  # Упрощенный расчет
        else:
            self.lbl_reading_days.setText("0")
            self.lbl_books_this_year.setText("0")

        # График чтения по месяцам
        self.create_monthly_chart(stats['monthly_stats'])

        # Статистика по жанрам
        self.load_genres_stats(stats['genres_stats'])

        # Статистика по оценкам
        self.load_ratings_stats(stats['ratings_stats'])

    def create_monthly_chart(self, monthly_stats):
        """Создает простой график чтения по месяцам"""
        # Очищаем предыдущий график
        for i in reversed(range(self.widget_chart.layout().count() if self.widget_chart.layout() else 0)):
            widget = self.widget_chart.layout().itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if not monthly_stats:
            # Если нет данных, показываем сообщение
            layout = QVBoxLayout(self.widget_chart)
            label = QLabel("Нет данных для графика")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            return

        # Создаем простой график
        fig = Figure(figsize=(6, 4))
        canvas = FigureCanvas(fig)

        ax = fig.add_subplot(111)

        # Подготавливаем данные
        months = [item['month'] for item in monthly_stats]
        counts = [item['count'] for item in monthly_stats]

        # Простая столбчатая диаграмма
        bars = ax.bar(range(len(months)), counts, color='lightblue')

        # Простые подписи
        ax.set_xlabel('Месяц')
        ax.set_ylabel('Количество книг')
        ax.set_title('Чтение по месяцам')

        # Простые подписи месяцев
        if len(months) <= 12:
            # Если месяцев немного, показываем все
            ax.set_xticks(range(len(months)))
            ax.set_xticklabels(months, rotation=45)
        else:
            # Если много месяцев, показываем каждый 3-й
            ax.set_xticks(range(0, len(months), 3))
            ax.set_xticklabels(months[::3], rotation=45)

        # Добавляем значения на столбцы (только если их немного)
        if len(bars) <= 15:
            for bar in bars:
                height = bar.get_height()
                if height > 0:  # Только если есть значение
                    ax.text(bar.get_x() + bar.get_width() / 2., height,
                            f'{int(height)}', ha='center', va='bottom')

        fig.tight_layout()

        # Встраиваем в Qt виджет
        layout = QVBoxLayout(self.widget_chart)
        layout.addWidget(canvas)

    def load_genres_stats(self, genres_stats):
        """Загружает статистику по жанрам"""
        total = sum(item['count'] for item in genres_stats if item['count'] > 0)

        self.table_genres.setRowCount(len(genres_stats))

        row = 0
        for genre_stat in genres_stats:
            genre = genre_stat['genre']
            count = genre_stat['count'] or 0

            # Только жанры с книгами
            if count == 0:
                continue

            percentage = (count / total * 100) if total > 0 else 0

            self.table_genres.setItem(row, 0, QTableWidgetItem(genre))
            self.table_genres.setItem(row, 1, QTableWidgetItem(str(count)))
            self.table_genres.setItem(row, 2, QTableWidgetItem(f"{percentage:.1f}%"))
            row += 1

        # Создаем простую круговую диаграмму
        self.create_pie_chart(genres_stats)

    def create_pie_chart(self, genres_stats):
        """Создает простую круговую диаграмму по жанрам"""
        # Очищаем предыдущий график
        for i in reversed(range(self.widget_pie_chart.layout().count() if self.widget_pie_chart.layout() else 0)):
            widget = self.widget_pie_chart.layout().itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Фильтруем только жанры с книгами
        filtered_stats = [item for item in genres_stats if item['count'] and item['count'] > 0]
        if not filtered_stats:
            # Если нет данных, показываем сообщение
            layout = QVBoxLayout(self.widget_pie_chart)
            label = QLabel("Нет данных для диаграммы")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            return

        # Подготавливаем данные
        labels = [item['genre'] for item in filtered_stats]
        sizes = [item['count'] for item in filtered_stats]

        # Создаем диаграмму
        fig = Figure(figsize=(5, 5))
        canvas = FigureCanvas(fig)

        ax = fig.add_subplot(111)

        # Простая круговая диаграмма
        wedges, texts, autotexts = ax.pie(sizes,
                                          labels=labels,
                                          autopct='%1.1f%%',
                                          startangle=90)

        ax.set_title('Распределение по жанрам')

        # Делаем подписи меньше
        for autotext in autotexts:
            autotext.set_fontsize(8)

        for text in texts:
            text.set_fontsize(8)

        fig.tight_layout()

        # Встраиваем в Qt виджет
        layout = QVBoxLayout(self.widget_pie_chart)
        layout.addWidget(canvas)

    def load_ratings_stats(self, ratings_stats):
        """Загружает статистику по оценкам"""
        self.table_ratings.setRowCount(len(ratings_stats))

        for row, rating_stat in enumerate(ratings_stats):
            rating = rating_stat['rating']
            count = rating_stat['count']

            self.table_ratings.setItem(row, 0, QTableWidgetItem("★" * rating))
            self.table_ratings.setItem(row, 1, QTableWidgetItem(str(count)))

        # Создаем простую столбчатую диаграмму
        self.create_bar_chart(ratings_stats)

    def create_bar_chart(self, ratings_stats):
        """Создает простую столбчатую диаграмму оценок"""
        # Очищаем предыдущий график
        for i in reversed(range(self.widget_bar_chart.layout().count() if self.widget_bar_chart.layout() else 0)):
            widget = self.widget_bar_chart.layout().itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if not ratings_stats:
            # Если нет данных, показываем сообщение
            layout = QVBoxLayout(self.widget_bar_chart)
            label = QLabel("Нет данных для графика")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            return

        # Подготавливаем данные
        ratings = [item['rating'] for item in ratings_stats]
        counts = [item['count'] for item in ratings_stats]
        labels = ["★" * r for r in ratings]

        # Создаем диаграмму
        fig = Figure(figsize=(5, 5))
        canvas = FigureCanvas(fig)

        ax = fig.add_subplot(111)

        # Простая столбчатая диаграмма
        colors = ['gold', 'silver', 'lightblue', 'lightgreen', 'pink']
        bars = ax.bar(labels, counts, color=colors[:len(ratings)])

        ax.set_xlabel('Оценка')
        ax.set_ylabel('Количество книг')
        ax.set_title('Распределение оценок')

        # Добавляем значения на столбцы
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{int(height)}', ha='center', va='bottom')

        fig.tight_layout()

        # Встраиваем в Qt виджет
        layout = QVBoxLayout(self.widget_bar_chart)
        layout.addWidget(canvas)