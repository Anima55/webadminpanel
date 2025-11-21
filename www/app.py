import io 
import csv
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, send_file, flash
import psycopg
import os
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

# DB_NAME - назва бд, DB_USER - Логін DB_PASSWORD - Пароль, DB_HOST - IP хоста DB_PORT - Порт
DB_NAME = os.environ.get('DB_NAME', 'wdb')
DB_USER = os.environ.get('DB_USER', 'webadmin')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'admin')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')

CONN_STRING = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Підключення до бд
def get_connection():
    """Створює та повертає об'єкт підключення."""
    try:
        conn = psycopg.connect(CONN_STRING)
        return conn
    except psycopg.OperationalError as e:
        # print(f"Помилка підключення до бази даних: {e}")
        return None

# Функцій для табліци HelperInfo
# Функція для отримання всіх помічників (для головної сторінки)
def get_all_helpers(query=None, sort_by=None, sort_type='ASC'): # ДОДАНО: query
    """Повертає всіх помічників з таблиці helperinfo, з можливістю сортування та пошуку."""
    
    conn = get_connection()
    if conn is None:
        return []

    # Визначення допустимих полів сортування
    valid_sort_fields = ['helper_id', 'admin_name', 'admin_rank', 'warnings_count']
    
    # Побудова SQL-запиту
    # 1. WHERE Clause (Пошук/Фільтрація)
    where_clause = ""
    params = {}
    
    if query:
        # Додаємо умову пошуку по імені або рангу (case-insensitive LIKE)
        where_clause = " WHERE admin_name ILIKE %(query)s OR admin_rank ILIKE %(query)s OR warnings_count ILIKE %(query)s"
        # %% використовується для передачі % у psycopg
        params['query'] = f"%{query}%"

    # 2. ORDER BY Clause (Сортування)
    order_clause = ""
    if sort_by and sort_by in valid_sort_fields:
        # Перевіряємо, чи ASC чи DESC
        sort_type = 'DESC' if sort_type and sort_type.upper() == 'DESC' else 'ASC'
        
        # Використовуємо ідентифікатор поля напряму, щоб уникнути SQL Injection
        order_clause = f" ORDER BY {psycopg.sql.Identifier(sort_by)} {psycopg.sql.SQL(sort_type)}"
    
    # 3. Формування повного запиту
    sql_template = f"SELECT helper_id, admin_name, admin_rank, warnings_count FROM helperinfo{where_clause}{order_clause}"
    
    results = []
    try:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            # Використовуємо cur.execute() з параметрами для безпеки
            cur.execute(sql_template, params)
            results = cur.fetchall()
    except Exception as e:
        print(f"Помилка при отриманні даних HelperInfo: {e}")
        # Залишаємо print для логування, як у вашому стилі
    finally:
        conn.close()
        
    return results

def get_helpers_by_search(search_query, sort_by=None, sort_type='ASC'): # <--- ДОДАТИ: параметри сортування
    """Повертає помічників, які відповідають search_query у будь-якому текстовому полі, з сортуванням."""
    conn = get_connection()
    if conn is None: return []

    valid_sort_fields = ['helper_id', 'admin_name', 'admin_rank', 'warnings_count']
    order_column = sort_by if sort_by in valid_sort_fields else 'helper_id'
    order_direction = sort_type if sort_type in ('ASC', 'DESC') else 'ASC'

    # !!! ЗМІНА В SQL-ЗАПИТІ: Додаємо ORDER BY
    sql = f"""
    SELECT helper_id, admin_name, admin_rank, warnings_count 
    FROM public.helperinfo 
    WHERE 
        admin_name ILIKE %s OR 
        admin_rank ILIKE %s OR
        CAST(warnings_count AS TEXT) ILIKE %s OR
        CAST(helper_id AS TEXT) ILIKE %s 
    ORDER BY {order_column} {order_direction}; 
    """
    search_pattern = f"%{search_query}%" 
    params = (search_pattern, search_pattern, search_pattern, search_pattern)

    try:
        with conn.cursor() as cur:
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

# ФУНКЦІЯ: Оновлення даних співробітника
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

# ФУНКЦІЯ: Видалення співробітника
def delete_helper_data(helper_id):
    """Видаляє співробітника з таблиці helperinfo за ID, попередньо видаливши всі пов'язані тікети."""
    conn = get_connection()
    if conn is None: return False

    try:
        with conn.cursor() as cur:
            # 1. Видаляємо всі тікети, пов'язані з цим співробітником (handler_helper_id)
            # Примітка: Тікети, де helper був призначений (handler_helper_id), будуть видалені.
            sql_delete_tickets = "DELETE FROM public.ticketinfo WHERE handler_helper_id = %s;"
            cur.execute(sql_delete_tickets, (helper_id,))
            deleted_tickets_count = cur.rowcount
            print(f"✅ Видалено {deleted_tickets_count} пов'язаних тікетів для Helper ID {helper_id}.")
            
            # 2. Видаляємо самого співробітника з helperinfo
            sql_delete_helper = "DELETE FROM public.helperinfo WHERE helper_id = %s;"
            cur.execute(sql_delete_helper, (helper_id,))
        
        conn.commit()
        # Повертаємо True, якщо видалено принаймні один рядок співробітника
        return cur.rowcount > 0 
        
    except Exception as e:
        # Обробляємо будь-яку іншу помилку і відкочуємо транзакцію
        print(f"❌ Помилка видалення співробітника ID {helper_id} або пов'язаних тікетів: {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

# ФУНКЦІЯ: Додавання нового співробітника
def insert_helper_data(name, rank, warnings):
    """Додає нового співробітника в таблицю helperinfo."""
    sql = """
    INSERT INTO public.helperinfo (admin_name, admin_rank, warnings_count)
    VALUES (%s, %s, %s);
    """
    conn = get_connection()
    if conn is None: return False

    try:
        with conn.cursor() as cur:
            cur.execute(sql, (name, rank, warnings))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Помилка додавання нового співробітника: {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

# Функцій для табліци TicketInfo
# Функція для отримання всіх тікетів (для сторінки TicketInfo)
def get_all_tickets(query=None, sort_by=None, sort_type='ASC'):
    """Повертає всі тікети з таблиці ticketinfo, з можливістю пошуку та сортування."""
    ticket_list = []
    
    # Визначення поля для сортування за замовчуванням
    if not sort_by:
        sort_by = 'ticket_id' # Сортуємо за ID за замовчуванням
    
    # Перевірка безпеки сортування: дозволені поля
    allowed_sort_fields = {
        'ticket_id': 't.ticket_id',
        'submitter_username': 't.submitter_username',
        'handler_name': 'h.admin_name',
        'time_spent': 't.time_spent',
        'resolution_rating': 't.resolution_rating'
    }
    
    # Перевіряємо чи вибране поле для сортування дозволено
    sort_column = allowed_sort_fields.get(sort_by, 't.ticket_id')
    sort_direction = 'DESC' if sort_type.upper() == 'DESC' else 'ASC'
    
    # Базовий запит із приєднанням (JOIN) для отримання імені хендлера
    base_query = """
        SELECT 
            t.ticket_id, 
            t.submitter_username, 
            t.handler_helper_id, 
            t.time_spent, 
            t.resolution_rating,
            h.admin_name AS handler_name
        FROM 
            ticketinfo t
        LEFT JOIN 
            helperinfo h ON t.handler_helper_id = h.helper_id
    """
    
    # Логіка для додавання фільтра (WHERE)
    where_clauses = []
    params = {}
    
    if query:
        # Додаємо фільтр для пошуку по username та імені хендлера
        where_clauses.append("(t.submitter_username ILIKE %(query_param)s OR h.admin_name ILIKE %(query_param)s)")
        params['query_param'] = f"%{query}%"

    full_query = base_query
    if where_clauses:
        full_query += " WHERE " + " AND ".join(where_clauses)
        
    # Додаємо сортування
    full_query += f" ORDER BY {sort_column} {sort_direction}"
    
    conn = get_connection()
    if conn is None:
        return ticket_list
        
    try:
        with conn.cursor() as cur:
            cur.execute(full_query, params)
            
            # Отримання імен колонок
            column_names = [desc[0] for desc in cur.description]
            
            for record in cur.fetchall():
                ticket_list.append(dict(zip(column_names, record)))
                
    except Exception as e:
        # print(f"Помилка при отриманні тікетів: {e}")
        pass
    finally:
        if conn:
            conn.close()
            
    return ticket_list

# Функція: Пошук тікетів за іменем заявника
def get_tickets_by_multi_search(search_query, sort_by=None, sort_type='ASC'): # <--- ЗМІНА: Додано параметри сортування
    """Повертає тікети, які відповідають search_query у кількох полях, з сортуванням."""
    conn = get_connection()
    if conn is None: return []

    valid_sort_fields = ['ticket_id', 'submitter_username', 'handler_name', 'time_spent', 'resolution_rating']
    order_column = sort_by if sort_by in valid_sort_fields else 'ticket_id'
    order_direction = sort_type if sort_type in ('ASC', 'DESC') else 'ASC'
    
    # !!! ЗМІНА В SQL-ЗАПИТІ: Додаємо ORDER BY
    sql = f"""
    SELECT 
        t.ticket_id, 
        t.submitter_username, 
        h.admin_name AS handler_name, 
        t.time_spent, 
        t.resolution_rating
    FROM public.ticketinfo AS t
    LEFT JOIN public.helperinfo AS h ON t.handler_helper_id = h.helper_id
    WHERE 
        CAST(t.ticket_id AS TEXT) ILIKE %s OR                      
        t.submitter_username ILIKE %s OR                           
        h.admin_name ILIKE %s OR                                   
        CAST(t.time_spent AS TEXT) ILIKE %s OR                     
        CAST(t.resolution_rating AS TEXT) ILIKE %s                  
    ORDER BY {order_column} {order_direction};
    """
    search_pattern = f"%{search_query}%" 
    params = (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern)

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

    # Шаблон пошуку, що підходить для всіх 5-ти полів
    search_pattern = f"%{search_query}%" 
    
    # Створюємо кортеж параметрів, повторюючи шаблон 5 разів (для 5-ти %s)
    params = (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern)

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

# ФУНКЦІЯ: для перевірки облікових даних webadmin
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

# Функція для отримання рангу WebAdmin
def get_webadmin_rank(username):
    """Повертає ранг (webadmin_rank) користувача webadmin."""
    conn = get_connection()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT webadmin_rank FROM webadmin WHERE webadmin_name = %s", (username,))
            result = cur.fetchone()
            return result[0] if result else None
    except Exception as e:
        print(f"Помилка отримання рангу webadmin: {e}")
        return None
    finally:
        if conn:
            conn.close()

# ==========================================================
# Функцій для табліци WebAdmin
# ==========================================================

# Функція для отримання всіх веб-адмінів
def get_all_webadmins(sort_by=None, sort_type='ASC'): 
    """Повертає всіх веб-адмінів з таблиці webadmin, з можливістю сортування."""
    
    # Виключаємо webadmin_password
    valid_sort_fields = ['webadmin_id', 'webadmin_name', 'webadmin_rank'] 
    order_column = sort_by if sort_by in valid_sort_fields else 'webadmin_id'
    order_direction = sort_type.upper() if sort_type.upper() in ('ASC', 'DESC') else 'ASC'
    
    sql = f"""
    SELECT webadmin_id, webadmin_name, webadmin_rank 
    FROM public.webadmin 
    ORDER BY {order_column} {order_direction};
    """
    conn = get_connection()
    if conn is None: return [] 

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            column_names = [desc[0] for desc in cur.description]
            webadmins = cur.fetchall()
            
            data = []
            for row in webadmins:
                data.append(dict(zip(column_names, row)))
            return data

    except Exception as e:
        print(f"❌ Помилка читання даних webadmin: {e}")
        return []
    finally:
        if conn: conn.close()

# Функція для пошуку веб-адмінів
def get_webadmins_by_search(search_query, sort_by=None, sort_type='ASC'):
    """Повертає веб-адмінів, які відповідають search_query, з сортуванням."""
    conn = get_connection()
    if conn is None: return []

    valid_sort_fields = ['webadmin_id', 'webadmin_name', 'webadmin_rank']
    order_column = sort_by if sort_by in valid_sort_fields else 'webadmin_id'
    order_direction = sort_type.upper() if sort_type.upper() in ('ASC', 'DESC') else 'ASC'

    sql = f"""
    SELECT webadmin_id, webadmin_name, webadmin_rank
    FROM public.webadmin 
    WHERE 
        webadmin_name ILIKE %s OR 
        webadmin_rank ILIKE %s OR
        CAST(webadmin_id AS TEXT) ILIKE %s 
    ORDER BY {order_column} {order_direction}; 
    """
    search_pattern = f"%{search_query}%" 
    params = (search_pattern, search_pattern, search_pattern)

    try:
        with conn.cursor() as cur:
            cur.execute(sql, params) 
            column_names = [desc[0] for desc in cur.description]
            webadmins = cur.fetchall()
            
            data = []
            for row in webadmins:
                data.append(dict(zip(column_names, row)))
            return data

    except Exception as e:
        print(f"❌ Помилка читання даних webadmin з пошуком: {e}")
        return []
    finally:
        if conn: conn.close()

# ФУНКЦІЯ: Оновлення даних веб-адміна (без зміни пароля)
def update_webadmin_data(webadmin_id, name, rank):
    """Оновлює ім'я та ранг веб-адміна в таблиці webadmin."""
    sql = """
    UPDATE public.webadmin
    SET webadmin_name = %s, webadmin_rank = %s
    WHERE webadmin_id = %s;
    """
    conn = get_connection()
    if conn is None: return False

    try:
        with conn.cursor() as cur:
            cur.execute(sql, (name, rank, webadmin_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Помилка оновлення даних веб-адміна ID {webadmin_id}: {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

# ФУНКЦІЯ: Видалення веб-адміна
def delete_webadmin_data(webadmin_id):
    """Видаляє веб-адміна з таблиці webadmin за ID."""
    sql = "DELETE FROM public.webadmin WHERE webadmin_id = %s;"
    conn = get_connection()
    if conn is None: return False

    try:
        with conn.cursor() as cur:
            cur.execute(sql, (webadmin_id,))
        conn.commit()
        return cur.rowcount > 0 
    except Exception as e:
        print(f"❌ Помилка видалення веб-адміна ID {webadmin_id}: {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

# ФУНКЦІЯ: Додавання нового веб-адміна
def insert_webadmin_data(name, rank, password):
    """Додає нового веб-адміна в таблицю webadmin."""
    # УВАГА: У реальному додатку тут слід використовувати хешування пароля!
    sql = """
    INSERT INTO public.webadmin (webadmin_name, webadmin_rank, webadmin_password)
    VALUES (%s, %s, %s);
    """
    conn = get_connection()
    if conn is None: return False

    try:
        with conn.cursor() as cur:
            cur.execute(sql, (name, rank, password))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Помилка додавання нового веб-адміна: {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

# --- НАЛАШТУВАННЯ FLASK ---
app = Flask(__name__)
# Встановлюємо Secret Key для Flash-повідомлень (якщо знадобиться)
app.config['SECRET_KEY'] = 'a_very_secret_key_that_is_long_and_random' 

# Декоратор для перевірки авторизації (із попереднього кроку)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(required_rank):
    """
    Декоратор, який перевіряє, чи користувач увійшов в систему 
    і чи має він необхідний ранг (включно із SuperAdmin).
    """
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 1. Перевіряємо, чи користувач увійшов (це вже робить login_required, але для надійності)
            if 'logged_in' not in session or not session.get('logged_in'):
                # Використовуємо flash для повідомлення, якщо потрібно
                # flash('Для доступу до цієї сторінки необхідний вхід.', 'danger')
                return redirect(url_for('login'))
            
            user_rank = session.get('user_rank', 'Guest')
            
            # 2. Перевіряємо ранг
            # Порівняння рангів (для простоти, припускаємо, що SuperAdmin має повний доступ)
            if user_rank != required_rank and user_rank != 'SuperAdmin':
                # flash(f'Недостатньо прав. Потрібен ранг: {required_rank}', 'warning')
                # Можна перенаправити на головну сторінку або сторінку 403
                return redirect(url_for('home'))
            
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

# --- МАРШРУТ 3: СТОРІНКА ВХОДУ (login) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    title = 'Вхід'
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_connection()
        if conn:
            try:
                with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                    cur.execute("SELECT webadmin_id, webadmin_name, webadmin_rank, webadmin_password FROM webadmin WHERE webadmin_name = %s", (username,))
                    result = cur.fetchone()
                
                # --- ЗМІНА ТУТ: ВИКОРИСТАННЯ check_password_hash ---
                if result and check_password_hash(result['webadmin_password'], password): 
                    # Вхід успішний
                    session['logged_in'] = True
                    session['username'] = result['webadmin_name']
                    session['webadmin_id'] = result['webadmin_id']
                    session['user_rank'] = result['webadmin_rank'] # Додано для адмін-панелі
                    return redirect(url_for('home'))
                else:
                    error = 'Невірне ім\'я користувача або пароль.'
                # ---------------------------------------------------

            except Exception as e:
                # print(f"Помилка входу: {e}")
                error = 'Помилка сервера при спробі входу.'
                
    # Якщо rank не встановлено, встановлюємо 'Guest' для коректного відображення навігації
    user_rank = session.get('user_rank', 'Guest')
    return render_template('login.html', title=title, error=error, user_rank=user_rank)

# --- МАРШРУТ 1: ГОЛОВНА СТОРІНКА (helperinfo) ---
@app.route('/')
@login_required 
def home():
    """Відображає таблицю helperinfo, з підтримкою пошуку та сортування."""
    
    search_query = request.args.get('query', '')
    query = request.args.get('query', '')
    
    # 1. Отримуємо параметри сортування з URL (тепер вони простіші)
    sort_by = request.args.get('sort_by', '')
    sort_type = request.args.get('sort_type', 'asc').upper() # ASC або DESC
        
    # 2. Вибираємо функцію для отримання даних
    if search_query:
        # Передаємо сортування в функцію пошуку
        helpers = get_helpers_by_search(search_query, sort_by, sort_type) 
        main_title = f"Співробітники (HelperInfo) - Пошук: '{search_query}'"
    else:
        # Передаємо сортування в функцію отримання всіх даних
        helpers = get_all_helpers(query, sort_by, sort_type)
        main_title = "Співробітники (HelperInfo)"
    
    item_count = len(helpers)

    user_rank = session.get('rank')
    # Параметри sort_by та sort_type будуть автоматично доступні в шаблоні 
    # завдяки request.args, тому їх окремо передавати не обов'язково.
    return render_template('index.html', 
        title="Helper Information", 
        table_data=helpers,
        col_headers=["ID", "Ім'я", "Ранг", "Попереджень"],
        main_content_title=main_title,
        sort_by=sort_by,
        sort_type=sort_type,
        item_count=item_count,
        user_rank=user_rank
        )

# --- МАРШРУТ 2: СТОРІНКА №1 (ticketinfo) ---
@app.route('/tickets')
# @login_required 
def tickets():
    """Відображає таблицю ticketinfo, з підтримкою пошуку та сортування.""" # <--- ЗМІНА
    
    search_query = request.args.get('query', '')
    user_rank = session.get('rank')

    # 1. Отримуємо параметри сортування з URL 
    sort_by = request.args.get('sort_by', '')
    sort_type = request.args.get('sort_type', 'asc').upper() # ASC або DESC
    
    if search_query:
        # 2. Передаємо сортування в функцію пошуку
        tickets_data = get_tickets_by_multi_search(search_query, sort_by, sort_type) # <--- ЗМІНА
        main_title = f"Тікети (TicketInfo) - Пошук: '{search_query}'"
    else:
        # 3. Передаємо сортування в функцію отримання всіх даних
        tickets_data = get_all_tickets(sort_by, sort_type) # <--- ЗМІНА
        main_title = "Тікети (TicketInfo)"
    
    item_count = len(tickets_data) # <--- Тимчасовий фікс, якщо була помилка з item_count
    
    query = request.args.get('query', '')

    ticket_list = get_all_tickets(query=query, sort_by=sort_by, sort_type=sort_type)
    
    return render_template(
        'tickets.html',
        title='TicketInfo',
        user_rank=session.get('user_rank'),
        ticket_list=ticket_list,
        # Передаємо поточні параметри назад до шаблону для відображення стану фільтра
        active_query=query,
        active_sort_by=sort_by,
        active_sort_type=sort_type
    )

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
        # Тут виводиться повідомлення, якщо видалення заблоковано через FK
        print(f"❌ Помилка видалення співробітника ID {helper_id} (можливо, він має відкриті тікети або ID не знайдено).")
        
    return redirect(url_for('home'))

# --- МАРШРУТ 6: ДОДАВАННЯ СПІВРОБІТНИКА ---
@app.route('/add_helper', methods=['POST'])
# @login_required 
def add_helper():
    name = request.form.get('admin_name')
    rank = request.form.get('admin_rank')
    warnings = request.form.get('warnings_count') or 0 # Приймаємо 0, якщо поле порожнє
    
    if insert_helper_data(name, rank, warnings):
        print(f"✅ Співробітник {name} успішно додано.")
    else:
        print(f"❌ Помилка додавання співробітника {name}.")
        
    return redirect(url_for('home'))

# --- МАРШРУТ 7: СТОРІНКА АДМІНА ---
@app.route('/admin-page', methods=['GET'])
# @login_required # Розкоментуйте, коли реалізуєте login_required
def admin_page():
    # Перевірка на SuperAdmin (якщо не закоментовано login_required, це не є критичним)
    if session.get('rank') != 'SuperAdmin':
        return redirect(url_for('home')) 
    
    # Параметри сортування
    sort_by = request.args.get('sort_by')
    sort_type = request.args.get('sort_type', 'asc')
    
    # Пошук
    search_query = request.args.get('query')
    
    if search_query:
        # Використовуємо функцію пошуку з параметрами сортування
        webadmin_list = get_webadmins_by_search(search_query, sort_by, sort_type)
    else:
        # Отримуємо всі дані з параметрами сортування
        webadmin_list = get_all_webadmins(sort_by, sort_type)
        
    return render_template(
        'admin-page.html', 
        title='Admin Panel - WebAdmins',
        webadmin_list=webadmin_list,
        user_rank=session.get('rank')
    )

# --- НОВИЙ МАРШРУТ: ОНОВЛЕННЯ ВЕБ-АДМІНА ---
@app.route('/update_webadmin', methods=['POST'])
@login_required
@admin_required('SuperAdmin')
def update_webadmin():
    webadmin_id = request.form['webadmin_id']
    username = request.form['webadmin_name']
    rank = request.form['webadmin_rank']
    
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                query = "UPDATE webadmin SET username = %s, webadmin_rank = %s"
                params = [username, rank]
                query += " WHERE webadmin_id = %s"
                params.append(webadmin_id)
                
                cur.execute(query, tuple(params))
            conn.commit()
            flash(f'WebAdmin ID {webadmin_id} успішно оновлено.', 'success')
        except Exception as e:
            # print(f"Помилка редагування WebAdmin: {e}")
            flash('Помилка редагування WebAdmin.', 'danger')
    
    return redirect(url_for('admin_page'))

# --- НОВИЙ МАРШРУТ: ВИДАЛЕННЯ ВЕБ-АДМІНА ---
@app.route('/delete_webadmin', methods=['POST'])
# @login_required
def delete_webadmin():
    # Перевірка на SuperAdmin
    if session.get('rank') != 'SuperAdmin':
        return redirect(url_for('admin_page'))
        
    webadmin_id = request.form.get('webadmin_id')
    
    if delete_webadmin_data(webadmin_id):
        print(f"✅ Веб-адмін ID {webadmin_id} успішно видалено.")
    else:
        print(f"❌ Помилка видалення веб-адміна ID {webadmin_id}.")
        
    return redirect(url_for('admin_page'))

# --- НОВИЙ МАРШРУТ: ДОДАВАННЯ ВЕБ-АДМІНА ---
@app.route('/add_webadmin', methods=['POST'])
@login_required
@admin_required('SuperAdmin')
def add_webadmin():
    username = request.form['webadmin_name']
    rank = request.form['webadmin_rank']
    password = request.form['webadmin_password']
    
    # --- ЗМІНА ТУТ: ХЕШУВАННЯ ПАРОЛЯ ---
    hashed_password = generate_password_hash(password)
    # ------------------------------------
    
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # ВСТАВЛЯЄМО ХЕШОВАНИЙ ПАРОЛЬ
                cur.execute("INSERT INTO webadmin (username, webadmin_rank, webadmin_password) VALUES (%s, %s, %s)", 
                            (username, rank, hashed_password))
            conn.commit()
            flash(f'WebAdmin "{username}" успішно додано.', 'success')
        except Exception as e:
            # print(f"Помилка додавання WebAdmin: {e}")
            flash('Помилка додавання WebAdmin.', 'danger')
    
    return redirect(url_for('admin_page'))

# --- НОВИЙ МАРШРУТ: ЕКСПОРТ HELPERINFO В EXCEL ---
@app.route('/export-helperinfo')
@login_required
def export_helperinfo():
    query = request.args.get('query', '').strip()
    sort_by = request.args.get('sort_by')
    sort_type = request.args.get('sort_type', 'ASC')
    
    # ВИПРАВЛЕННЯ: Використовуємо ту ж логіку, що і в функції home(),
    # щоб забезпечити, що якщо 'query' є, ми використовуємо функцію пошуку.
    if query:
        # 1. Якщо є пошуковий запит, використовуємо багатопольовий пошук (як на сторінці)
        helper_list = get_helpers_by_search(query, sort_by, sort_type)
    else:
        # 2. Якщо запиту немає, отримуємо всі дані (або використовуємо get_all_helpers без запиту)
        # Змінено: використовуємо get_all_helpers, але з поточними параметрами сортування
        helper_list = get_all_helpers(query=None, sort_by=sort_by, sort_type=sort_type)
        
    header = ['ID', 'Ім\'я Адміна', 'Ранг', 'Попередження'] 
    
    output = io.StringIO()
    # Використовуємо крапку з комою (;) та BOM для сумісності з українським Excel
    writer = csv.writer(output, delimiter=';') 
    
    writer.writerow(header)
    
    for helper in helper_list:
        writer.writerow([
            helper['helper_id'],
            helper['admin_name'],
            helper['admin_rank'],
            helper['warnings_count']
        ])

    output.seek(0)
    # Додаємо BOM для коректного відображення українських символів в Excel
    csv_bytes = (u'\ufeff' + output.getvalue()).encode('utf-8')
    buffer = io.BytesIO(csv_bytes)
    
    return send_file(
        buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='HelperInfo_Export.xlsx' 
    )
    
# --- НОВИЙ МАРШРУТ: ЕКСПОРТ TICKETINFO В EXCEL ---
@app.route('/export-ticketinfo')
@login_required
def export_ticketinfo():
    query = request.args.get('query', '').strip()
    sort_by = request.args.get('sort_by')
    sort_type = request.args.get('sort_type', 'ASC')
    
    # Виклик функції з фільтрацією/сортуванням
    # ПЕРЕВІРТЕ, ЩО get_all_tickets ПРИЙМАЄ ЦІ ПАРАМЕТРИ
    # Припускаю, що функція get_all_tickets існує
    ticket_list = get_all_tickets(query=query, sort_by=sort_by, sort_type=sort_type)

    # Згідно зі структурою БД (wdb.sql) та tickets.html
    header = ['ID_Тікета', 'Користувач', 'Хендлер_ID', 'Хендлер_Ім\'я', 'Витрачений_час_(хв)', 'Оцінка_вирішення'] 
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';') 
    
    writer.writerow(header)
    
    for ticket in ticket_list:
        writer.writerow([
            ticket['ticket_id'],
            ticket['submitter_username'],
            ticket['handler_helper_id'],
            # 'handler_name' є у tickets.html, але може бути відсутній у ticketinfo таблиці, 
            # тому використовуємо .get() або припускаємо, що він приєднується через JOIN
            ticket.get('handler_name', 'Невідомий'), 
            ticket['time_spent'],
            ticket['resolution_rating']
        ])

    output.seek(0)
    csv_bytes = (u'\ufeff' + output.getvalue()).encode('utf-8')
    buffer = io.BytesIO(csv_bytes)
    
    return send_file(
        buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='TicketInfo_Export.xlsx'
    )

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