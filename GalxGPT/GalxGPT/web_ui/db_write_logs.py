import psycopg2
from datetime import datetime
import os 

# Функция для записи данных в таблицу YT_LOGGS_WEBX
def save_logs_to_postgresql(user, date, prompt, answer, assistant_id, session_id, thread_id, run_id, functions, db_name, db_user, db_password, db_host):
    conn = None
    cursor = None
    try:
        # Параметры подключения
        dsn = {
            'dbname': db_name,
            'user': db_user,
            'password': db_password,
            'host': db_host,
            'port': '5432'
        }
        
        # Формат 'YYYY-MM-DD HH:MM:SS'
        current_datetime = datetime.now()
        
        # Подключаемся к БД
        conn = psycopg2.connect(**dsn)
        cursor = conn.cursor()
        
        # Выполняем вставку данных
        cursor.execute('''
            INSERT INTO rechat.log ("user",date,prompt,answer,assistant_id,session_id,thread_id,run_id,function)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (user, date, prompt, answer, assistant_id, session_id, thread_id, run_id, functions))
        
        # Фиксируем изменения
        conn.commit()
        
    except psycopg2.Error as e:
        print(f"Произошла ошибка при записи в PostgreSQL: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()