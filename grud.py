import psycopg
import os

# --- КОНФІГУРАЦІЯ БАЗИ ДАНИХ (ЗМІНІТЬ НА ВАШІ ДАНІ!) ---
DB_NAME = os.environ.get('DB_NAME', 'wdb')
DB_USER = os.environ.get('DB_USER', 'webadmin')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'admin')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')

# Рядок підключення у форматі URI
CONN_STRING = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def get_connection():
    """Створює та повертає об'єкт підключення."""
    try:
        conn = psycopg.connect(CONN_STRING)
        return conn
    except psycopg.OperationalError as e:
        print(f"Помилка підключення до бази даних: {e}")
        return None

# =======================================================
#                    ОПЕРАЦІЇ CRUD
# =======================================================

## ➕ CREATE (Створення нового Helper)
def create_helper(admin_name, admin_rank, warnings_count=0):
    """Додає нового помічника до таблиці helperinfo."""
    sql = """
    INSERT INTO public.helperinfo (admin_name, admin_rank, warnings_count) 
    VALUES (%s, %s, %s) 
    RETURNING helper_id;
    """
    conn = get_connection()
    if conn is None: return

    try:
        with conn.cursor() as cur:
            cur.execute(sql, (admin_name, admin_rank, warnings_count))
            new_id = cur.fetchone()[0]
            conn.commit()  # Застосовуємо зміни
            print(f"✅ Успішно створено нового помічника: ID={new_id}, Ім'я={admin_name}")
    except Exception as e:
        conn.rollback() # Відкочуємо зміни у разі помилки
        print(f"❌ Помилка створення помічника: {e}")
    finally:
        conn.close()

## 📖 READ (Читання всіх Helper-ів)
def read_all_helpers():
    """Виводить усіх помічників з таблиці helperinfo."""
    sql = "SELECT helper_id, admin_name, admin_rank, warnings_count FROM public.helperinfo ORDER BY helper_id;"
    conn = get_connection()
    if conn is None: return

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            helpers = cur.fetchall()
            
            print("\n===============================")
            print("Список усіх помічників (helperinfo)")
            print("===============================")
            if not helpers:
                print("База даних не містить помічників.")
            else:
                for helper in helpers:
                    print(f"ID: {helper[0]}, Ім'я: {helper[1]:<15}, Ранг: {helper[2]:<10}, Попереджень: {helper[3]}")
            print("===============================\n")

    except Exception as e:
        print(f"❌ Помилка читання даних: {e}")
    finally:
        conn.close()

## ✏️ UPDATE (Оновлення Helper-а)
def update_helper_rank(helper_id, new_rank):
    """Оновлює ранг помічника за його ID."""
    sql = "UPDATE public.helperinfo SET admin_rank = %s WHERE helper_id = %s;"
    conn = get_connection()
    if conn is None: return

    try:
        with conn.cursor() as cur:
            cur.execute(sql, (new_rank, helper_id))
            conn.commit()
            
            if cur.rowcount > 0:
                print(f"✅ Успішно оновлено ранг помічника ID={helper_id} на '{new_rank}'")
            else:
                print(f"⚠️ Помічника з ID={helper_id} не знайдено.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Помилка оновлення помічника: {e}")
    finally:
        conn.close()

## ⬆️ Видати попередження
def add_warning_to_helper(helper_id, warnings_to_add=1):
    """Збільшує кількість попереджень помічника за його ID."""
    sql = """
    UPDATE public.helperinfo 
    SET warnings_count = warnings_count + %s 
    WHERE helper_id = %s 
    RETURNING warnings_count;
    """
    conn = get_connection()
    if conn is None: return

    try:
        with conn.cursor() as cur:
            cur.execute(sql, (warnings_to_add, helper_id))
            conn.commit()
            
            if cur.rowcount > 0:
                new_count = cur.fetchone()[0]
                print(f"🔔 Успішно видано {warnings_to_add} попереджень помічнику ID={helper_id}. Нова кількість: {new_count}")
            else:
                print(f"⚠️ Помічника з ID={helper_id} не знайдено.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Помилка видачі попередження: {e}")
    finally:
        conn.close()
        
## ⬇️ Зняти попередження (НОВА ФУНКЦІЯ)
def remove_warning_from_helper(helper_id, warnings_to_remove=1):
    """Зменшує кількість попереджень помічника за його ID, не дозволяючи опуститися нижче нуля."""
    # Використовуємо GREATEST(0, ...) для запобігання від'ємним значенням
    sql = """
    UPDATE public.helperinfo 
    SET warnings_count = GREATEST(0, warnings_count - %s)
    WHERE helper_id = %s 
    RETURNING warnings_count;
    """
    conn = get_connection()
    if conn is None: return

    try:
        with conn.cursor() as cur:
            cur.execute(sql, (warnings_to_remove, helper_id))
            conn.commit()
            
            if cur.rowcount > 0:
                new_count = cur.fetchone()[0]
                print(f"✅ Успішно знято {warnings_to_remove} попереджень з помічника ID={helper_id}. Нова кількість: {new_count}")
            else:
                print(f"⚠️ Помічника з ID={helper_id} не знайдено.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Помилка зняття попередження: {e}")
    finally:
        conn.close()


## 🗑️ DELETE (Видалення Helper-а)
def delete_helper(helper_id):
    """Видаляє помічника за його ID."""
    sql = "DELETE FROM public.helperinfo WHERE helper_id = %s;"
    conn = get_connection()
    if conn is None: return

    try:
        with conn.cursor() as cur:
            cur.execute(sql, (helper_id,))
            conn.commit()
            
            if cur.rowcount > 0:
                print(f"✅ Успішно видалено помічника ID={helper_id}")
            else:
                print(f"⚠️ Помічника з ID={helper_id} не знайдено.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Помилка видалення помічника: {e}")
    finally:
        conn.close()


# =======================================================
#                      ІНТЕРФЕЙС
# =======================================================
def main_menu():
    """Головне меню консольного застосунку."""
    while True:
        print("\n=== МЕНЮ CRUD (HelperInfo) ===")
        print("1. Створити помічника (CREATE)")
        print("2. Показати всіх помічників (READ)")
        print("3. Оновити ранг помічника (UPDATE Rank)")
        print("4. Видати попередження (+Warning)")
        print("5. Зняти попередження (-Warning)")
        print("6. Видалити помічника (DELETE)")
        print("7. Вихід")
        
        choice = input("Оберіть опцію: ")

        if choice == '1':
            name = input("Введіть ім'я помічника: ")
            rank = input("Введіть ранг помічника: ")
            try:
                warnings = int(input("Кількість попереджень (залиште 0): ") or 0)
            except ValueError:
                print("Невірний формат числа. Встановлено 0.")
                warnings = 0
            create_helper(name, rank, warnings)
            
        elif choice == '2':
            read_all_helpers()
            
        elif choice == '3':
            try:
                helper_id = int(input("Введіть ID помічника для оновлення: "))
                new_rank = input("Введіть новий ранг: ")
                update_helper_rank(helper_id, new_rank)
            except ValueError:
                print("Невірний ID. Спробуйте ще раз.")
        
        elif choice == '4':
            try:
                helper_id = int(input("Введіть ID помічника, якому видати попередження: "))
                warnings_to_add = input("Скільки попереджень додати (залиште 1): ")
                warnings_to_add = int(warnings_to_add) if warnings_to_add.isdigit() and int(warnings_to_add) > 0 else 1
                add_warning_to_helper(helper_id, warnings_to_add)
            except ValueError:
                print("Невірний ID або кількість попереджень. Спробуйте ще раз.")
        
        elif choice == '5': # НОВА ОПЦІЯ ЗНЯТТЯ ПОПЕРЕДЖЕНЬ
            try:
                helper_id = int(input("Введіть ID помічника, з якого зняти попередження: "))
                warnings_to_remove = input("Скільки попереджень зняти (залиште 1): ")
                warnings_to_remove = int(warnings_to_remove) if warnings_to_remove.isdigit() and int(warnings_to_remove) > 0 else 1
                remove_warning_from_helper(helper_id, warnings_to_remove)
            except ValueError:
                print("Невірний ID або кількість попереджень. Спробуйте ще раз.")

        elif choice == '6':
            try:
                helper_id = int(input("Введіть ID помічника для видалення: "))
                delete_helper(helper_id)
            except ValueError:
                print("Невірний ID. Спробуйте ще раз.")
            
        elif choice == '7':
            print("Завершення роботи застосунку.")
            break
            
        else:
            print("Невірна опція. Спробуйте ще раз.")

if __name__ == "__main__":
    main_menu()