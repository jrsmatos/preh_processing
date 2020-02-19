import configparser

config = configparser.ConfigParser()
config.read('config.txt', encoding='utf-8-sig')


class Config:
    FOLDER = config.get('PATH', 'folder')
