import unittest
import psycopg2
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
        # Подключаемся к тестовой базе данных.
        # Создайте базу данных competencies_test в PostgreSQL, чтобы тесты не влияли на основную базу.
        try:
            cls.conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="competencies",  # имя базы данных, указанное при запуске Docker-контейнера
            user="user1",  # замените на ваше имя пользователя (POSTGRES_USER)
            password="admin1"  # замените на ваш пароль (POSTGRES_PASSWORD)
        )
        except Exception as e:
            raise Exception("Ошибка подключения к тестовой базе данных: " + str(e))
        init_db(cls.conn)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def setUp(self):
        # Перед каждым тестом очищаем все данные
        cursor = self.conn.cursor()
        cursor.execute("""
            TRUNCATE TABLE survey_scores, surveys, competencies, categories, employees 
            RESTART IDENTITY CASCADE;
        """)
        self.conn.commit()

    def test_add_employee(self):
        emp_id = add_employee(self.conn, "Test Employee")
        print("Добавлен сотрудник с ID:", emp_id)
        self.assertIsInstance(emp_id, int)
        employees = get_employees(self.conn)
        print("Текущие сотрудники:", employees)
        self.assertEqual(len(employees), 1)
        self.assertEqual(employees[0][1], "Test Employee")

    def test_add_category_and_competency(self):
        cat_id = add_category(self.conn, "Test Category")
        print("Добавлена категория с ID:", cat_id)
        self.assertIsInstance(cat_id, int)
        cats = get_categories(self.conn)
        print("Текущие категории:", cats)
        self.assertEqual(len(cats), 1)
        self.assertEqual(cats[0][1], "Test Category")

        comp_id = add_competency(self.conn, "Test Competency", cat_id)
        print("Добавлена компетенция с ID:", comp_id)
        self.assertIsInstance(comp_id, int)
        comps = get_competencies_by_category(self.conn, cat_id)
        print("Компетенции для категории Test Category:", comps)
        self.assertEqual(len(comps), 1)
        self.assertEqual(comps[0][1], "Test Competency")

    def test_add_survey_and_results(self):
        # Добавляем сотрудника, категорию и компетенцию
        emp_id = add_employee(self.conn, "Employee 1")
        cat_id = add_category(self.conn, "Category 1")
        comp_id = add_competency(self.conn, "Competency 1", cat_id)

        period = "2025-Q1"
        survey_id = add_survey(self.conn, emp_id, period)
        print("Добавлен опрос с ID:", survey_id, "для сотрудника", emp_id, "за период", period)
        self.assertIsInstance(survey_id, int)

        # Добавляем оценку
        add_survey_score(self.conn, survey_id, comp_id, 4.0)
        print("Добавлена оценка 4.0 для компетенции", comp_id)

        results = get_survey_results(self.conn)
        print("Результаты опросов:\n", results)
        self.assertIn("Employee 1", results)
        self.assertIn("2025-Q1", results)
        self.assertIn("Category 1", results)
        self.assertIn("Competency 1", results)
        self.assertIn("4", results)


# Кастомный класс TestResult, который выводит сообщение об успешном выполнении каждого теста.
class VerboseTestResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        self.stream.writeln("TEST PASSED: " + str(test))


# Кастомный TestRunner, использующий VerboseTestResult.
class VerboseTestRunner(unittest.TextTestRunner):
    resultclass = VerboseTestResult


if __name__ == '__main__':
    unittest.main(testRunner=VerboseTestRunner, verbosity=2)
