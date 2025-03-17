import tkinter as tk
from tkinter import messagebox, ttk
import psycopg2
import sys


# Функции для работы с базой данных PostgreSQL

def init_db(conn):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL UNIQUE
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS competencies (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
        UNIQUE(name, category_id)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS surveys (
        id SERIAL PRIMARY KEY,
        employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
        period TEXT NOT NULL
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS survey_scores (
        id SERIAL PRIMARY KEY,
        survey_id INTEGER NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
        competency_id INTEGER NOT NULL REFERENCES competencies(id) ON DELETE CASCADE,
        score REAL NOT NULL
    );
    """)
    conn.commit()


def add_employee(conn, name):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO employees (name) VALUES (%s) RETURNING id;", (name,))
    emp_id = cursor.fetchone()[0]
    conn.commit()
    return emp_id


def get_employees(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM employees;")
    return cursor.fetchall()


def add_category(conn, name):
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (%s) RETURNING id;", (name,))
        cat_id = cursor.fetchone()[0]
        conn.commit()
        return cat_id
    except psycopg2.IntegrityError:
        conn.rollback()
        return None


def get_categories(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM categories;")
    return cursor.fetchall()


def add_competency(conn, name, category_id):
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO competencies (name, category_id) VALUES (%s, %s) RETURNING id;",
                       (name, category_id))
        comp_id = cursor.fetchone()[0]
        conn.commit()
        return comp_id
    except psycopg2.IntegrityError:
        conn.rollback()
        return None


def get_competencies_by_category(conn, category_id):
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM competencies WHERE category_id=%s;", (category_id,))
    return cursor.fetchall()


def add_survey(conn, employee_id, period):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO surveys (employee_id, period) VALUES (%s, %s) RETURNING id;", (employee_id, period))
    survey_id = cursor.fetchone()[0]
    conn.commit()
    return survey_id


def add_survey_score(conn, survey_id, competency_id, score):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO survey_scores (survey_id, competency_id, score) VALUES (%s, %s, %s);",
                   (survey_id, competency_id, score))
    conn.commit()


def get_survey_results(conn):
    cursor = conn.cursor()
    cursor.execute("""
    SELECT s.id, e.name, s.period, cat.name, comp.name, ss.score
    FROM surveys s
    JOIN employees e ON s.employee_id = e.id
    JOIN survey_scores ss ON ss.survey_id = s.id
    JOIN competencies comp ON ss.competency_id = comp.id
    JOIN categories cat ON comp.category_id = cat.id
    ORDER BY s.id;
    """)
    rows = cursor.fetchall()
    if not rows:
        return "Нет данных об опросах."

    results = ""
    surveys = {}
    for row in rows:
        survey_id, employee_name, period, cat_name, comp_name, score = row
        if survey_id not in surveys:
            surveys[survey_id] = {
                'employee_name': employee_name,
                'period': period,
                'scores': []
            }
        surveys[survey_id]['scores'].append((cat_name, comp_name, score))
    for survey_id, data in surveys.items():
        results += f"\nОпрос ID: {survey_id} | Сотрудник: {data['employee_name']} | Период: {data['period']}\n"
        cat_totals = {}
        cat_counts = {}
        for cat_name, comp_name, score in data['scores']:
            results += f"  {cat_name} - {comp_name}: {score}\n"
            cat_totals[cat_name] = cat_totals.get(cat_name, 0) + score
            cat_counts[cat_name] = cat_counts.get(cat_name, 0) + 1
        results += "Средние оценки по категориям:\n"
        overall_total = 0
        overall_count = 0
        for cat, total in cat_totals.items():
            avg = total / cat_counts[cat]
            results += f"  {cat}: {avg:.2f}\n"
            overall_total += total
            overall_count += cat_counts[cat]
        overall_avg = overall_total / overall_count if overall_count else 0
        results += f"Общая оценка: {overall_avg:.2f}\n"
    return results


# Графический интерфейс на основе Tkinter

class App(tk.Tk):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.title("Оценка компетенций сотрудников")
        self.geometry("400x300")

        # Основное меню
        btn_add_employee = tk.Button(self, text="Добавить сотрудника", command=self.open_add_employee)
        btn_add_employee.pack(pady=10)

        btn_conduct_survey = tk.Button(self, text="Провести опрос", command=self.open_conduct_survey)
        btn_conduct_survey.pack(pady=10)

        btn_show_results = tk.Button(self, text="Показать результаты опросов", command=self.open_show_results)
        btn_show_results.pack(pady=10)

        btn_manage_categories = tk.Button(self, text="Управление категориями и компетенциями",
                                          command=self.open_manage_categories)
        btn_manage_categories.pack(pady=10)

        btn_exit = tk.Button(self, text="Выход", command=self.quit)
        btn_exit.pack(pady=10)

    def open_add_employee(self):
        win = tk.Toplevel(self)
        win.title("Добавить сотрудника")
        tk.Label(win, text="Имя сотрудника:").pack(pady=5)
        entry_name = tk.Entry(win)
        entry_name.pack(pady=5)

        def add_emp():
            name = entry_name.get().strip()
            if name:
                add_employee(self.conn, name)
                messagebox.showinfo("Успех", "Сотрудник добавлен.")
                win.destroy()
            else:
                messagebox.showerror("Ошибка", "Имя не может быть пустым.")

        tk.Button(win, text="Добавить", command=add_emp).pack(pady=10)

    def open_conduct_survey(self):
        win = tk.Toplevel(self)
        win.title("Провести опрос")
        # Выбор сотрудника
        tk.Label(win, text="Выберите сотрудника:").pack(pady=5)
        employees = get_employees(self.conn)
        if not employees:
            messagebox.showerror("Ошибка", "Нет сотрудников. Сначала добавьте сотрудника.")
            win.destroy()
            return
        emp_names = [f"{emp[1]} (ID: {emp[0]})" for emp in employees]
        emp_ids = [emp[0] for emp in employees]
        selected_emp = tk.StringVar()
        combo_emp = ttk.Combobox(win, textvariable=selected_emp, values=emp_names, state="readonly")
        combo_emp.pack(pady=5)
        combo_emp.current(0)

        # Ввод года и выбор квартала
        tk.Label(win, text="Введите год опроса (например, 2025):").pack(pady=5)
        entry_year = tk.Entry(win)
        entry_year.pack(pady=5)

        tk.Label(win, text="Выберите квартал:").pack(pady=5)
        quarter_var = tk.StringVar()
        quarter_combo = ttk.Combobox(win, textvariable=quarter_var, values=["Q1", "Q2", "Q3", "Q4"], state="readonly")
        quarter_combo.pack(pady=5)
        quarter_combo.current(0)

        # Фрейм для ввода оценок
        frame_scores = tk.Frame(win)
        frame_scores.pack(pady=10, fill="both", expand=True)

        # Получаем категории и компетенции
        categories = get_categories(self.conn)
        self.score_entries = {}  # {id компетенции: виджет Entry}
        for cat in categories:
            competencies = get_competencies_by_category(self.conn, cat[0])
            if competencies:
                lbl_cat = tk.Label(frame_scores, text=f"Категория: {cat[1]}", font=("Arial", 10, "bold"))
                lbl_cat.pack(anchor="w", pady=(5, 0))
                for comp in competencies:
                    frame_comp = tk.Frame(frame_scores)
                    frame_comp.pack(anchor="w", pady=2, fill="x")
                    tk.Label(frame_comp, text=f"{comp[1]}:").pack(side="left")
                    entry_score = tk.Entry(frame_comp, width=5)
                    entry_score.pack(side="left", padx=5)
                    self.score_entries[comp[0]] = entry_score

        def submit_survey():
            year = entry_year.get().strip()
            if not (year.isdigit() and len(year) == 4):
                messagebox.showerror("Ошибка", "Введите корректный год (4 цифры).")
                return
            period = f"{year}-{quarter_var.get().strip()}"
            emp_index = combo_emp.current()
            employee_id = emp_ids[emp_index]
            survey_id = add_survey(self.conn, employee_id, period)
            # Сохраняем оценки
            for comp_id, entry in self.score_entries.items():
                try:
                    score = float(entry.get().strip())
                    if 1 <= score <= 5:
                        add_survey_score(self.conn, survey_id, comp_id, score)
                    else:
                        messagebox.showerror("Ошибка", "Оценка должна быть от 1 до 5.")
                        return
                except ValueError:
                    messagebox.showerror("Ошибка", "Введите числовое значение для оценки.")
                    return
            messagebox.showinfo("Успех", "Опрос проведён.")
            win.destroy()

        tk.Button(win, text="Провести опрос", command=submit_survey).pack(pady=10)

    def open_show_results(self):
        win = tk.Toplevel(self)
        win.title("Результаты опросов")
        text = tk.Text(win, wrap="word", width=80, height=20)
        text.pack(padx=10, pady=10)
        results = get_survey_results(self.conn)
        text.insert("1.0", results)
        text.config(state="disabled")

    def open_manage_categories(self):
        win = tk.Toplevel(self)
        win.title("Управление категориями и компетенциями")
        # Текстовое поле для отображения данных
        text = tk.Text(win, wrap="word", width=60, height=15)
        text.pack(padx=10, pady=10)

        def refresh_data():
            text.delete("1.0", tk.END)
            cats = get_categories(self.conn)
            if not cats:
                text.insert(tk.END, "Нет категорий.\n")
            else:
                for cat in cats:
                    text.insert(tk.END, f"Категория: {cat[1]} (ID: {cat[0]})\n")
                    comps = get_competencies_by_category(self.conn, cat[0])
                    if comps:
                        for comp in comps:
                            text.insert(tk.END, f"    - {comp[1]} (ID: {comp[0]})\n")
                    else:
                        text.insert(tk.END, "    (нет компетенций)\n")

        refresh_data()

        def add_cat():
            win_cat = tk.Toplevel(win)
            win_cat.title("Добавить категорию")
            tk.Label(win_cat, text="Название категории:").pack(pady=5)
            entry_cat = tk.Entry(win_cat)
            entry_cat.pack(pady=5)

            def submit_cat():
                name = entry_cat.get().strip()
                if name:
                    if add_category(self.conn, name):
                        messagebox.showinfo("Успех", "Категория добавлена.")
                        win_cat.destroy()
                        refresh_data()
                    else:
                        messagebox.showerror("Ошибка", "Категория с таким именем уже существует.")
                else:
                    messagebox.showerror("Ошибка", "Название не может быть пустым.")

            tk.Button(win_cat, text="Добавить", command=submit_cat).pack(pady=10)

        def add_comp():
            win_comp = tk.Toplevel(win)
            win_comp.title("Добавить компетенцию")
            tk.Label(win_comp, text="Выберите категорию:").pack(pady=5)
            cats = get_categories(self.conn)
            if not cats:
                messagebox.showerror("Ошибка", "Сначала добавьте категорию.")
                win_comp.destroy()
                return
            cat_names = [f"{cat[1]} (ID: {cat[0]})" for cat in cats]
            selected_cat = tk.StringVar()
            combo_cat = ttk.Combobox(win_comp, textvariable=selected_cat, values=cat_names, state="readonly")
            combo_cat.pack(pady=5)
            combo_cat.current(0)
            tk.Label(win_comp, text="Название компетенции:").pack(pady=5)
            entry_comp = tk.Entry(win_comp)
            entry_comp.pack(pady=5)

            def submit_comp():
                name = entry_comp.get().strip()
                if name:
                    cat_index = combo_cat.current()
                    category_id = cats[cat_index][0]
                    if add_competency(self.conn, name, category_id):
                        messagebox.showinfo("Успех", "Компетенция добавлена.")
                        win_comp.destroy()
                        refresh_data()
                    else:
                        messagebox.showerror("Ошибка", "Компетенция с таким именем уже существует в этой категории.")
                else:
                    messagebox.showerror("Ошибка", "Название не может быть пустым.")

            tk.Button(win_comp, text="Добавить", command=submit_comp).pack(pady=10)

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Добавить категорию", command=add_cat).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Добавить компетенцию", command=add_comp).pack(side="left", padx=5)


def main():
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="competencies",  # имя базы данных, указанное при запуске Docker-контейнера
            user="user1",  # замените на ваше имя пользователя (POSTGRES_USER)
            password="admin1"  # замените на ваш пароль (POSTGRES_PASSWORD)
        )
    except Exception as e:
        print("Ошибка подключения к базе данных:", e)
        sys.exit(1)

    init_db(conn)

    app = App(conn)
    app.mainloop()
    conn.close()


if __name__ == '__main__':
    main()
