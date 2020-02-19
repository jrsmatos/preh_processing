from datetime import datetime
from lxml import etree
import os
import time


def get_order_from_xml(xml):
    """
    Recolhe valor da tag lot_no (Ordem de fabrico) do xml.
    :param xml: path do ficheiro xml.
    :return: valor da tag lot_no ou None
    """
    tree = etree.parse(xml)
    order_element = tree.find('./lot_no')
    return order_element.text if order_element is not None else None


def parse(order_folder, xml_10, xml_11):
    tree_10 = etree.parse(xml_10)
    tree_11 = etree.parse(xml_11)
    ok_path = os.path.join(order_folder, '{}\\OK'.format(order_folder))
    nok_path = os.path.join(order_folder, '{}\\NOK'.format(order_folder))
    modules_per_panel = int(tree_11.find('./pcbs_in_panel').text)
    module_status = {}
    for module in range(modules_per_panel):
        module_sn = tree_11.find('serial_pcb_{}'.format(module + 1)).text
        status_top = tree_11.find('status_pcb_{}'.format(module + 1)).text
        status_bot = tree_10.find('status_pcb_{}'.format(module + 1)).text
        module_status[module_sn] = [status_top, status_bot]
        if not module_sn or len(module_sn) != 14:
            raise Exception('Campo "serial_pcb_<x>" não é válido.')
    ng_modules = []
    for key, value in module_status.items():
        if 'NG' in value:
            ng_modules.append(key)
    filename = xml_11.split('\\')[-1].split('_')[0][2:]

    if ng_modules:
        file_path = os.path.join(nok_path, '{}.xml'.format(filename))
    else:
        file_path = os.path.join(ok_path, '{}.xml'.format(filename))

    root = etree.Element("result_file")
    header = etree.SubElement(root, "header")
    etree.SubElement(header, "creation_date").text = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    etree.SubElement(header, "supplier_name").text = "Uartronica"
    etree.SubElement(header, "supplier_SAP_number").text = "Codigo_SAP_atribuido_Uartronica"
    etree.SubElement(header, "supplier_location").text = "Portugal"
    etree.SubElement(header, "last_vtpid").text = "10"
    etree.SubElement(header, "file_name").text = filename
    etree.SubElement(header, "file_length").text = "0"
    etree.SubElement(header, 'part_number').text = ''.join(tree_11.find('./program').text.split('_')[:3])

    module_no = 1
    for sn, status in module_status.items():
        module_info = etree.SubElement(root, "module_info")
        etree.SubElement(module_info, 'name').text = str(module_no)
        etree.SubElement(module_info, 'serial_number').text = sn

        if not 'NG' in status:
            etree.SubElement(module_info, 'result').text = '1'
        else:
            etree.SubElement(module_info, 'result').text = '0'

        module_no += 1

    temp_file = os.path.join('temp\\', str(time.time()) + '.xml')

    tree = etree.ElementTree(root)
    tree.write(temp_file, encoding='utf-8', xml_declaration=True, pretty_print=True)

    # reescreve o ficheiro com total de bytes atualizado
    new_value = os.path.getsize(temp_file)
    tree = etree.parse(temp_file)
    xml_length = tree.find('.//header//file_length')
    old_value = xml_length.text
    new_value += len(str(new_value)) - len(old_value)
    xml_length.text = str(new_value)

    # remove duplicado se existir
    if filename + '.xml' in os.listdir(ok_path):
        os.remove(os.path.join(ok_path, filename + '.xml'))
    if filename + '.xml' in os.listdir(nok_path):
        os.remove(os.path.join(nok_path, filename + '.xml'))

    tree.write(file_path, encoding='utf-8', xml_declaration=True, pretty_print=True)  # escreve xml
    os.remove(temp_file)
