# test_app.py
import unittest
import psycopg2

# Добавляем модуль для измерения покрытия кода
import coverage

# Инициализируем coverage ДО импорта тестируемых модулей
cov = coverage.Coverage(
    include='src/kurwithGUI.py',  # Указываем, за каким файлом следить
    omit='*test_*.py'  # Игнорируем тестовые файлы
)
cov.start()  # Начинаем сбор данных о покрытии

from kurwithGUI import (
    init_db,
    add_employee,
    get_employees,
    add_category,
    get_categories,
    add_competency,
    get_competencies_by_category,
    add_survey,
    add_survey_score,
    get_survey_results
)


class TestDBFunctions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Выполняется один раз перед всеми тестами.
        Здесь подключаемся к БД и инициализируем схему.
        """
        try:
            cls.conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="competencies",
                user="user1",
                password="admin1"
            )
        except Exception as e:
            raise Exception(f"Ошибка подключения к БД: {e}")

        init_db(cls.conn)  # Создаем таблицы

    @classmethod
    def tearDownClass(cls):
        """
        Выполняется после всех тестов.
        Закрываем соединение и генерируем отчет о покрытии.
        """
        cls.conn.close()

        # Останавливаем сбор данных и сохраняем отчет
        cov.stop()
        cov.save()
        print("\nОтчет о покрытии кода:")
        cov.report()  # Вывод в консоль
        cov.html_report(directory='htmlcov')  # Генерация HTML

    def setUp(self):
        """
        Выполняется перед КАЖДЫМ тестом.
        Очищаем данные в таблицах.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            TRUNCATE TABLE 
                survey_scores, surveys, 
                competencies, categories, 
                employees RESTART IDENTITY CASCADE;
        """)
        self.conn.commit()

    # Тесты остаются без изменений, но добавлены комментарии
    def test_add_employee(self):
        """Тестируем добавление сотрудника"""
        emp_id = add_employee(self.conn, "Иван Петров")
        employees = get_employees(self.conn)

        self.assertEqual(len(employees), 1)
        self.assertEqual(employees[0][1], "Иван Петров")

    def test_add_category_and_competency(self):
        """Тестируем добавление категории и компетенции"""
        # Добавляем категорию
        cat_id = add_category(self.conn, "Программирование")
        self.assertIsNotNone(cat_id)

        # Добавляем компетенцию
        comp_id = add_competency(self.conn, "Python", cat_id)
        comps = get_competencies_by_category(self.conn, cat_id)

        self.assertEqual(len(comps), 1)
        self.assertEqual(comps[0][1], "Python")

    def test_full_survey_flow(self):
        """Полный тест цикла опроса"""
        # 1. Добавляем данные
        emp_id = add_employee(self.conn, "Анна Сидорова")
        cat_id = add_category(self.conn, "Тестирование")
        comp_id = add_competency(self.conn, "Pytest", cat_id)

        # 2. Создаем опрос
        survey_id = add_survey(self.conn, emp_id, "2024-Q1")
        add_survey_score(self.conn, survey_id, comp_id, 4.5)

        # 3. Проверяем результаты
        results = get_survey_results(self.conn)

        self.assertIn("Анна Сидорова", results)
        self.assertIn("Тестирование - Pytest: 4.5", results)


# Кастомные классы для красивого вывода (без изменений)
class VerboseTestResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        self.stream.writeln(f"✅ УСПЕХ: {test._testMethodName}")


class VerboseTestRunner(unittest.TextTestRunner):
    resultclass = VerboseTestResult


if __name__ == '__main__':
    # Запуск с кастомным runner и максимальной детализацией
    unittest.main(
        testRunner=VerboseTestRunner,
        verbosity=2,
        # Можно указать конкретные тесты для запуска:
        # argv=['', 'TestDBFunctions.test_add_employee']
    )