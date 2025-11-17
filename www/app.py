from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import psycopg
import os
from functools import wraps

# --- ПОЧАТОК КОДУ З GRUD.PY (Для функцій БД) ---
# --- КОНФІГУРАЦІЯ БАЗИ ДАНИХ (ЗМІНІТЬ НА ВАШІ ДАНІ!) ---
DB_NAME = os.environ.get('DB_NAME', 'wdb')
DB_USER = os.environ.get('DB_USER', 'webadmin')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'admin')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')

# Рядок підключення у форматі URI
# ЗМІНІТЬ ЦЕЙ РЯДОК НА ВАШІ РЕАЛЬНІ ПАРАМЕТРИ ПІДКЛЮЧЕННЯ
CONN_STRING = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def get_connection():
    """Створює та повертає об'єкт підключення."""
    try:
        conn = psycopg.connect(CONN_STRING)
        return conn
    except psycopg.OperationalError as e:
        # print(f"Помилка підключення до бази даних: {e}")
        return None

# Функція для отримання всіх помічників (для головної сторінки)
def get_all_helpers():
    """Повертає всіх помічників з таблиці helperinfo."""
    sql = "SELECT helper_id, admin_name, admin_rank, warnings_count FROM public.helperinfo ORDER BY helper_id;"
    conn = get_connection()
    if conn is None: return [] # Повертаємо порожній список у разі помилки

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            # Отримуємо імена стовпців для коректного відображення в шаблоні
            column_names = [desc[0] for desc in cur.description]
            helpers = cur.fetchall()
            
            # Перетворюємо результат у список словників для зручної роботи в Jinja2
            data = []
            for row in helpers:
                data.append(dict(zip(column_names, row)))
            return data

    except Exception as e:
        # print(f"❌ Помилка читання даних helperinfo: {e}")
        return []
    finally:
        conn.close()

def get_helpers_by_search(search_query):
    """Повертає помічників, які відповідають search_query у будь-якому текстовому полі."""
    conn = get_connection()
    if conn is None: return []

    # НОВИЙ SQL-ЗАПИТ: Використовуємо OR для пошуку в кількох стовпцях.
    # Числові стовпці (ID, Попередження) перетворюємо на TEXT за допомогою CAST.
    sql = """
    SELECT helper_id, admin_name, admin_rank, warnings_count 
    FROM public.helperinfo 
    WHERE 
        admin_name ILIKE %s OR 
        admin_rank ILIKE %s OR
        CAST(warnings_count AS TEXT) ILIKE %s OR
        CAST(helper_id AS TEXT) ILIKE %s 
    ORDER BY helper_id;
    """
    # Шаблон пошуку, що підходить для всіх 4-х полів
    search_pattern = f"%{search_query}%" 
    
    # Створюємо кортеж параметрів, повторюючи шаблон 4 рази (для 4-х %s)
    params = (search_pattern, search_pattern, search_pattern, search_pattern)

    try:
        with conn.cursor() as cur:
            # cur.execute отримує кортеж з 4-ма елементами
            cur.execute(sql, params) 
            column_names = [desc[0] for desc in cur.description]
            helpers = cur.fetchall()
            
            data = []
            for row in helpers:
                data.append(dict(zip(column_names, row)))
            return data

    except Exception as e:
        print(f"❌ Помилка читання даних helperinfo з пошуком: {e}")
        return []
    finally:
        if conn: conn.close()

# НОВА ФУНКЦІЯ: Оновлення даних співробітника
def update_helper_data(helper_id, name, rank, warnings):
    """Оновлює дані співробітника в таблиці helperinfo."""
    sql = """
    UPDATE public.helperinfo
    SET admin_name = %s, admin_rank = %s, warnings_count = %s
    WHERE helper_id = %s;
    """
    conn = get_connection()
    if conn is None: return False

    try:
        with conn.cursor() as cur:
            cur.execute(sql, (name, rank, warnings, helper_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Помилка оновлення даних співробітника ID {helper_id}: {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

# НОВА ФУНКЦІЯ: Видалення співробітника
def delete_helper_data(helper_id):
    """Видаляє запис співробітника з таблиці helperinfo."""
    sql = "DELETE FROM public.helperinfo WHERE helper_id = %s;"
    conn = get_connection()
    if conn is None: return False

    try:
        with conn.cursor() as cur:
            cur.execute(sql, (helper_id,))
        conn.commit()
        return True
    except psycopg.errors.ForeignKeyViolation as e:
        # Обробка помилки, якщо є пов'язані тікети
        print(f"❌ Помилка: Неможливо видалити співробітника ID {helper_id}, оскільки він має пов'язані тікети. {e}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"❌ Помилка видалення співробітника ID {helper_id}: {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

# Функція для отримання всіх тікетів
def get_all_tickets():
    """Повертає всі тікети з таблиці ticketinfo."""
    sql = """
    SELECT 
        t.ticket_id, 
        t.submitter_username, 
        h.admin_name AS handler_name, 
        t.time_spent, 
        t.resolution_rating, 
        t.created_at, 
        t.closed_at
    FROM public.ticketinfo AS t
    LEFT JOIN public.helperinfo AS h ON t.handler_helper_id = h.helper_id
    ORDER BY t.ticket_id;
    """
    conn = get_connection()
    if conn is None: return []

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            column_names = [desc[0] for desc in cur.description]
            tickets = cur.fetchall()
            
            data = []
            for row in tickets:
                data.append(dict(zip(column_names, row)))
            return data
    except Exception as e:
        # print(f"❌ Помилка читання даних ticketinfo: {e}")
        return []
    finally:
        if conn: conn.close()

# НОВА ФУНКЦІЯ: Пошук тікетів за іменем заявника
def get_tickets_by_multi_search(search_query):
    """Повертає тікети, які відповідають search_query у кількох полях."""
    conn = get_connection()
    if conn is None: return []

    # НОВИЙ SQL-ЗАПИТ: 
    # Шукаємо по ID, submitter_username, admin_name (обробник), time_spent та resolution_rating.
    # Числові поля (ticket_id, time_spent, resolution_rating) перетворюємо на TEXT.
    sql = """
    SELECT 
        t.ticket_id, 
        t.submitter_username, 
        h.admin_name AS handler_name, 
        t.time_spent, 
        t.resolution_rating, 
        t.created_at, 
        t.closed_at
    FROM public.ticketinfo AS t
    LEFT JOIN public.helperinfo AS h ON t.handler_helper_id = h.helper_id
    WHERE 
        CAST(t.ticket_id AS TEXT) ILIKE %s OR                      -- Пошук по ID
        t.submitter_username ILIKE %s OR                           -- Пошук по Заявнику
        h.admin_name ILIKE %s OR                                   -- Пошук по Обробнику
        CAST(t.time_spent AS TEXT) ILIKE %s OR                     -- Пошук по Часу (сек)
        CAST(t.resolution_rating AS TEXT) ILIKE %s                  -- Пошук по Рейтингу
    ORDER BY t.ticket_id;
    """
    # Шаблон пошуку, що підходить для всіх 5-ти полів
    search_pattern = f"%{search_query}%" 
    
    # Створюємо кортеж параметрів, повторюючи шаблон 5 разів (для 5-ти %s)
    params = (search_pattern,) * 5

    try:
        with conn.cursor() as cur:
            cur.execute(sql, params) 
            column_names = [desc[0] for desc in cur.description]
            tickets = cur.fetchall()
            
            data = []
            for row in tickets:
                data.append(dict(zip(column_names, row)))
            return data

    except Exception as e:
        print(f"❌ Помилка читання даних ticketinfo з пошуком: {e}")
        return []
    finally:
        if conn: conn.close()

# НОВА ФУНКЦІЯ: для перевірки облікових даних webadmin
def check_webadmin_credentials(username, password):
    """
    Перевіряє облікові дані webadmin в таблиці public.webadmin.
    
    УВАГА: ЦЯ ФУНКЦІЯ ПЕРЕВІРЯЄ ПАРОЛЬ ЯК ПРОСТИЙ ТЕКСТ. 
    У РЕАЛЬНОМУ ПРОЄКТІ ВИ ПОВИННІ ВИКОРИСТОВУВАТИ ХЕШУВАННЯ (наприклад, bcrypt)!
    """
    sql = "SELECT webadmin_id, webadmin_name FROM public.webadmin WHERE webadmin_name = %s AND webadmin_password = %s;"
    conn = get_connection()
    if conn is None: return None # Помилка підключення

    try:
        with conn.cursor() as cur:
            # Використовуємо параметризований запит для захисту від SQL-ін'єкцій
            cur.execute(sql, (username, password))
            admin_data = cur.fetchone()
            
            if admin_data:
                # Повертаємо дані адміністратора (ID та ім'я)
                return {'webadmin_id': admin_data[0], 'webadmin_name': admin_data[1]}
            else:
                return None # Облікові дані невірні
    except Exception as e:
        # print(f"❌ Помилка перевірки облікових даних: {e}")
        return None
    finally:
        if conn:
            conn.close()


# --- НАЛАШТУВАННЯ FLASK ---
app = Flask(__name__)
# Встановлюємо Secret Key для Flash-повідомлень (якщо знадобиться)
app.config['SECRET_KEY'] = 'a_very_secret_key_that_is_long_and_random' 

# Декоратор для перевірки авторизації (із попереднього кроку)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- МАРШРУТ 1: ГОЛОВНА СТОРІНКА (helperinfo) ---
@app.route('/')
@login_required 
def home():
    """Відображає таблицю helperinfo, з підтримкою пошуку."""
    
    # 1. Отримуємо пошуковий запит з URL
    search_query = request.args.get('query', '')
    
    if search_query:
        # 2. Якщо запит є, використовуємо функцію пошуку
        helpers = get_helpers_by_search(search_query)
        main_title = f"Співробітники (HelperInfo) - Пошук: '{search_query}'"
    else:
        # 3. Якщо запиту немає, отримуємо всі дані
        helpers = get_all_helpers()
        main_title = "Співробітники (HelperInfo)"
    
    # Використовуємо той самий шаблон index.html, але з даними помічників
    return render_template('index.html', 
                           title="Helper Information", 
                           table_data=helpers,
                           col_headers=["ID", "Ім'я", "Ранг", "Попереджень"],
                           main_content_title=main_title)

# --- МАРШРУТ 2: СТОРІНКА №1 (ticketinfo) ---
@app.route('/tickets')
# @login_required 
def tickets():
    """Відображає таблицю ticketinfo, з підтримкою пошуку."""
    
    # 1. Отримуємо пошуковий запит з URL
    search_query = request.args.get('query', '')
    
    if search_query:
        # 2. Якщо запит є, використовуємо НОВУ функцію пошуку
        tickets_data = get_tickets_by_multi_search(search_query) 
        main_title = f"Тікети (TicketInfo) - Пошук: '{search_query}'"
    else:
        # 3. Якщо запиту немає, отримуємо всі дані
        tickets_data = get_all_tickets()
        main_title = "Тікети (TicketInfo)"
    
    return render_template('index.html', 
                           title="Ticket Information", 
                           table_data=tickets_data,
                           col_headers=["ID", "Заявник", "Обробник", "Час (сек)", "Рейтинг", "Створено", "Закрито"],
                           main_content_title=main_title)

# --- МАРШРУТ 3: СТОРІНКА ВХОДУ (login) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 1. Отримання даних з форми
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 2. Перевірка облікових даних у базі даних
        admin_info = check_webadmin_credentials(username, password) # <--- ВИКОРИСТОВУЄМО НОВУ ФУНКЦІЮ
        
        if admin_info:
            # Успішний вхід: 
            session['logged_in'] = True 
            session['username'] = admin_info['webadmin_name'] # Зберігаємо ім'я користувача
            session['webadmin_id'] = admin_info['webadmin_id'] # Зберігаємо ID

            print(f"✅ Успішний вхід для користувача: {username}")
            return redirect(url_for('home'))
        else:
            # Невдалий вхід
            error = 'Невірне ім\'я користувача або пароль.'
            print(f"❌ Невдалий вхід для користувача: {username}")
            # Повертаємо користувача на сторінку логіну з повідомленням про помилку
            return render_template('login.html', error=error)

    # Метод GET: Просто відображаємо сторінку логіну
    return render_template('login.html', title="Вхід до системи")

# --- МАРШРУТ 4: ОНОВЛЕННЯ ДАНИХ СПІВРОБІТНИКА ---
@app.route('/update_helper', methods=['POST'])
# @login_required 
def update_helper():
    helper_id = request.form.get('helper_id')
    name = request.form.get('admin_name')
    rank = request.form.get('admin_rank')
    warnings = request.form.get('warnings_count')
    
    if update_helper_data(helper_id, name, rank, warnings):
        print(f"✅ Дані співробітника ID {helper_id} успішно оновлено.")
    else:
        print(f"❌ Помилка оновлення даних для ID {helper_id}.")
        
    return redirect(url_for('home'))

# --- МАРШРУТ 5: ВИДАЛЕННЯ СПІВРОБІТНИКА ---
@app.route('/delete_helper', methods=['POST'])
# @login_required 
def delete_helper():
    helper_id = request.form.get('helper_id')
    
    if delete_helper_data(helper_id):
        print(f"✅ Співробітник ID {helper_id} успішно видалено.")
    else:
        # У разі невдачі (наприклад, через FK) можна додати повідомлення про помилку
        print(f"❌ Помилка видалення співробітника ID {helper_id} (можливо, він має відкриті тікети).")
        
    return redirect(url_for('home'))

# Маршрут для виходу (із попереднього кроку)
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('webadmin_id', None)
    return redirect(url_for('login')) 

# --- НОВИЙ МАРШРУТ: для подачі файлів з папки 'script' ---
@app.route('/script/<path:filename>')
def script(filename):
    """Подає статичні файли з папки 'script'."""
    return send_from_directory('script', filename)


if __name__ == '__main__':
    app.run(debug=True)