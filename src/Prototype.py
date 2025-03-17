import sys

class Employee:
    """
    Класс для представления сотрудника.
    Каждый сотрудник имеет имя и оценки по компетенциям.
    """
    def __init__(self, name):
        self.name = name
        self.competencies = {}  # словарь: название компетенции -> оценка

    def add_competency(self, competency, score):
        """Добавляет или обновляет оценку по указанной компетенции."""
        self.competencies[competency] = score

    def evaluate(self):
        """Вычисляет общую оценку сотрудника (среднее значение оценок по компетенциям)."""
        if self.competencies:
            return sum(self.competencies.values()) / len(self.competencies)
        return 0

    def __str__(self):
        comp_scores = ", ".join([f"{comp}: {score}" for comp, score in self.competencies.items()])
        overall = self.evaluate()
        return f"Сотрудник: {self.name}\n  Оценки: {comp_scores}\n  Общая оценка: {overall:.2f}\n"


def main():
    employees = []
    # Предопределённый список компетенций для оценки
    competencies_list = ["Коммуникация", "Работа в команде", "Решение проблем", "Лидерство"]

    while True:
        print("Меню:")
        print("1. Добавить сотрудника")
        print("2. Провести оценку сотрудника")
        print("3. Показать всех сотрудников")
        print("4. Выход")

        choice = input("Выберите пункт меню: ").strip()

        if choice == '1':
            name = input("Введите имя сотрудника: ").strip()
            if name:
                employee = Employee(name)
                employees.append(employee)
                print("Сотрудник добавлен.\n")
            else:
                print("Имя не может быть пустым.\n")

        elif choice == '2':
            if not employees:
                print("Нет сотрудников для оценки. Сначала добавьте сотрудника.\n")
                continue

            print("Список сотрудников:")
            for idx, employee in enumerate(employees, start=1):
                print(f"{idx}. {employee.name}")
            emp_choice = input("Выберите сотрудника для оценки (номер): ").strip()
            try:
                emp_index = int(emp_choice) - 1
                if emp_index < 0 or emp_index >= len(employees):
                    print("Неверный выбор.\n")
                    continue
            except ValueError:
                print("Неверный ввод. Пожалуйста, введите число.\n")
                continue

            selected_employee = employees[emp_index]
            print(f"\nВведите оценки по следующим компетенциям (оценка от 1 до 5):")
            for competency in competencies_list:
                while True:
                    try:
                        score_input = input(f"{competency}: ").strip()
                        score = float(score_input)
                        if 1 <= score <= 5:
                            selected_employee.add_competency(competency, score)
                            break
                        else:
                            print("Оценка должна быть от 1 до 5.")
                    except ValueError:
                        print("Неверный ввод. Введите числовое значение.")
            overall = selected_employee.evaluate()
            print(f"\nОбщая оценка для {selected_employee.name}: {overall:.2f}\n")

        elif choice == '3':
            if not employees:
                print("Нет сотрудников для отображения.\n")
            else:
                print("\nСписок сотрудников с оценками:")
                for employee in employees:
                    print(employee)
            print()

        elif choice == '4':
            print("Выход из приложения.")
            sys.exit(0)

        else:
            print("Неверный выбор. Повторите ввод.\n")


if __name__ == '__main__':
    main()
