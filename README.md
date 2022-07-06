Бот для телеграмма, позволяющий преобразовывать одно изображение на основе стиля другого .
А также имеется возможность увеличения разрешения изображения. Все происходит с помощью нейронной сети

Пример входного изображения
<p align="center">
<img src="https://github.com/romegor/ml_tg_bot/blob/main/img/in1.jpg">
</p>

Пример изображения стиля
<p align="center">
<img src="https://github.com/romegor/ml_tg_bot/blob/main/img/style.jpg">
</p>

<p align="center">
Пример изображения после обработки
<img src="https://github.com/romegor/ml_tg_bot/blob/main/img/out1.jpg">
</p>


Сам проект разделен на 2 части - непосредственно реализация бота и сервер, отвечающий за обработку изображений и к которому обращается бот. Разделение необходимо, чтобы обеспечивать асинхронную работу бота (при синфронной по сути реализации переноса стиля), а также для более удобной реализации дополнительной функциональности в будущем в качестве rest-сервисов

## BOT

Бот реализован с использованием библиотеки <a href="https://github.com/aiogram/aiogram"> aiogram</a>. 
Необходим Python 3.7 и выше с [asyncio](https://docs.python.org/3/library/asyncio.html) и [aiohttp](https://github.com/aio-libs/aiohttp).

## Параметры (env)
* TOKEN - собственно токен бота
* ml_srv_ip - адрес ml_server, с которым будет общаться бот (по умолчанию "http://127.0.0.1")
* ml_srv_port - порт ml_server, с которым будет общаться бот (по умолчанию "5001")
* ml_srv_epoch - количество эпох обучения (по умолчанию 200)

Количество эпох влияет на качество переноса стиля, однако напрямую также влияет на время выполнения.
На GPU рекомендуется около 500-700 эпох (хотя можно и больше), на CPU - это будет ОЧЕНЬ долгий процесс, поэтому 200 эпох для демонстрации работы будет достаточно.

У бота стоит ограничение по времени на ответ от ml_server (20 минут)

## Запуск

Запускаете выполнение скрипта bot/main.py с заданными параметрами и бот готов к использованию


## ML_SERVER

Сервер, на котором реализована обработка изображений с помощью нейронных сетей использует Python 3.7 и выше. Реализация нейросетей основана на [pytorch](https://github.com/pytorch/pytorch), а сам сервер на [fastapi](https://github.com/tiangolo/fastapi). Более подробные требования указаны в файле requirements.txt

## Параметры (env)
* ml_srv_port - порт ml_server, на которым будет работать сервер (по умолчанию "5001")
* ml_srv_imgsize - размер изображения на выходе [ml_srv_imgsize x ml_srv_imgsize] (по умолчанию 384 x 384)
* ml_srv_imgsize_cpu - размер изображения на выходе, если запуск на среде CPU (по умолчанию 256 x 256)

Размер изображения напрямую влияет на время выполнения, а также на объем используемой памяти (GPU или RAM).

## Запуск

Запускаете выполнение скрипта ml_server/ml_server.py с заданными параметрами и сервер готов к использованию.
Для удобства тестирования реализован интерфейс swagger по адресу ip_host:ml_srv_port/docs
