# Функция для создания изображений 
def generate_image(prompt, client):
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    if response and response.data and len(response.data) > 0:
        return response.data[0].url
    else:
        raise ValueError("Нет данных изображения в ответе.")