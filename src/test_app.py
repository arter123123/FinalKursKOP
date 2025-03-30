# test_app.py
import unittest
import psycopg2
import os
import sys

# Импортируем coverage ПЕРЕД импортом тестируемых модулей
import coverage

# Настраиваем coverage перед импортом приложения
cov = coverage.Coverage(
    source=['.'],  # Отслеживаем все файлы в текущей директории
    omit=[
        '*test_*.py',  # Исключаем тестовые файлы
        '*/site-packages/*'  # Исключаем системные зависимости
    ]
)
cov.start()

# Теперь импортируем тестируемые модули
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
        """Инициализация тестовой БД"""
        try:
            cls.conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="competencies",
                user="user1",
                password="admin1"
            )
            init_db(cls.conn)
        except Exception as e:
            raise Exception(f"Database connection failed: {str(e)}")

    @classmethod
    def tearDownClass(cls):
        """Завершение работы с coverage и закрытие соединения"""
        cls.conn.close()
        cov.stop()
        cov.save()

        # Генерация отчетов
        print("\nCoverage Report:")
        cov.report()
        cov.html_report(directory='htmlcov')
        print("HTML report generated in 'htmlcov' directory")

    def setUp(self):
        """Очистка данных перед каждым тестом"""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                TRUNCATE TABLE 
                    survey_scores, surveys, 
                    competencies, categories, 
                    employees RESTART IDENTITY CASCADE;
            """)
            self.conn.commit()

    def test_add_employee(self):
        """Тест добавления сотрудника"""
        emp_id = add_employee(self.conn, "John Doe")
        employees = get_employees(self.conn)
        self.assertEqual(len(employees), 1)
        self.assertEqual(employees[0][1], "John Doe")

    def test_add_category_and_competency(self):
        """Тест добавления категории и компетенции"""
        # Тест категории
        cat_id = add_category(self.conn, "Programming")
        self.assertIsNotNone(cat_id)

        # Тест компетенции
        comp_id = add_competency(self.conn, "Python", cat_id)
        comps = get_competencies_by_category(self.conn, cat_id)
        self.assertEqual(comps[0][1], "Python")

    def test_full_workflow(self):
        """Полный тест рабочего процесса"""
        # Добавляем данные
        emp_id = add_employee(self.conn, "Alice Smith")
        cat_id = add_category(self.conn, "Testing")
        comp_id = add_competency(self.conn, "Pytest", cat_id)

        # Создаем опрос
        survey_id = add_survey(self.conn, emp_id, "2024-Q1")
        add_survey_score(self.conn, survey_id, comp_id, 4.5)

        # Проверяем результаты
        results = get_survey_results(self.conn)
        self.assertIn("Alice Smith", results)
        self.assertIn("Pytest", results)
        self.assertIn("4.5", results)


class CustomTestRunner(unittest.TextTestRunner):
    """Кастомный runner для улучшенного вывода"""
    resultclass = unittest.TextTestResult

    def run(self, test):
        result = super().run(test)
        print("\n" + "=" * 50)
        print(f"Tests run: {result.testsRun}")
        print(f"Errors: {len(result.errors)}")
        print(f"Failures: {len(result.failures)}")
        return result


if __name__ == '__main__':
    # Запуск с кастомным runner
    unittest.main(
        testRunner=CustomTestRunner,
        verbosity=2,
        exit=False
    )