import pandas as pd
import os
#from docx import Document
import pypandoc
# Функция для конвертации файла
def convert_to_txt(file_path):
    if not os.path.exists(file_path):
        return "Файл не найден. Пожалуйста, укажите корректный путь к файлу."
    try:
        file_extension = file_path.split('.')[-1].lower()
        # Конвертация файла эксель
        if file_extension == 'xlsx':
            df = pd.read_excel(file_path)
            txt_file_path = file_path.replace(f".{file_extension}", ".txt")
            df.to_csv(txt_file_path, index=False, header=True)
            return txt_file_path
        # Конвертация файла эксель
        if file_extension == 'xls':
            df = pd.read_excel(file_path)
            txt_file_path = file_path.replace(f".{file_extension}", ".txt")
            df.to_csv(txt_file_path, index=False, header=True)
            return txt_file_path
        # Конвертация файла эксель
        if file_extension == 'xlsm':
            df = pd.read_excel(file_path)
            txt_file_path = file_path.replace(f".{file_extension}", ".txt")
            df.to_csv(txt_file_path, index=False, header=True)
            return txt_file_path
        # Конвертация файла цсв
        elif file_extension == 'csv':
            df = pd.read_csv(file_path, encoding='cp1251', delimiter=';', on_bad_lines='skip')
            txt_file_path = file_path.replace(f".{file_extension}", ".txt")
            df.to_csv(txt_file_path, index=False, header=True)
            return txt_file_path
        # Конвертация файла пдф
        elif file_extension == 'pdf':
            # Если формат PDF, просто возвращаем оригинальный путь без конверсии
            return file_path
        # Конвертация файла докс
        elif file_extension == 'docx':
            # Обработка файлов формата docx
            txt_file_path = file_path.replace(f".{file_extension}", ".txt")
            #doc = Document(file_path)
            # with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
            #     for para in doc.paragraphs:
            #         txt_file.write(para.text + '\n')
            # return txt_file_path
        # Конвертация файла док    
        elif file_extension == 'doc':
            # Обработка файлов формата doc с помощью pypandoc
            txt_file_path = file_path.replace(f".{file_extension}", ".txt")
            output = pypandoc.convert_file(file_path, 'plain', outputfile=txt_file_path)
            return txt_file_path
        else:
            return file_path
    except Exception as e:
        return f"Error converting file: {e}"