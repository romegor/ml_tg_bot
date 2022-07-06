import base64
import logging
from aiogram import Bot, Dispatcher, executor, types
import json
from io import BytesIO
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram import types
# import asyncio
# import threading
# from multiprocessing import Pool
# from torchvision.utils import save_image

import aiohttp
# import asyncio
import os

if 'TOKEN' in os.environ.keys():
    TOKEN = os.environ['TOKEN']
else:
    print('Error! You need add TOKEN to env for start bot work')
    raise Exception("NO TOKEN ERROR")

if 'ml_srv_ip' in os.environ.keys():
    ml_srv_ip = os.environ['ml_srv_ip']
else:
    ml_srv_ip = "http://127.0.0.1"
if 'ml_srv_port' in os.environ.keys():
    ml_srv_port = str(os.environ['ml_srv_port'])
else:
    ml_srv_port = "5001"
if 'ml_srv_epoch' in os.environ.keys():
    ml_srv_epoch = int(os.environ['ml_srv_epoch'])
else:
    ml_srv_epoch = 200

class UserData(StatesGroup):
    original = State()
    style = State()


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Запустить бота"),
        types.BotCommand("help", "Помощь"),
        types.BotCommand("magic", "Изменение стиля"),
        types.BotCommand("super", "Улучшение изображения"),
        types.BotCommand("info", "Просмотр шаблонов"),
    ])

async def get_image_3(original, style, epoch=100, user_id=0):
    original.seek(0)
    style.seek(0)
    payload = {"image1": base64.b64encode(original.read()).decode("utf8"),
               "image2": base64.b64encode(style.read()).decode("utf8"),
               "epoch": epoch,
               "user_id": user_id}
    session_timeout = aiohttp.ClientTimeout(total=None, sock_connect=1200, sock_read=1200)
    # async with aiohttp.ClientSession(timeout=session_timeout) as session:
    #     async with session.post(ml_srv_ip + ':' + ml_srv_port + '/image_transform', json=payload,
    #                             allow_redirects=False, timeout=1200) as response:
    async with aiohttp.request("POST", ml_srv_ip + ':' + ml_srv_port + '/image_transform',
                               json=payload, timeout=session_timeout) as response:
        res = await response.text("utf-8")
        result = json.loads(res)
        img_bytes = base64.b64decode(result['magic_image'].encode('utf-8'))
        return BytesIO(img_bytes)

async def get_image_superres(img, user_id=0):
    img.seek(0)
    payload = {"image": base64.b64encode(img.read()).decode("utf8"),
               "user_id": user_id}
    session_timeout = aiohttp.ClientTimeout(total=None, sock_connect=300, sock_read=300)
    async with aiohttp.request("POST", ml_srv_ip + ':' + ml_srv_port + '/image_superres',
                               json=payload, timeout=session_timeout) as response:
    # async with aiohttp.ClientSession(timeout=session_timeout) as session:
    #     async with session.post(ml_srv_ip + ':' + ml_srv_port + '/image_superres', json=payload,
    #                             allow_redirects=False, timeout=300) as response:
        res = await response.text("utf-8")
        result = json.loads(res)
        img_bytes = base64.b64decode(result['superres_image'].encode('utf-8'))
        return BytesIO(img_bytes)

class MagicImageBot:
    def __init__(self):
        """Constructor"""
        self.work_flag = False
        # self.slow_model = slow_model.vgg16model()
        # self.pool = Pool(processes=2)
        # self.result_list = []
        self.styles = {}
        for style in os.listdir('templates'):
            # print(style)
            with open('templates/' + style, 'rb') as fh:
                self.styles[style.split('.')[0]] = BytesIO(fh.read())
        self.info = {}
        for style_info in os.listdir('templates_info'):
            # print(style_info)
            with open('templates_info/' + style_info, 'rb') as fh:
                self.info[style_info] = (BytesIO(fh.read()))

    def get_keyboard(self):
        # Генерация клавиатуры
        buttons = []
        for S in self.styles.keys():
            buttons.append(types.InlineKeyboardButton(text=S, callback_data='style_' + S))
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(*buttons)
        return keyboard

    def MainActivity(self):
        bot = Bot(token=TOKEN)
        storage = MemoryStorage()
        dp = Dispatcher(bot, storage=storage)


        # You can use state '*' if you need to handle all states
        @dp.message_handler(state='*', commands='cancel')
        @dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
        async def cancel_handler(message: types.Message, state: FSMContext):
            """
            Allow user to cancel any action
            """
            current_state = await state.get_state()
            if current_state is None:
                return

            logging.info('Cancelling state %r', current_state)
            # Cancel state and inform user about it
            await state.finish()
            # And remove keyboard (just in case)
            await message.reply('Заказ на прекрасную картину от искусственного интеллекта отменен',
                                reply_markup=types.ReplyKeyboardRemove())

        @dp.message_handler(commands=['help', 'start'])
        async def send_help(message: types.Message):
            """
            This handler will be called when user sends `/help` command
            """
            await message.answer('Привет, {name}! Присылай мне команду /magic, затем картинку, '
                                 'выбирай стиль и жди ее превращения!'
                                 .format(name=message.from_user.first_name))
            await message.answer('Чтобы посмотреть готовые варианты шаблонов, присылай /templates или /info')
            await message.answer('Если передумал, присылай /cancel и бот перестанет напрягаться '
                                 '(хотя может и обидеться =) )')
            await message.answer('А еще можно увеличить разрешение картинки, присылай /super, потом картинку и жди результата.'
                                 'Только не стоит присылать большую картинку (больше 640х640)')

        @dp.message_handler(commands=['magic'])
        async def send_original(message: types.Message, state: FSMContext):
            """
            This handler will be called when user sends `/magic` command
            """
            await message.answer('{name}, присылай мне картинку оригинал!'
                                 .format(name=message.from_user.first_name))
            await UserData.original.set()
            async with state.proxy() as data:
                data['command'] = 'magic'

        @dp.message_handler(commands=['templates', 'info'])
        async def send_template_info(message: types.Message):
            """
            This handler will be called when user sends `/magic` command
            """
            await message.answer('Держи картинки шаблонов')
            for X in self.info.keys():
                self.info[X].seek(0)
                await message.answer_photo(photo=self.info[X].getvalue())

        @dp.message_handler(content_types=['photo','document'], state=UserData.original)
        async def process_photo_command_original(message: types.Message, state: FSMContext):
            command = 'magic'
            async with state.proxy() as data:
                command = data['command']
            buffer = BytesIO()
            good_flag = False
            if len(message.photo) > 0:
                await message.photo[-1].download(buffer)
                good_flag = True
            elif message.document.mime_base == 'image':
                await message.document.download(buffer)
                good_flag = True
            if good_flag:
                if command == 'magic':
                    async with state.proxy() as data:
                        data['original'] = buffer
                    async with state.proxy() as data:
                        data['msg_id'] = message.message_id + 1
                    await UserData.next()
                    await message.answer('А теперь присылай картинку стиля или выбирай стиль из шаблонов', reply_markup=self.get_keyboard())
                elif command == 'super':
                    try:
                        res_flag = False
                        if len(message.photo) > 0:
                            if message.photo[-1].height > 640 or message.photo[-1].width > 640:
                                res_flag = True
                        else:
                            if message.document.thumb.height > 640 or message.document.thumb.width > 640:
                                res_flag = True
                        if res_flag:
                            await message.answer('Картинка итак в хорошем разрешении. Так не пойдет...')
                        else:
                            await message.answer('Искусственный интеллект начал работать')
                            res = await get_image_superres(buffer, message.from_user.id)
                            await message.answer_photo(photo=res)
                    except Exception as Ex:
                        print(Ex)
                        await message.answer(
                            'Наш искусственный интеллект сегодня не быстр, может вообще забыл, что делает. '
                            'Он же еще совсем маленький. Попробуйте еще раз')
                    await state.finish()
            else:
                await message.answer('Это не картинка! Бот все еще ждет файл с изображением')


        @dp.callback_query_handler(text_startswith='style_', state=UserData.style)
        async def callbacks_check(call: types.CallbackQuery, state: FSMContext):
            style = call.data.split("_")[1]
            async with state.proxy() as data:
                original = data['original']
            await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)

            await call.message.answer('Искусственный интеллект рисует по шаблону - <{template}>. Уже взял кисти в руки, '
                                      'подождите несколько минут'.format(template=style))
            try:
                res = await get_image_3(original, self.styles[style], ml_srv_epoch, call.message.from_user.id)
                await call.message.answer_photo(photo=res)
            except Exception as Ex:
                print(Ex)
                await call.message.answer(
                    'Наш искусственный интеллект сегодня не быстр, может вообще забыл, что делает. '
                    'Он же еще совсем маленький. Попробуйте еще раз')
            await state.finish()
            # await call.answer()

        @dp.message_handler(content_types=['photo','document'], state=UserData.style)
        async def image_transform(message: types.Message, state: FSMContext):
            original = None
            keyborad_msg_id = message.message_id
            async with state.proxy() as data:
                original = data['original']
                keyborad_msg_id = data['msg_id']
            buffer = BytesIO()
            good_flag = False
            if len(message.photo) > 0:
                await message.photo[-1].download(buffer)
                good_flag = True
            elif message.document.mime_base == 'image':
                await message.document.download(buffer)
                good_flag = True
            if good_flag:
                await bot.delete_message(chat_id=message.from_user.id, message_id=keyborad_msg_id)
                await message.answer('Искусственный интеллект пыатеся нарисовать первую картинку в стиле второй. '
                                     'Уже взял кисти в руки, подождите несколько минут', reply_markup=types.ReplyKeyboardRemove())
                # await message. .delete_reply_markup()

                try:
                    res = await get_image_3(original, buffer, ml_srv_epoch, message.from_user.id)
                    await message.answer_photo(photo=res)
                except Exception as Ex:
                    print(Ex)
                    await message.answer(
                        'Наш искусственный интеллект сегодня не быстр, может вообще забыл, что делает. '
                        'Он же совсем маленький. Попробуйте еще раз')
                await state.finish()
            else:
                await message.answer('Это не картинка! Бот все еще ждет файл с изображением')

        @dp.message_handler(commands=['super'])
        async def send_super(message: types.Message, state: FSMContext):
            """
            This handler will be called when user sends `/super` command
            """
            await message.answer('Привет, {name}! Присылай мне картинку для улучшения!'
                                 .format(name=message.from_user.first_name))
            await UserData.original.set()
            async with state.proxy() as data:
                data['command'] = 'super'
            # await message.answer('TEST')
            # with open('samurai_lr.png', 'rb') as fh:
            #     res = await get_image_superres(BytesIO(fh.read()), message.from_user.id)
            #     await message.answer_photo(photo=res)


        executor.start_polling(dp, skip_updates=True, on_startup=set_default_commands)



if __name__ == '__main__':
    while True:
        # bot = MagicImageBot()
        # bot.MainActivity()
        try:
            bot = MagicImageBot()
            bot.MainActivity()
        except Exception as Ex:
            print('Перезапуск бота')
