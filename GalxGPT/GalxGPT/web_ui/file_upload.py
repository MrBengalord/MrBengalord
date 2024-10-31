# Функция для загрузки файла к ассистенту в ОпенАИ
def file_upload_GPT(file_content, client):
    try:
        with open(file_content, "rb") as file:
            response = client.files.create(
                file=file,
                purpose="assistants"
            )
        file_id = response.id
        return file_id
    except FileNotFoundError:
        print("Файл не найден. Пожалуйста, укажите корректный путь к файлу.")
        