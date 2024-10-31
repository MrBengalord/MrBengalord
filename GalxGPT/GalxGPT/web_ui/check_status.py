import time
# Функция для проверки статуса треда
def check_thread_stat(thread_id, run_id_PEREMEN, client):
    # Время начала выполнения функции
    start_time = time.monotonic()
    timeout=600
    while True:
        # Получение информации о текущем запуске треда
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id_PEREMEN
        )
        # Задаем переменную для вывода статуса треда
        thread_status = run.status
        print("Статус обработки треда:", thread_status)
        # Проверяем статус треда
        if thread_status == 'completed':
            return run  # Возвращаем объект run, когда статус станет "completed"
        
        # Проверяем, прошло ли больше времени, чем заданный таймаут
        elapsed_time = time.monotonic() - start_time
        if elapsed_time > timeout:
            print("Проверка треда превысила лимит времени")
            return None  # Или выбросить исключение, или выполнить другую логику
        # Проверяем статус треда и заканчиваем работу, если тред не получилось обработать
        if thread_status == 'failed':
            break
        time.sleep(0.1)  # Ждем 0.1 секунды перед следующей проверкой