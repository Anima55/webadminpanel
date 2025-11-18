from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import psycopg
import os
from functools import wraps

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
def get_all_helpers(sort_by=None, sort_type='ASC'): # <--- ДОДАТИ: параметри сортування
    """Повертає всіх помічників з таблиці helperinfo, з можливістю сортування."""
    
    valid_sort_fields = ['helper_id', 'admin_name', 'admin_rank', 'warnings_count']
    order_column = sort_by if sort_by in valid_sort_fields else 'helper_id'
    order_direction = sort_type if sort_type in ('ASC', 'DESC') else 'ASC'
    
    sql = f"""
    SELECT helper_id, admin_name, admin_rank, warnings_count 
    FROM public.helperinfo 
    ORDER BY {order_column} {order_direction};
    """
    conn = get_connection()
    if conn is None: return [] 

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            column_names = [desc[0] for desc in cur.description]
            helpers = cur.fetchall()
            
            data = []
            for row in helpers:
                data.append(dict(zip(column_names, row)))
            return data

    except Exception as e:
        # print(f"❌ Помилка читання даних helperinfo: {e}")
        return []
    finally:
        conn.close()

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
    """Видаляє співробітника з таблиці helperinfo за ID."""
    sql = "DELETE FROM public.helperinfo WHERE helper_id = %s;"
    conn = get_connection()
    if conn is None: return False

    try:
        with conn.cursor() as cur:
            cur.execute(sql, (helper_id,))
        conn.commit()
        # Повертаємо True, якщо видалено принаймні один рядок
        return cur.rowcount > 0 
    except psycopg.errors.ForeignKeyViolation as e:
        # Ця помилка виникає, якщо співробітник має тікети (Foreign Key Constraint)
        print(f"❌ Помилка видалення: Співробітник ID {helper_id} має пов'язані записи в інших таблицях (тікети).")
        conn.rollback()
        return False
    except Exception as e:
        print(f"❌ Невідома помилка видалення: {e}")
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
# Функція для отримання всіх тікетів
def get_all_tickets(sort_by=None, sort_type='ASC'): # <--- ЗМІНА: Додано параметри сортування
    """Повертає всі тікети з таблиці ticketinfo, з можливістю сортування."""
    
    valid_sort_fields = ['ticket_id', 'submitter_username', 'handler_name', 'time_spent', 'resolution_rating']
    order_column = sort_by if sort_by in valid_sort_fields else 'ticket_id'
    order_direction = sort_type if sort_type in ('ASC', 'DESC') else 'ASC'
    
    sql = f"""
    SELECT 
        t.ticket_id, 
        t.submitter_username, 
        h.admin_name AS handler_name, 
        t.time_spent, 
        t.resolution_rating
    FROM public.ticketinfo AS t
    LEFT JOIN public.helperinfo AS h ON t.handler_helper_id = h.helper_id
    ORDER BY {order_column} {order_direction}; 
    """ # <--- ЦЕЙ ЗАПИТ ТЕПЕР ВИКОРИСТОВУЄТЬСЯ
    conn = get_connection()
    if conn is None: return []

    try:
        with conn.cursor() as cur:
            # !!! ЗМІНА: ВИКОРИСТОВУЄМО ДИНАМІЧНИЙ SQL-ЗАПИТ
            cur.execute(sql) 
            
            # Отримання імен колонок
            columns = [desc[0] for desc in cur.description]
            tickets_data = cur.fetchall()
            
            # Перетворення в список словників для зручності в Jinja2
            return [dict(zip(columns, ticket)) for ticket in tickets_data]
            
    except Exception as e:
        print(f"❌ Помилка отримання тікетів з БД: {e}")
        return []
    finally:
        if conn:
            conn.close()

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

# --- МАРШРУТ 3: СТОРІНКА ВХОДУ (login) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        # 1. Отримання даних з форми
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 2. Перевірка облікових даних у базі даних
        admin_info = check_webadmin_credentials(username, password) # <--- ВИКОРИСТОВУЄМО НОВУ ФУНКЦІЮ
        rank = get_webadmin_rank(username) # Викликаємо нову функцію
        
        if admin_info:
            # Успішний вхід: 
            session['logged_in'] = True 
            session['username'] = admin_info['webadmin_name'] # Зберігаємо ім'я користувача
            session['webadmin_id'] = admin_info['webadmin_id'] # Зберігаємо ID

            
            session['rank'] = rank if rank else 'user' # Зберігаємо роль, або 'user' за замовчуванням

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

# --- МАРШРУТ 1: ГОЛОВНА СТОРІНКА (helperinfo) ---
@app.route('/')
@login_required 
def home():
    """Відображає таблицю helperinfo, з підтримкою пошуку та сортування."""
    
    search_query = request.args.get('query', '')
    
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
        helpers = get_all_helpers(sort_by, sort_type) 
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
    
    return render_template('tickets.html', 
        title="Ticket Information", 
        table_data=tickets_data,
        col_headers=["ID", "Заявник", "Обробник", "Час (сек)", "Рейтинг"],
        main_content_title=main_title,
        item_count=item_count,
        ticket_list=tickets_data,
        user_rank=user_rank,
        sort_by=sort_by,
        sort_type=sort_type
        ) # <--- Тимчасовий фікс, якщо була помилка з item_count

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

# --- НОВИЙ МАРШРУТ 7: ПРИКЛАД СТОРІНКИ АДМІНА ---
@app.route('/admin-page')
# @login_required 
def admin_page():
    # Додаткова перевірка, щоб бути впевненим, що тільки адмін може її бачити
    if session.get('rank') != 'SuperAdmin':
        return redirect(url_for('home')) # Або інший маршрут для заборони доступу
        
    return "<h1>Вітаємо на сторінці Адміністратора!</h1>" # Замініть на render_template('admin_page.html')

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