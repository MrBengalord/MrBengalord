from flask import Flask, render_template, request, session, redirect, url_for, flash
import os
import openai
from openai import OpenAI
from dotenv import load_dotenv
import shutil
from empty_thread import form_thread_message
from start_thread_run_GPT import start_thread_run
from check_status import check_thread_stat
from get_answer import get_answer
from generate_image import generate_image
from GPT_web_search import web_search_gpt
from db_write_logs import save_logs_to_postgresql
from db_write_label import save_label_to_postgresql
import re
from datetime import datetime
import uuid
import getpass
from flask import request, abort
from flask_session import Session
import logging

# Проверка существования файла .env, из него мы будем забирать все необходимые ключи для работы
env_path = os.path.join(os.getcwd(), '.env')
if not os.path.exists(env_path):
    raise FileNotFoundError(f".env file not found at {env_path}")

# Загрузка переменных окружения из файла .env
load_dotenv()
# подтягиваем апи ключ для работы с ОпенАИ через environ
API_KEY = os.getenv('API_KEY')
# подтягиваем id основного ассистента через environ
ASSISTANT_ID = os.getenv('ASSISTANT_ID')
# подтягиваем id  всех остальных неободимых ассистентов через environ
ASSISTANT_ID_Search_query_builder = os.getenv('ASSISTANT_ID_Search_query_builder')  # ассистент, который формирует текст запроса в гугл
ASSISTANT_ID_Web_summarize = os.getenv('ASSISTANT_ID_Web_summarize')  # ассистент анализирует данные и выдает саммари, а также проверяет, что данные отвечают на вопрос
# подтягиваем ключи для записи в базу данных
# db_name = os.getenv('db_name')
# db_user = os.getenv('db_user')
# db_password = os.getenv('db_password')
# db_host = os.getenv('db_host')

if not API_KEY:
    raise ValueError("API_KEY is not set. Please provide a valid OpenAI API key.")
if not ASSISTANT_ID:
    raise ValueError("ASSISTANT_ID is not set. Please provide a valid Assistant ID.")

# Настройка клиента OpenAI с таймаутом и максимальным числом повторных попыток
client = OpenAI(api_key=API_KEY, timeout=100.0, max_retries=3)

app = Flask(__name__)

# Задаем условие использования filesystem
app.config['SESSION_TYPE'] = 'filesystem'

app.secret_key = os.urandom(24)  # Секретный ключ для сохранения данных сессии
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

# Инициализируем сессию
Session(app)

# Максимальный разрешенный размер файла в байтах (10 МБ)
MAX_FILE_SIZE = 5 * 1024 * 1024

# # Допустимые типы файлов
# ALLOWED_EXTENSIONS = {
#     "txt", "pdf", "png", "jpg", "jpeg", "csv", "xlsx", "xls", "xlsm", "doc", "docx"
# }

# Допустимые типы файлов
ALLOWED_EXTENSIONS = {
    "png", "jpg", "jpeg"
}

@app.route('/', methods=['GET', 'POST'])
def index_final():
    history = session.get('history', [])
    if request.method == 'POST':

        user = getpass.getuser()  # Получение имени текущего пользователя
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Получение текущей даты и времени
        session_id = session.get('session_id', str(uuid.uuid4())) # Получение текущей сессии
        thread_id = session.get('thread_id') # Получение текущего треда
        functions = "GPT" # Получение текущей функции
        assistant_id = ASSISTANT_ID  # Задаем ассистента
        uploaded_file = None
        prompt = request.form.get('prompt_field') # Получение текущего промта
        uploaded_file = request.files.get('file') # Получение приложенного файла
        create_image = request.form.get('create_image')  # Получаем значение переключателя
        if create_image: # Проверка значения переключателя
            functions = "Dall-e" # Задаем текущую функцию
        web_search = request.form.get('web_search')  # Получаем значение переключателя
        if web_search: # Проверка значения переключателя
            functions = "Web-Gpt" # Задаем текущую функцию
            assistant_id = ASSISTANT_ID_Web_summarize  # Меняем ассистента на искателя по интернету
        file_path = None
        # Проверка значения переключателя
        if create_image:
            try:
                # generate_image возвращает URL изображения
                img_link = generate_image(prompt, client)
                session['img_link'] = img_link # Сохраняем ссылку на изображение в сессии
                run_id = session.get('run_id')
                # Добавляем запрос и ответ (ссылка на изображение) в историю
                history.append((prompt, f'<img src="{img_link}" alt="Generated Image" />'))
                session['history'] = history
                # Сохраняем данные в базу данных
                # save_logs_to_postgresql(user, date, prompt, img_link, assistant_id, session_id, thread_id, run_id, functions, db_name, db_user, db_password, db_host)
            # Проверка на возникновение ошибок  
            except Exception as e:
                error_message = f"Ошибка при генерации изображения: {str(e)}"
                error_message = re.sub(r'<[^>]+>', '', error_message)  # Удаление HTML тегов из сообщения об ошибке
                # Выводим ошибку в интерфейс
                history.append((prompt, error_message))
                session['history'] = history
            
            return redirect(url_for('index_final')) 
        # Проверка значения переключателя
        elif web_search:
            thread_id = session.get('thread_id')
            run_id = session.get('run_id')
            # Используем функцию web_search_gpt, получаем 3 параметра: 
            response, user_input, all_data = web_search_gpt(prompt, ASSISTANT_ID_Search_query_builder, ASSISTANT_ID_Web_summarize, client, thread_id)
            history.append((user_input, response))
            session['history'] = history  # Сохраняем историю в сессии
                            
            ################ ################ ################ ################ ################  tyt mi bydem vstavlyat v tred soobsheniya
            if thread_id:
                client.beta.threads.messages.create(
                    thread_id=thread_id,  # Указание существующего идентификатора треда
                    role="user",  # Указываем роль отправителя (user, assistant и т.д.)
                    content=all_data  # Передаем текст сообщения, который вы хотите отправить
                )
                client.beta.threads.messages.create(
                    thread_id=thread_id,  # Указание существующего идентификатора треда
                    role="assistant",  # Указываем роль отправителя (user, assistant и т.д.)
                    content=response  # Передаем текст сообщения, который вы хотите отправить
                )
            ################ ################ ################ ################ ################ ################
            else:
                # Создаем новый поток
                thread_id = form_thread_message(client, user_input=all_data)

                client.beta.threads.messages.create(
                    thread_id=thread_id,  # Указание существующего идентификатора треда
                    role="assistant",  # Указываем роль отправителя (user, assistant и т.д.)
                    content=response  # Передаем текст сообщения, который вы хотите отправить
                )
                # Сохраняем thread_id в сессии
                session['thread_id'] = thread_id
                first_three_words = ' '.join(prompt.split()[:3])
                # save_label_to_postgresql(thread_id, first_three_words, db_name, db_user, db_password, db_host)
            # save_logs_to_postgresql(user, date, prompt, response, assistant_id, session_id, thread_id, run_id, functions, db_name, db_user, db_password, db_host)

            return redirect(url_for('index_final'))

        else:
            prompt_old = prompt
            if uploaded_file and uploaded_file.filename != '':
                give_file = "Я передаю тебе файл, взаимодействуй с ним, как тебе скажет пользователь."
                prompt = give_file + " " + prompt
                # Проверка размера файла
                if uploaded_file.content_length > MAX_FILE_SIZE:
                    flash("Максимальный размер файла не больше 10 МБ", "danger")
                    return redirect(url_for('index_final'))

                # Проверка формата файла
                file_extension = uploaded_file.filename.rsplit('.', 1)[1].lower()
                if file_extension not in ALLOWED_EXTENSIONS:
                    flash(f": Пока еще нельзя приложить файл такого формата. Допустимые форматы файлов: {', '.join(ALLOWED_EXTENSIONS)}", "danger")
                    return redirect(url_for('index_final'))
                else:
                    # Сохраняем файл на сервере
                    file_path = os.path.join('uploads', uploaded_file.filename)
                    uploaded_file.save(file_path)

            if prompt:

                # Обращение к переменным
                user = getpass.getuser()  # Получение имени текущего пользователя
                assistant_id = ASSISTANT_ID  # Уже определено
                session_id = session.get('session_id', str(uuid.uuid4()))
                thread_id = session.get('thread_id')

                if thread_id:
                    # Обновляем существующий поток
                    form_thread_message(client, prompt, thread_id, file_path)
                else:
                    # Создаем новый поток
                    thread_id = form_thread_message(client, user_input=prompt, file_path=file_path)
                    first_three_words = ' '.join(prompt.split()[:3])
                    # save_label_to_postgresql(thread_id, first_three_words, db_name, db_user, db_password, db_host)
                    # Сохраняем thread_id в сессии
                    session['thread_id'] = thread_id

                # Запуск нового треда с заданным ассистентом
                run_id = start_thread_run(thread_id, ASSISTANT_ID, client)
                session['run_id'] = run_id

                # Проверка статуса треда
                check = check_thread_stat(thread_id, run_id, client)
                # Если статус треда "completed", выведем статус

                answer = get_answer(thread_id, client)
                #answer = re.sub(r'(\w+):', r'\1&#58;', answer)  # Замена двоеточий в нужных местах
                
                # Регулярное выражение для поиска блоков кода, заключённых в тройные кавычки
                code_pattern = re.compile(r'```(.*?)```', re.DOTALL)
                # Замена блоков кода на HTML-теги для форматирования
                answer = code_pattern.sub(r'<pre><code>\1</code></pre>', answer)
                # Применяем регулярное выражение для удаления текста внутри 【】 из ответа
                answer = re.sub(r'【.*?】', '', answer)

                # save_logs_to_postgresql(user, date, prompt, answer, assistant_id, session_id, thread_id, run_id, functions, db_name, db_user, db_password, db_host)
                

                # Добавляем запрос и ответ в историю сессии
                history.append((prompt_old, answer))
                session['history'] = history

                upload_folder = 'uploads'

                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                else:
                    # Очищаем содержимое папки, но не удаляем саму папку.
                    for filename in os.listdir(upload_folder):
                        file_path = os.path.join(upload_folder, filename)
                        try:
                            if os.path.isfile(file_path) or os.path.islink(file_path):
                                os.unlink(file_path)
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                        except Exception as e:
                            print(f"Не удалось удалить {file_path}. Причина: {e}")

    return render_template('index_final.html', history=history, error_message=None)

@app.route('/clear_session', methods=['POST'])
# функция оцичстки сессии
def clear_session():
    session.clear()
    return redirect(url_for('index_final'))

@app.after_request
def error_for_large_cookie(response):
    # Получаем все Set-Cookie заголовки
    cookies = response.headers.getlist("Set-Cookie")
    
    # Суммируем длину всех заголовков
    total_cookie_size = sum(len(cookie.encode('utf-8')) for cookie in cookies)
    
    if total_cookie_size >= 4093:
        abort(400, "Cookie size too large.")
    
    return response

# Запуск приложения
if __name__ == '__main__':          
    app.run(host='0.0.0.0', port=5005, debug=True)