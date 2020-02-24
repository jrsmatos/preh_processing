from config import Config
from file_parser import get_order_from_xml, parse
from threading import Thread
from datetime import datetime
import glob
import shutil
import os
import time


def move_to_ignored(file):
    """
    Move ficheiro para a pasta 'ignorados'
    :param file: path do ficheiro
    :return: None
    """
    if not os.path.exists(os.path.join(Config.FOLDER, 'IGNORED')):
        os.mkdir(os.path.join(Config.FOLDER, 'IGNORED'))
    shutil.move(file, os.path.join(Config.FOLDER, 'IGNORED'))


def make_order_folder(folder):
    """
    Cria diretório para Ordem de fabrico
        > OF_xxxx
            > 10 (Guarda todos os ficheiro 10*.xml)
            > 11 (Guarda todos os ficheiros 11*.xml)
            > OK (Guarda ficheiros processados 'OK')
            > NOK (Guarda ficheiros processados 'NOK')
    :param folder: diretório da pasta OF
    :return: None
    """
    os.mkdir(folder)
    os.mkdir(os.path.join(folder, '10'))
    os.mkdir(os.path.join(folder, '11'))
    os.mkdir(os.path.join(folder, 'OK'))
    os.mkdir(os.path.join(folder, 'NOK'))


def get_latest(files):
    """
    Devolve o ficheiro mais recente de uma lista de ficheiros.
    :param files: lista de ficheiros
    :return: ficheiro mais recente
    """
    dates = {}
    for file in files:
        date = file.split('\\')[-1].split('_')[1]
        dates[file] = datetime.strptime(date, '%Y%m%d%H%M%S')

    now = datetime.now()
    latest = max(dates[dt] for dt in dates.keys() if dates[dt] < now)
    for key, value in dates.items():
        if value == latest:
            return key


class Sniffer(Thread):
    def __init__(self):
        """ Construtor  """
        super(Sniffer, self).__init__()
        self.stop = False

    def run(self):
        """ Inicia Thread """
        while not self.stop:
            files = glob.glob('{}\\*.xml'.format(Config.FOLDER))
            time.sleep(0.5)
            for file in files:
                if not str(file.split('\\')[-1]).startswith('10') and not str(file.split('\\')[-1]).startswith('11'):
                    # ficheiros que não começem por 10 ou 11 são ignorados
                    move_to_ignored(file)
                else:
                    order = get_order_from_xml(file)
                    if not order:
                        # ficheiros que não tenham a ordem de fabrico são ignorados
                        move_to_ignored(file)
                    else:
                        order_folder = os.path.join(Config.FOLDER, 'OF_{}'.format(order))
                        try:
                            if not os.path.exists(order_folder):
                                make_order_folder(order_folder)
                        except FileNotFoundError:
                            move_to_ignored(file)
                            continue
                        shutil.move(file, os.path.join(order_folder, file.split('\\')[-1]))

                        # se file for xml 11 (top) iniciar agregação dos ficheiros
                        if str(file.split('\\')[-1]).startswith('11'):
                            current_file = os.path.join(order_folder, file.split('\\')[-1])
                            sn_11 = current_file.split('\\')[-1].split('_')[0]
                            sn_10 = sn_11[0:2].replace(sn_11[0:2], '10') + sn_11[2:]

                            # lista todos os ficheiros (10 e 11) da mesma unidade
                            all_10 = glob.glob('{}\\{}*.xml'.format(order_folder, sn_10)) + \
                                     glob.glob('{}\\{}*.xml'.format(os.path.join(order_folder, '10'), sn_10))
                            all_11 = glob.glob('{}\\{}*.xml'.format(order_folder, sn_11)) + \
                                     glob.glob('{}\\{}*.xml'.format(os.path.join(order_folder, '11'), sn_11))

                            if all_10 and all_11:
                                # se existirem ficheiros 10 e 11 identifica o mais recente para ambos os casos
                                latest_10 = get_latest(all_10)
                                latest_11 = get_latest(all_11)

                                # inicia agregação do ficheiro
                                parse(order_folder, latest_10, latest_11)

                            for file in all_10:
                                shutil.move(file, os.path.join(os.path.join(order_folder, '10'), file.split('\\')[-1]))
                            for file in all_11:
                                shutil.move(file, os.path.join(os.path.join(order_folder, '11'), file.split('\\')[-1]))


def main():
    sniffer = Sniffer()
    sniffer.start()
    input("\nPress Any key to exit\n")
    sniffer.stop = True


if __name__ == '__main__':
    main()
