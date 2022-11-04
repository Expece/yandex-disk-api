import os

from starlette.config import Config


dir_path = os.path.dirname(os.path.realpath(__file__))
root_dir = dir_path[:-3]

config = Config(f'{root_dir}.env')

DATABASE_URL = f'sqlite:///{root_dir}' + config('DB_NAME', cast=str)
VERSION = '0.1'
PROJECT_NAME = 'Yet Another Disk Open API'
PROJECT_DESCRIPTION = 'Вступительное задание в Осеннюю Школу Бэкенд Разработки Яндекса 2022'
BASE_ROUTER='Задачи'
