from convert_to_txt import convert_to_txt
from file_upload import file_upload_GPT
# Функция для создания сообщения в треде
def form_thread_message(client, user_input="", thread_id=None, file_path=None):
    # Создаем новый поток, если идентификатор потока не существует
    if thread_id is None:
        empty_thread = client.beta.threads.create()
        thread_id = empty_thread.id

    # Предопределенный контент сообщения
    message_content = [
        {
            "type": "text",
            "text": user_input
        }
    ]

    # Проверяем наличие прикрепленного файла
    if file_path:
        txt_file_path = convert_to_txt(file_path)
        if not txt_file_path:
            raise ValueError("Файл не был конвертирован.")
        
        # Проверка формата файла
        allowed_formats = ['png', 'jpeg', 'jpg']
        file_extension = txt_file_path.split('.')[-1].lower()
        # Если файл не допустимого формата, пробуем его загрузить так
        if file_extension not in allowed_formats:
            file_id = file_upload_GPT(txt_file_path, client)
            if not file_id:
                raise ValueError("Файл не был загружен на сервер.")
            
            # Передаём ассистенту файл на анализ
            message_data = {
                "thread_id": thread_id,
                "role": "user",
                "content": message_content,
                "attachments": [{
                    "file_id": file_id,
                    "tools": [{"type": "file_search"},
                              {"type": "code_interpreter"}]
                }]
            }
        # Если файл в допустимом формате, то есть если он картинка
        else:
            file_id = file_upload_GPT(txt_file_path, client)
            if not file_id:
                raise ValueError("Картинка не была загружена на сервер.")
            
            message_content.append({
                "type": "image_file",
                "image_file": {
                    "file_id": file_id
                }
            })

            message_data = {
                "thread_id": thread_id,
                "role": "user",
                "content": message_content
            }

    # Если файл не был приложен
    else:
        message_data = {
            "thread_id": thread_id,
            "role": "user",
            "content": message_content
        }

    thread_message = client.beta.threads.messages.create(**message_data)
    return thread_id  # Возвращаем идентификатор треда