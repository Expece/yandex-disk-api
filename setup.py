from setuptools import setup

setup(
    name='disk',
    version='0.0.1',
    author='Misha G',
    author_email='meja1@inbox.ru',
    description='disk api',
    install_requires=[
        'fastapi==0.83.0',
        'requests==2.28.1',
        'SQLAlchemy==1.4.41',
        'uvicorn==0.18.3'
    ],
    scripts=['app/main.py']
)