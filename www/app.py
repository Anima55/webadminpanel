import io 
import csv
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, send_file, flash, jsonify
import psycopg
import os
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import subprocess
from datetime import datetime

# DB_NAME - назва бд, DB_USER - Логін DB_PASSWORD - Пароль, DB_HOST - IP хоста DB_PORT - Порт
DB_NAME = os.environ.get('DB_NAME', 'wdb')
DB_USER = os.environ.get('DB_USER', 'webadmin')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'admin')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')

PG_DUMP_PATH = os.environ.get('PG_DUMP_PATH', 'I:/code/postgresql/bin/pg_dump.exe')

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

# Декоратор для перевірки авторизації
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

def curator_required(f):
    """Декоратор для перевірки прав Curator (редагування тільки співробітників)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session.get('logged_in'):
            return redirect(url_for('login'))
        
        user_rank = session.get('user_rank', 'Guest')
        
        # Curator може тільки редагувати, не може додавати/видаляти
        if user_rank not in ['Curator', 'Manager', 'SuperAdmin']:
            flash('Недостатньо прав для виконання цієї дії.', 'warning')
            return redirect(url_for('home'))
            
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    """Декоратор для перевірки прав Manager (без права встановлювати SuperAdmin)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session.get('logged_in'):
            return redirect(url_for('login'))
        
        user_rank = session.get('user_rank', 'Guest')
        
        if user_rank not in ['Manager', 'SuperAdmin']:
            flash('Недостатньо прав для виконання цієї дії.', 'warning')
            return redirect(url_for('home'))
            
        return f(*args, **kwargs)
    return decorated_function

def can_edit_rank(user_rank, target_rank):
    """Перевіряє, чи може користувач редагувати співробітника з вказаним рангом"""
    rank_hierarchy = {
        'Moder': 1,
        'Admin': 2,
        'Curator': 3,
        'Manager': 4,
        'SuperAdmin': 5
    }
    
    user_level = rank_hierarchy.get(user_rank, 0)
    target_level = rank_hierarchy.get(target_rank, 0)
    
    # Користувач може редагувати тільки співробітників з рівнем <= його рівню
    return target_level <= user_level

# ==========================================================
# Функцій для табліци HelperInfo
# ==========================================================

# --- ФУНКЦІЯ H1: Для отримання всіх помічників (для головної сторінки) ---
def get_all_helpers(query=None, sort_by=None, sort_type='ASC', rank_filter=None):
    """Повертає всіх помічників з таблиці helperinfo, з можливістю сортування та пошуку."""
    
    conn = get_connection()
    if conn is None:
        return []

    # Базовий SQL запит
    sql = "SELECT helper_id, admin_name, admin_rank, warnings_count FROM helperinfo"
    params = []
    conditions = []
    
    # Додаємо пошук якщо є query
    if query:
        conditions.append("(admin_name ILIKE %s OR admin_rank ILIKE %s OR CAST(warnings_count AS TEXT) ILIKE %s OR CAST(helper_id AS TEXT) ILIKE %s)")
        search_pattern = f"%{query}%"
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
    
    # Додаємо фільтр по рангу якщо вказано
    if rank_filter:
        conditions.append("admin_rank = %s")
        params.append(rank_filter)
    
    # Додаємо WHERE якщо є умови
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    
    # Додаємо сортування якщо вказано
    valid_sort_fields = ['helper_id', 'admin_name', 'admin_rank', 'warnings_count']
    if sort_by and sort_by in valid_sort_fields:
        sort_direction = 'DESC' if sort_type.upper() == 'DESC' else 'ASC'
        sql += f" ORDER BY {sort_by} {sort_direction}"
    
    results = []
    try:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            results = cur.fetchall()
    except Exception as e:
        print(f"Помилка при отриманні даних HelperInfo: {e}")
    finally:
        conn.close()
        
    return results

# --- ФУНКЦІЯ H2: Для фільтра Helperinfo ---
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

# --- ФУНКЦІЯ H3: Оновлення даних помічників ---
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

# --- ФУНКЦІЯ H4: Видалення помічників ---
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

# --- ФУНКЦІЯ H5: Додавання нового помічників ---
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

# --- ФУНКЦІЯ H6: Отримання Одиничного Запису (Helper) ---
def get_helper_by_id(helper_id):
    """Отримує одного помічника за helper_id."""
    conn = get_connection()
    if not conn:
        return None
    
    helper = None
    try:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT helper_id, admin_name, admin_rank, warnings_count FROM helperinfo WHERE helper_id = %s;",
                (helper_id,)
            )
            helper = cur.fetchone()
    except psycopg.Error as e:
        print(f"Помилка отримання помічника: {e}")
    finally:
        conn.close()
    
    return helper


# ==========================================================
# Функцій для табліци TicketInfo
# ==========================================================

# --- ФУНКЦІЯ T1: Для отримання всіх тікетів
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

# --- ФУНКЦІЯ T2: Пошук тікетів за іменем заявника
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



# ==========================================================
# Функцій для табліци WebAdmin
# ==========================================================

# --- ФУНКЦІЯ W1: Для отримання всіх веб-адмінів
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

# --- ФУНКЦІЯ W2: Для пошуку веб-адмінів ---
def get_webadmins_by_search(search_query, sort_by=None, sort_type='ASC', rank_filter=None):
    """Повертає веб-адмінів, які відповідають search_query, з сортуванням та фільтрацією за рангом."""
    conn = get_connection()
    if conn is None: return []

    valid_sort_fields = ['webadmin_id', 'webadmin_name', 'webadmin_rank']
    order_column = sort_by if sort_by in valid_sort_fields else 'webadmin_id'
    order_direction = sort_type.upper() if sort_type.upper() in ('ASC', 'DESC') else 'ASC'

    # Базовий SQL запит
    sql = f"""
    SELECT webadmin_id, webadmin_name, webadmin_rank
    FROM public.webadmin 
    WHERE 
        (webadmin_name ILIKE %s OR 
        webadmin_rank ILIKE %s OR
        CAST(webadmin_id AS TEXT) ILIKE %s)
    """
    
    search_pattern = f"%{search_query}%" 
    params = [search_pattern, search_pattern, search_pattern]
    
    # Додаємо фільтр по рангу якщо вказано
    if rank_filter:
        sql += " AND webadmin_rank = %s"
        params.append(rank_filter)
    
    # Додаємо сортування
    sql += f" ORDER BY {order_column} {order_direction}" 

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

# --- ФУНКЦІЯ W3: Оновлення даних веб-адміна (без зміни пароля)
def update_webadmin_data(webadmin_id, name, rank):
    """Оновлює ім'я та ранг веб-адміна в таблиці webadmin."""
    print(f"🔄 Спроба оновити webadmin: ID={webadmin_id}, Name={name}, Rank={rank}")
    
    sql = """
    UPDATE public.webadmin
    SET webadmin_name = %s, webadmin_rank = %s
    WHERE webadmin_id = %s;
    """
    conn = get_connection()
    if conn is None: 
        print("❌ Помилка: Не вдалося підключитися до бази даних")
        return False

    try:
        with conn.cursor() as cur:
            cur.execute(sql, (name, rank, webadmin_id))
            updated_rows = cur.rowcount
            print(f"✅ Оновлено рядків: {updated_rows}")
        
        conn.commit()
        print("✅ Транзакція успішно зафіксована")
        return True
        
    except Exception as e:
        print(f"❌ Помилка оновлення даних веб-адміна ID {webadmin_id}: {e}")
        conn.rollback()
        return False
    finally:
        if conn: 
            conn.close()
            print("🔌 З'єднання закрито")

# --- ФУНКЦІЯ W4: Видалення веб-адміна
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

# --- ФУНКЦІЯ W5: Додавання нового веб-адміна
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

# --- ФУНКЦІЯ W6: ЛОГУВАННЯ ДІЙ З ДАНИМИ ---
def log_action(user_id, username, action, table_name, object_id=None):
    """
    Логує дії користувача у файл у форматі, схожому на CLF.
    Формат: [Час] - [Користувач ID/Ім'я] - [Дія] - [Таблиця] - [ID Об'єкта]
    """
    # [22/Nov/2025:16:47:54 +0200]
    timestamp = datetime.now().strftime('[%d/%b/%Y:%H:%M:%S +0200]')
    
    # Використовуємо '?' як аналог відсутнього IP у CLF, де 'user_id' це 'remote_logname'
    log_entry = f"? {user_id} {username} {timestamp} \"{action} {table_name} ID:{object_id}\"\n"
    
    try:
        # Відкриваємо файл логування в режимі додавання (append)
        with open('app.log', 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Помилка логування: {e}")

# --- ФУНКЦІЯ W7: РЕЗЕРВНОГО КОПІЮВАННЯ БАЗИ ДАНИХ ---
def backup_database():
    """
    Створює резервну копію бази даних PostgreSQL за допомогою pg_dump.
    """
    # Шлях, де будуть зберігатися бекапи (створюємо підпапку 'backups')
    backup_dir = 'backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    # Формат імені файлу: wdb_backup_20251122_183000.sql
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"{DB_NAME}_backup_{timestamp}.sql")

    if not os.path.exists(PG_DUMP_PATH):
        error_msg = f"Файл pg_dump не знайдено за шляхом: {PG_DUMP_PATH}. Перевірте константу PG_DUMP_PATH."
        log_action(session.get('webadmin_id'), session.get('username'), 
                   'BACKUP_FAILED', 'database', error_msg)
        return False, error_msg
    
    # Будуємо команду pg_dump
    # Ми використовуємо змінні середовища для передачі облікових даних pg_dump
    command = [
        PG_DUMP_PATH,
        '-h', DB_HOST,
        '-p', DB_PORT,
        '-U', DB_USER,
        '-d', DB_NAME,
        '-f', backup_file,
        '-F', 'p' # Вивід у plain text SQL-файл
    ]
    
    # Визначаємо змінні середовища для процесу (включаючи пароль)
    env_vars = os.environ.copy()
    env_vars['PGPASSWORD'] = DB_PASSWORD # Пароль передається через PGPASSWORD
    
    try:
        # Запускаємо команду
        process = subprocess.run(command, env=env_vars, check=True, capture_output=True, text=True)
        
        # Перевірка результату
        if process.returncode == 0:
            log_action(session.get('webadmin_id'), session.get('username'), 
                       'BACKUP', 'database', backup_file)
            return True, f"Успішно створено бекап: {backup_file}"
        else:
            log_action(session.get('webadmin_id'), session.get('username'), 
                       'BACKUP_FAILED', 'database', f"Помилка: {process.stderr}")
            return False, f"Помилка pg_dump: {process.stderr}"

    except FileNotFoundError:
        log_action(session.get('webadmin_id'), session.get('username'), 
                   'BACKUP_FAILED', 'database', 'Утиліта pg_dump не знайдена. Переконайтеся, що PostgreSQL bin dir додано до PATH.')
        return False, "Помилка: Утиліта pg_dump не знайдена (перевірте PATH)."
    except subprocess.CalledProcessError as e:
        log_action(session.get('webadmin_id'), session.get('username'), 
                   'BACKUP_FAILED', 'database', f"Помилка: {e.stderr}")
        return False, f"Помилка виконання команди: {e.stderr}"
    except Exception as e:
        log_action(session.get('webadmin_id'), session.get('username'), 
                   'BACKUP_FAILED', 'database', f"Невідома помилка: {e}")
        return False, f"Невідома помилка: {e}"
    except FileNotFoundError:
        log_action(session.get('webadmin_id'), session.get('username'), 
                   'BACKUP_FAILED', 'database', 'Перевірте, чи коректно вказано шлях до pg_dump.')
        return False, "Помилка: Перевірте, чи коректно вказано шлях до pg_dump."

# --- ФУНКЦІЯ W8: Для отримання веб-адмінів з фільтрацією за рангом ---
def get_webadmins_by_rank(rank_filter=None, sort_by=None, sort_type='ASC'):
    """Повертає веб-адмінів з фільтрацією за рангом, з можливістю сортування."""
    
    valid_sort_fields = ['webadmin_id', 'webadmin_name', 'webadmin_rank']
    order_column = sort_by if sort_by in valid_sort_fields else 'webadmin_id'
    order_direction = sort_type.upper() if sort_type.upper() in ('ASC', 'DESC') else 'ASC'
    
    # Базовий SQL запит
    sql = f"""
    SELECT webadmin_id, webadmin_name, webadmin_rank 
    FROM public.webadmin 
    """
    
    params = []
    
    # Додаємо фільтр по рангу якщо вказано
    if rank_filter:
        sql += " WHERE webadmin_rank = %s"
        params.append(rank_filter)
    
    # Додаємо сортування
    sql += f" ORDER BY {order_column} {order_direction}"
    
    conn = get_connection()
    if conn is None: 
        return []

    try:
        with conn.cursor() as cur:
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
                
            column_names = [desc[0] for desc in cur.description]
            webadmins = cur.fetchall()
            
            data = []
            for row in webadmins:
                data.append(dict(zip(column_names, row)))
            return data

    except Exception as e:
        print(f"❌ Помилка читання даних webadmin з фільтром за рангом: {e}")
        return []
    finally:
        if conn: 
            conn.close()

# --- ФУНКЦІЯ W9: Для перевірки облікових даних webadmin
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

# --- ФУНКЦІЯ W10: Для отримання рангу WebAdmin
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

# --- НАЛАШТУВАННЯ FLASK ---
app = Flask(__name__)
# Встановлюємо Secret Key для Flash-повідомлень (якщо знадобиться)
app.config['SECRET_KEY'] = 'a_very_secret_key_that_is_long_and_random' 

# ==========================================================
# --- МАРШРУТИ: Сторінки login ---
# ==========================================================

# --- МАРШРУТ 1: СТОРІНКА ВХОДУ (login) ---
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

# --- Маршрут 2: Для виходу ---
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('webadmin_id', None)
    return redirect(url_for('login')) 

# ==========================================================
# --- МАРШРУТИ: Сторінки ticketinfo ---
# ==========================================================

# --- МАРШРУТ 3: СТОРІНКА (ticketinfo) ---
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

# --- МАРШРУТ 4: ЕКСПОРТ TICKETINFO В EXCEL ---
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

# ==========================================================
# --- МАРШРУТИ: Сторінки helperinfo ---
# ==========================================================

# --- МАРШРУТ 5: ГОЛОВНА СТОРІНКА (helperinfo) ---
@app.route('/')
@login_required 
def home():
    """Відображає таблицю helperinfo, з можливістю пошуку та сортування."""
    
    search_query = request.args.get('query', '')
    
    # Отримуємо параметри сортування з URL
    sort_by = request.args.get('sort_by', '')
    sort_type = request.args.get('sort_type', 'asc')
    rank_filter = request.args.get('rank_filter', '')
    
    # Використовуємо одну функцію для отримання даних
    helpers = get_all_helpers(query=search_query, sort_by=sort_by, sort_type=sort_type, rank_filter=rank_filter)
    
    # Формуємо заголовок з урахуванням фільтрів
    if search_query and rank_filter:
        main_title = f"Співробітники (HelperInfo) - Пошук: '{search_query}', Ранг: {rank_filter}"
    elif search_query:
        main_title = f"Співробітники (HelperInfo) - Пошук: '{search_query}'"
    elif rank_filter:
        main_title = f"Співробітники (HelperInfo) - Ранг: {rank_filter}"
    else:
        main_title = "Співробітники (HelperInfo)"
    
    item_count = len(helpers)

    return render_template('index.html', 
        title="Helper Information", 
        table_data=helpers,
        col_headers=["ID", "Ім'я", "Ранг", "Попереджень"],
        main_content_title=main_title,
        sort_by=sort_by,
        sort_type=sort_type,
        rank_filter=rank_filter,
        item_count=item_count,
        user_rank=session.get('user_rank')
    )

# --- МАРШРУТ 6: ОНОВЛЕННЯ ДАНИХ СПІВРОБІТНИКА ---
@app.route('/update_helper', methods=['POST'])
@login_required
@curator_required
def update_helper():
    conn = get_connection()
    if not conn:
        flash('Помилка підключення до бази даних.', 'error')
        return redirect(url_for('home'))

    helper_id = request.form.get('helper_id')
    admin_name = request.form.get('admin_name')
    admin_rank = request.form.get('admin_rank')
    warnings_count = request.form.get('warnings_count')
    
    # Отримуємо поточні дані співробітника
    current_helper = get_helper_by_id(helper_id)
    if not current_helper:
        flash('Співробітника не знайдено.', 'error')
        return redirect(url_for('home'))
    
    user_rank = session.get('user_rank')
    
    # Перевіряємо, чи може користувач редагувати цього співробітника
    if not can_edit_rank(user_rank, current_helper['admin_rank']):
        flash('Недостатньо прав для редагування співробітника з вищим рангом.', 'error')
        return redirect(url_for('home'))
    
    # Перевіряємо, чи не намагається користувач встановити ранг вище за свій
    if not can_edit_rank(user_rank, admin_rank):
        flash('Недостатньо прав для встановлення цього рангу.', 'error')
        return redirect(url_for('home'))
    
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE helperinfo SET admin_name = %s, admin_rank = %s, warnings_count = %s WHERE helper_id = %s;",
                (admin_name, admin_rank, warnings_count, helper_id)
            )
            conn.commit()
            flash('Зміни успішно збережено!', 'success')
            
            log_action(session.get('webadmin_id'), session.get('username'), 
                       'UPDATE', 'helperinfo', helper_id)
            
    except psycopg.Error as e:
        conn.rollback()
        flash(f'Помилка оновлення даних: {e}', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('home'))

# --- МАРШРУТ 7: ВИДАЛЕННЯ СПІВРОБІТНИКА ---
@app.route('/delete_helper', methods=['POST'])
@login_required
@manager_required  # Змінено з admin_required
def delete_helper():
    conn = get_connection()
    if not conn:
        flash('Помилка підключення до бази даних.', 'error')
        return redirect(url_for('home'))
        
    helper_id = request.form.get('helper_id')
    
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM helperinfo WHERE helper_id = %s;", (helper_id,))
            success = cur.rowcount > 0
            conn.commit()
            
            if success:
                flash('Співробітника успішно видалено!', 'success')
                log_action(session.get('webadmin_id'), session.get('username'), 
                           'DELETE', 'helperinfo', helper_id)
            else:
                flash('Співробітника не знайдено.', 'error')
            
    except psycopg.Error as e:
        conn.rollback()
        flash(f'Помилка видалення співробітника: {e}', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('home'))

# --- МАРШРУТ 8: ДОДАВАННЯ СПІВРОБІТНИКА ---
@app.route('/add-helper', methods=['POST'])
@login_required
@manager_required  # Змінено з admin_required
def add_helper():
    conn = get_connection()
    if not conn:
        flash('Помилка підключення до бази даних.', 'error')
        return redirect(url_for('home'))

    admin_name = request.form.get('admin_name')
    admin_rank = request.form.get('admin_rank')
    warnings_count = request.form.get('warnings_count')
    
    # Для Manager - заборонити встановлення SuperAdmin
    user_rank = session.get('user_rank')
    if user_rank == 'Manager' and admin_rank == 'SuperAdmin':
        flash('Недостатньо прав для створення співробітника з рангом SuperAdmin.', 'error')
        return redirect(url_for('home'))
    
    new_helper_id = None
    
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO helperinfo (admin_name, admin_rank, warnings_count) VALUES (%s, %s, %s) RETURNING helper_id;",
                (admin_name, admin_rank, warnings_count)
            )
            new_helper_id = cur.fetchone()[0]
            conn.commit()
            flash('Співробітника успішно додано!', 'success')
            
            log_action(session.get('webadmin_id'), session.get('username'), 
                       'CREATE', 'helperinfo', new_helper_id)
            
    except psycopg.Error as e:
        conn.rollback()
        flash(f'Помилка додавання співробітника: {e}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('home'))

# --- МАРШРУТ 9: ЕКСПОРТ HELPERINFO В EXCEL ---
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

# ==========================================================
# --- МАРШРУТИ: Сторінки адміна ---
# ==========================================================
# --- МАРШРУТ 10: СТОРІНКА АДМІНА ---
@app.route('/admin-page', methods=['GET'])
@login_required
@admin_required(['SuperAdmin'])
def admin_page():
    
    # Параметри сортування
    sort_by = request.args.get('sort_by', '')
    sort_type = request.args.get('sort_type', 'asc')
    
    # Пошук
    search_query = request.args.get('query', '')
    
    # Фільтр за рангом
    rank_filter = request.args.get('rank_filter', '')
    
    if search_query:
        # Використовуємо функцію пошуку з параметрами сортування
        webadmin_list = get_webadmins_by_search(search_query, sort_by, sort_type)
    elif rank_filter:
        # Використовуємо функцію фільтрації за рангом
        webadmin_list = get_webadmins_by_rank(rank_filter, sort_by, sort_type)
    else:
        # Отримуємо всі дані з параметрами сортування
        webadmin_list = get_all_webadmins(sort_by, sort_type)
    
    # Формуємо заголовок з урахуванням фільтрів
    if search_query and rank_filter:
        main_title = f"Веб-Адміністратори - Пошук: '{search_query}', Ранг: {rank_filter}"
    elif search_query:
        main_title = f"Веб-Адміністратори - Пошук: '{search_query}'"
    elif rank_filter:
        main_title = f"Веб-Адміністратори - Ранг: {rank_filter}"
    else:
        main_title = "Веб-Адміністратори"
        
    return render_template(
        'admin-page.html', 
        title='Admin Panel - WebAdmins',
        webadmin_list=webadmin_list,
        main_content_title=main_title,
        sort_by=sort_by,
        sort_type=sort_type,
        rank_filter=rank_filter,
        user_rank=session.get('user_rank')
    )

# --- МАРШРУТ 11: ОНОВЛЕННЯ ВЕБ-АДМІНА ---
@app.route('/update_webadmin', methods=['POST'])
@login_required
@admin_required('SuperAdmin')
def update_webadmin():
    print("🔵 === ПОЧАТОК ОНОВЛЕННЯ WEBADMIN ===")
    
    conn = get_connection()
    if not conn:
        print("❌ Помилка підключення до бази даних")
        flash('Помилка підключення до бази даних.', 'error')
        return redirect(url_for('admin_page'))
        
    # Отримуємо дані з форми
    webadmin_id = request.form.get('webadmin_id')
    username = request.form.get('username')  # Зверніть увагу на ім'я поля!
    webadmin_rank = request.form.get('webadmin_rank')
    password = request.form.get('password')
    
    # Логуємо отримані дані
    print(f"📥 Отримані дані форми:")
    print(f"   ID: {webadmin_id}")
    print(f"   Ім'я: {username}")
    print(f"   Ранг: {webadmin_rank}")
    print(f"   Пароль: {'***' if password else 'Не вказано'}")
    print(f"   Всі поля форми: {dict(request.form)}")
    
    try:
        with conn.cursor() as cur:
            if password and password.strip():  # Якщо пароль вказано і не порожній
                new_hashed_password = generate_password_hash(password)
                print(f"🔑 Оновлення з паролем")
                cur.execute(
                    "UPDATE webadmin SET webadmin_name = %s, webadmin_password = %s, webadmin_rank = %s WHERE webadmin_id = %s;",
                    (username, new_hashed_password, webadmin_rank, webadmin_id)
                )
            else:
                print(f"🔑 Оновлення без зміни пароля")
                cur.execute(
                    "UPDATE webadmin SET webadmin_name = %s, webadmin_rank = %s WHERE webadmin_id = %s;",
                    (username, webadmin_rank, webadmin_id)
                )
            
            # Перевіряємо скільки рядків оновлено
            updated_rows = cur.rowcount
            print(f"✅ Оновлено рядків: {updated_rows}")
            
            conn.commit()
            
            if updated_rows > 0:
                flash(f"Дані WebAdmin '{username}' успішно оновлено!", 'success')
                print(f"✅ Успішне оновлення webadmin ID {webadmin_id}")
                
                # Логування дії
                log_action(session.get('webadmin_id'), session.get('username'), 
                           'UPDATE', 'webadmin', webadmin_id)
            else:
                flash('WebAdmin не знайдено або дані не змінилися.', 'warning')
                print(f"⚠️  Жодного рядка не оновлено (можливо, ID не знайдено)")
            
    except psycopg.Error as e:
        conn.rollback()
        error_msg = f'Помилка оновлення даних WebAdmin: {e}'
        flash(error_msg, 'error')
        print(f"❌ Помилка бази даних: {e}")
    except Exception as e:
        conn.rollback()
        error_msg = f'Невідома помилка: {e}'
        flash(error_msg, 'error')
        print(f"❌ Невідома помилка: {e}")
    finally:
        conn.close()
        print("🔵 === ЗАВЕРШЕННЯ ОНОВЛЕННЯ WEBADMIN ===\n")
        
    return redirect(url_for('admin_page'))

# --- МАРШРУТ 13: ВИДАЛЕННЯ ВЕБ-АДМІНА ---
# --- МАРШРУТ 13: ВИДАЛЕННЯ ВЕБ-АДМІНА ---
@app.route('/delete-webadmin', methods=['POST'])
@login_required
@admin_required(['SuperAdmin'])
def delete_webadmin():
    print("🔵 === ПОЧАТОК ВИДАЛЕННЯ WEBADMIN ===")
    
    conn = get_connection()
    if not conn:
        flash('Помилка підключення до бази даних.', 'error')
        conn.close()  # Додайте це
        return redirect(url_for('admin_page'))  # Додайте return
        
    webadmin_id = request.form.get('webadmin_id')
    print(f"📥 Отримано ID для видалення: {webadmin_id}")
    
    if not webadmin_id:
        flash('ID веб-адміністратора не вказано.', 'error')
        print("❌ Помилка: webadmin_id відсутній у формі")
        conn.close()
        return redirect(url_for('admin_page'))  # Додайте return
    
    # Запобігання видаленню власного облікового запису
    if str(webadmin_id) == str(session.get('webadmin_id')):
        flash('Ви не можете видалити власний обліковий запис!', 'error')
        conn.close()
        return redirect(url_for('admin_page'))  # Додайте return
    
    try:
        with conn.cursor() as cur:
            # Спочатку отримаємо ім'я адміністратора для логування
            cur.execute("SELECT webadmin_name FROM webadmin WHERE webadmin_id = %s;", (webadmin_id,))
            result = cur.fetchone()
            
            if not result:
                flash('WebAdmin не знайдено.', 'error')
                conn.close()
                return redirect(url_for('admin_page'))  # Додайте return
            
            admin_name = result[0]
            
            # Видаляємо адміністратора
            cur.execute("DELETE FROM webadmin WHERE webadmin_id = %s;", (webadmin_id,))
            deleted_rows = cur.rowcount
            
            conn.commit()
            
            if deleted_rows > 0:
                flash(f'WebAdmin "{admin_name}" успішно видалено!', 'success')
                print(f"✅ Успішне видалення webadmin ID {webadmin_id}")
                
                # Логування дії
                log_action(session.get('webadmin_id'), session.get('username'), 
                           'DELETE', 'webadmin', webadmin_id)
            else:
                flash('WebAdmin не знайдено.', 'error')
                print(f"⚠️  Жодного рядка не видалено")
            
    except psycopg.Error as e:
        conn.rollback()
        error_msg = f'Помилка видалення WebAdmin: {e}'
        flash(error_msg, 'error')
        print(f"❌ Помилка бази даних при видаленні: {e}")
    except Exception as e:
        conn.rollback()
        error_msg = f'Невідома помилка: {e}'
        flash(error_msg, 'error')
        print(f"❌ Невідома помилка при видаленні: {e}")
    finally:
        conn.close()
        print("🔵 === ЗАВЕРШЕННЯ ВИДАЛЕННЯ WEBADMIN ===\n")
        
    return redirect(url_for('admin_page'))  # Цей return завжди має бути в кінці


# --- МАРШРУТ 14: ДОДАВАННЯ ВЕБ-АДМІНА ---
@app.route('/add-webadmin', methods=['POST'])
@login_required
@admin_required(['SuperAdmin'])
def add_webadmin():
    conn = get_connection()
    if not conn:
        flash('Помилка підключення до бази даних.', 'error')
        return redirect(url_for('admin_page'))
    
    username = request.form.get('webadmin_name')
    password = request.form.get('webadmin_password')
    webadmin_rank = request.form.get('webadmin_rank')
    
    if not username or not password or not webadmin_rank:
        flash('Усі поля обов\'язкові для заповнення.', 'error')
        return redirect(url_for('admin_page'))
    
    hashed_password = generate_password_hash(password)

    try:
        with conn.cursor() as cur:
            # ИСПРАВЛЕНИЕ: Используем INSERT вместо UPDATE
            cur.execute(
                "INSERT INTO webadmin (webadmin_name, webadmin_password, webadmin_rank) VALUES (%s, %s, %s) RETURNING webadmin_id;",
                (username, hashed_password, webadmin_rank)
            )
            new_webadmin_id = cur.fetchone()[0]
            conn.commit()
            flash(f"WebAdmin '{username}' успішно додано!", 'success')
            
            # --- ВИКЛИК ЛОГУВАННЯ: CREATE ---
            log_action(session.get('webadmin_id'), session.get('username'), 
                       'CREATE', 'webadmin', new_webadmin_id)
            
    except psycopg.Error as e:
        conn.rollback()
        flash(f'Помилка додавання WebAdmin: {e}', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('admin_page'))

# --- МАРШРУТ 15: ЗАПУСК РЕЗЕРВНОГО КОПІЮВАННЯ ---
@app.route('/backup', methods=['POST'])
@login_required
@admin_required(['SuperAdmin'])
def backup_route():
    success, message = backup_database()
    
    if success:
        flash(message, 'success')
    else:
        # Виводимо перші 200 символів помилки, щоб не забивати Flash
        flash(f"Помилка резервного копіювання: {message[:200]}", 'error') 

    # Перенаправляємо назад на сторінку адміністратора або логів
    return redirect(url_for('admin_page'))

# --- МАРШРУТ 16: СТОРІНКА ЛОГІВ ---
@app.route('/logs')
@login_required
@admin_required(['SuperAdmin'])
def logs_page():
    log_entries = []
    log_file_path = 'app.log' # Використовуйте шлях до вашого лог-файлу

    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            # Читаємо останні 500 рядків логу (для оптимізації)
            log_entries = f.readlines()[-500:] 
    except FileNotFoundError:
        log_entries = ["Файл логів (app.log) не знайдено. Створіть його вручну або виконайте першу CRUD-операцію."]
    except PermissionError:
        log_entries = [f"ПОМИЛКА ПРАВ ДОСТУПУ: Не вдалося прочитати файл {log_file_path}. Перевірте права доступу для користувача, під яким працює Flask."]
    except Exception as e:
        log_entries = [f"Невідома помилка читання файлу логів: {e}"]
        
    # Перевертаємо список, щоб новіші записи були зверху
    log_entries.reverse() 
        
    return render_template(
        'logs.html', 
        title='Журнал Дій',
        log_entries=log_entries,
        user_rank=session.get('user_rank')
    )

# ==========================================================
# --- МАРШРУТ 17: для подачі файлів з папки 'script' ---
# ==========================================================
@app.route('/script/<path:filename>')
def script(filename):
    """Подає статичні файли з папки 'script'."""
    return send_from_directory('script', filename)

# ==========================================================
# API ENDPOINT: ОТРИМАННЯ ДЕТАЛЕЙ ОДНОГО ПОМІЧНИКА
# ==========================================================

# --- API ENDPOINT 1: ОТРИМАННЯ ВСІХ ПОМІЧНИКІВ (HelperInfo) ---
@app.route('/api/v1/helpers', methods=['GET'])
@login_required
def api_get_helpers():
    # Використовуємо існуючу функцію для отримання всіх помічників
    # Можна додати обробку параметрів 'query', 'sort_by' з request.args, як у home(),
    # але для простоти API v1 повернемо всі дані без фільтрації.
    helper_list = get_all_helpers() 
    
    # Конвертуємо список словників у JSON відповідь
    if helper_list:
        return jsonify({
            'status': 'success',
            'count': len(helper_list),
            'data': helper_list
        }), 200
    else:
        return jsonify({
            'status': 'error',
            'message': 'Дані HelperInfo не знайдено'
        }), 404

# --- API ENDPOINT 2: ОТРИМАННЯ ВСІХ ТІКЕТІВ (TicketInfo) ---
@app.route('/api/v1/tickets', methods=['GET'])
@login_required
def api_get_tickets():
    # Використовуємо існуючу функцію для отримання всіх тікетів
    ticket_list = get_all_tickets()

    # Конвертуємо список словників у JSON відповідь
    if ticket_list:
        return jsonify({
            'status': 'success',
            'count': len(ticket_list),
            'data': ticket_list
        }), 200
    else:
        return jsonify({
            'status': 'error',
            'message': 'Дані TicketInfo не знайдено'
        }), 404

# --- API ENDPOINT 3: ОТРИМАННЯ ДЕТАЛЕЙ ОДНОГО ПОМІЧНИКА ---
@app.route('/api/v1/helpers/<int:helper_id>', methods=['GET'])
@login_required
def api_get_helper_details(helper_id):
    helper = get_helper_by_id(helper_id)
    
    if helper:
        return jsonify({
            'status': 'success',
            'data': helper
        }), 200
    else:
        return jsonify({
            'status': 'error',
            'message': f'Помічника з ID {helper_id} не знайдено'
        }), 404


if __name__ == '__main__':
    app.run(debug=True)