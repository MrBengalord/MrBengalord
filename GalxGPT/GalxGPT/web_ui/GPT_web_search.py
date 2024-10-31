# -*- coding: utf-8 -*-
from openai import OpenAI
from bs4 import BeautifulSoup
#from googlesearch import search
from duckduckgo_search import DDGS
from empty_thread import form_thread_message
from start_thread_run_GPT import start_thread_run
from check_status import check_thread_stat
from get_answer import get_answer
from empty_thread import form_thread_message
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import re

# Инициализация ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=5)
# Основная функция для отрпавки и получения сообщений от ассистента в ОпенАИ
def main_code(assistant_id, user_input, client, thread_id=None):
    thread_id = form_thread_message(client, user_input)
    run_id_PER = start_thread_run(thread_id, assistant_id, client)
    check_thread_stat(thread_id, run_id_PER, client)
    response = get_answer(thread_id, client)
    return response, thread_id
# Функция для очистки текста
def clean_text(data):
    # Удаление HTML-тегов с помощью BeautifulSoup
    soup = BeautifulSoup(data, 'html.parser')
    cleaned_data = soup.get_text()
    # Удаление спецсимволов и лишних пробелов
    cleaned_data = re.sub(r'\s+', ' ', cleaned_data)  # Замена множества пробелов одним пробелом
    cleaned_data = cleaned_data.strip()  # Удаление пробелов в начале и конце строки
    # Удаление неалфавитных символов, оставляя только буквы и пробелы
    #cleaned_data = re.sub(r'[^a-zA-Zа-яА-ЯёЁ\s\.]', '', cleaned_data)
    #cleaned_data = re.sub(r'[^\w\s.,!?]', '', cleaned_data)
    return cleaned_data

def search_links(search_query, x):
    # Выполняем поиск в интернете с помощью Google и парсим первые 10 ссылок
    search_results_links = list(DDGS().text(search_query, max_results=x))
    # Извлекаем ссылки (значение по ключу 'href')
    links = [result['href'] for result in search_results_links if 'href' in result]
    return links

# Асинхронная функция для парсинга данных с веб страницы
# Функция для парсинга данных с веб страницы
def parse_page(url):
    # Имитация асинхронного парсинга через BeautifulSoup
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=7)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return url, soup.get_text()
        else:
            print(f'Ошибка подключения: {response.status_code}')
    except requests.exceptions.RequestException as e:
        print(f'Ошибка при запросе {url}: {e}')
    return url, ''

# Функция для обработки списка вебстраниц для парсинга данных с них
def parse_data_sync(search_results_links):
    # Используем ThreadPoolExecutor для обработки запросов параллельно
    all_parsed_data = ''
    successful_links = []
    num_parsed = 0
    futures = [executor.submit(parse_page, link) for link in search_results_links]
    flag = 0

    for future in as_completed(futures):    
        url, result = future.result()
        if num_parsed >= 2:
            break
        if result:
            if len(all_parsed_data + result)<800000:
                all_parsed_data += result + "\n\n"
                successful_links.append(url)
                num_parsed += 1
            else:
                flag = "Data exceed"
                break
    return all_parsed_data, successful_links, num_parsed, flag


# Функция поиска и обработки данных в интернете
def web_search_gpt(user_input, ASSISTANT_ID_Search_query_builder, ASSISTANT_ID_Web_summarize, client, thread_id=None):
    # Логика работы алгоритма: Вопрос пользователя -> ИИ формирует поисковой запрос -> Гугл парсит ссылки -> Парсим данные по ссылкам -> ИИ делает выводы по данным и сверяется с вопросом
    # функция main code это функция, где создается новый пустой тред, дальше кладется туда сообщение, запускается тред, опрашивается и получаем ответ. Каждый раз создаем новый тред!!!!
    # ИИ обрабатывает вопрос пользователя и формулирует поисковой запрос
    search_query, query_id = main_code(ASSISTANT_ID_Search_query_builder, user_input, client, thread_id=thread_id)
    # Работаем с вебпоиском
    search_results_links = search_links(search_query, 10)  # С помощью google библиотеки парсим ссылки из поиска, которые нашли по поисковому запросу
    # Разделяем ссылки на два списка, за счет этого достигается приоритезация парсинга первых 5 ссылок, а если из них удалось запарсить менее 3 сайтов подключается второй батч ссылок
    first_batch = search_results_links[:5]
    second_batch = search_results_links[5:]
    # С помощью aiohttp и BeautifulSoup парсим текст по ссылкам из первого батча
    all_parsed_data, successful_parsed_links, num_parsed_first_batch, flag = parse_data_sync(first_batch)
    # Если не удалось собрать достаточно данных, обрабатываем второй батч ссылок
    if num_parsed_first_batch < 2:
        additional_data, additional_links, num_parsed_second_batch, flag = parse_data_sync(second_batch)
        all_parsed_data += additional_data
        successful_parsed_links += additional_links
    successful_parsed_links = ", ".join(successful_parsed_links)
    # Если данные превышают допустимый размер
    if flag == "Data exceed":
        web_summary = "Объем обнаруженных данных превышает лимиты. Пожалуйста, попробуйте самостоятельно изучить сайты, которые мы нашли." + "\n\n" + f"<b>Поисковой запрос: </b>{search_query}" + "\n\n" + "<b>Источники данных: </b>" + successful_parsed_links
        all_data =  "Мой вопрос: " + user_input + "." + "\n\n" + "Данные, которые я нашел в интернете: " + web_summary
    # Если данные в порядке
    else:            
        # Очищаем полученный ответ от ШТМЛ тегов и спецсимволов с пробелами
        all_parsed_data = clean_text(all_parsed_data)
        # Если необходимых данных нет 
        if not all_parsed_data:
            web_summary = "Объем обнаруженных данных превышает лимиты. Пожалуйста, попробуйте самостоятельно изучить сайты, которые мы нашли." + "\n\n" + f"<b>Поисковой запрос: </b>{search_query}" + "\n\n" + "<b>Источники данных: </b>" + successful_parsed_links
            all_data =  "Мой вопрос: " + user_input + "." + "\n\n" + "Данные, которые я нашел в интернете: " + web_summary
            return ("К сожалению, мне не удалось получить информацию из Интернета. Но вы можете самостоятельно изучить сайты: " + ', '.join(search_results_links), user_input, "")

        # ИИ формулирует финальный ответ
        all_data = "Мой вопрос: " + user_input + "." + "\n\n" + "Данные, которые я нашел в интернете: " + all_parsed_data  # корректируем input в ИИ. К данным приклеиваем изначальный вопрос пользователя + запарсенные данные
        web_summary, thread_id = main_code(ASSISTANT_ID_Web_summarize, all_data, client)  # ИИ делает выводы по данным и сверяется с вопросом
        web_summary = web_summary + "\n\n" + f"<b>Поисковой запрос: </b>{search_query}" + "\n\n" + "<b>Источники данных: </b>" + successful_parsed_links  # К финальному ответу ИИ добавляем текст с источниками данных (сайты откуда парсили информацию)

    return web_summary, user_input, all_data
