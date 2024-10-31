# Функция для получения сообщени из треда
def get_answer(thread_id, client):
    # Получение сообщений из потока
    thread_messages = client.beta.threads.messages.list(thread_id)
    if thread_messages.data:
        last_message = thread_messages.data[0]
        result = last_message.content[0].text.value  # Получение результата анализа
    else:
        result = "Нет сообщений в треде"
    return result