# Функция для запуска треда с сообщениями
def start_thread_run(thread_id, assistant_id, client):
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    run_id_PEREMEN = run.id
    thread_id = run.thread_id
    thread_status = run.status
    print("Статус обработки треда:", thread_status)
    return run_id_PEREMEN