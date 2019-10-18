# -*- coding: utf-8 -*-
import os
import sys
import time
from queue import Queue
from threading import Thread
import re
import datetime
import config
import psutil


from WebWhatsapp.webwhatsapi import WhatsAPIDriver
from WebWhatsapp.webwhatsapi.objects.message import MediaMessage, Message

queue1 = Queue()
queue2 = Queue()

queue_dict = {
    queue1 : "queue1",
    queue2 : "queue2"
}
# with open("queue1-listen.csv", "r") as queue1_listen:
#     text = queue1_listen.read()
#     text = re.sub(r"\#\$\#\$\#\n\n*", "\n", text)
#     len_queue1_listen = len(text.split("\n"))
# with open("queue1-write.csv", "r") as queue1_write:
#     text = queue1_write.read()
#     text = re.sub(r"\#\$\#\$\#\n\n*", "\n", text)
#     len_queue1_write = len(text.split("\n"))
# with open("queue2-listen.csv", "r") as queue2_listen:
#     text = queue2_listen.read()
#     text = re.sub(r"\#\$\#\$\#\n\n*", "\n", text)
#     len_queue2_listen = len(text.split("\n"))
# with open("queue2-write.csv", "r") as queue2_write:
#     text = queue2_write.read()
#     text = re.sub(r"\#\$\#\$\#\n\n*", "\n", text)
#     len_queue2_write = len(text.split("\n"))

# diff_queue1 = len_queue1_listen - len_queue1_write
# if diff_queue1 > 0:
#     with open("queue1-listen.csv", "r") as queue1_listen:
#         lines = queue1_listen.readlines()
#         for i in range(diff_queue1):
#             line = lines[len_queue2_write+i-1]
#             msg_type, path, caption = line[:-5].split("###")
#             queue1.put((msg_type, path, caption))
# diff_queue2 = len_queue2_listen - len_queue2_write
# if diff_queue2 > 0:
#     with open("queue2-listen.csv", "r") as queue2_listen:
#         lines = queue2_listen.readlines()
#         for i in range(diff_queue2):
#             line = lines[len_queue2_write+i-1]
#             msg_type, path, caption = line[:-5].split("###")
#             queue1.put((msg_type, path, caption))


def get_all_contacts(driver):
    retorno = driver.get_my_contacts()
    contatos = {}
    for x in retorno:
        json = x._js_obj
        contatos[json['id']['user']] = json['formattedName']
    return contatos

def change_contact(text, contacts):
    mencoes = re.findall(r"\d{12}", text)
    for mencao in mencoes:
        if mencao in contacts.keys():
            contactName = contacts[mencao]
            text = text.replace(mencao, contactName)
        else:
            print(f"Contact not found, number {mencao}")
    return text

def select_contact(contacts, selected_contact):
    for contact in contacts:
        c_name = contact.chat.name
        if selected_contact == c_name:
            return contact
    return False


directory_path = os.path.normpath(os.getcwd())
temp_folder = os.path.normpath(directory_path + os.sep + "temp")

def text_formatting(group_number, sender, text):
    text = change_contact(text, contacts)
    return f'[{group_number}] *_{sender}_*: {text}'

def save_media(message):
    file_name = message.filename
    file_path = temp_folder + os.sep + file_name
    message.save_media(temp_folder, force_download=True)
    return file_path


def listen(driverNumber, queue, group):
    time.sleep(20)
    while True:
        if (config.reset == True):
            print(statusThread)
            statusThread["listen"+driverNumber] = False
            print(f"thread listen{driverNumber} parada")
            time.sleep(3)
            continue
  
        try:
            contacts = config.driver[driverNumber].get_unread()
            contact = select_contact(contacts, group)
        except Exception as identifier:
            print(f"Erro ao carregar os contatos {identifier}")
            continue
        if contact:
            for message in contact.messages:
                msg_type = message.type
                sender = message.sender.name
                group_number =config.groups[group]
                text = ""
                file_path = "no path"
                if msg_type in ['document', 'image' ,'video', 'ptt', 'audio']:
                    if msg_type in ['image' ,'video']:
                        text = message.caption
                    file_path = save_media(message)
                    formatted_text = text_formatting(group_number, sender, text)
                    queue.put((msg_type, file_path, formatted_text))
                    # print(msg_type)
                elif msg_type == "chat":
                    text = message.content
                    formatted_text = text_formatting(group_number, sender, text)
                    # print(f'[{group_number}] *_{sender}_*: {text}')
                    queue.put((msg_type, file_path, formatted_text))
                queue_file = queue_dict[queue] + "-listen.csv"
                with open(queue_file, "a+") as queue_file_content:
                    queue_file_content.write(f"{msg_type}###{file_path}###{formatted_text}#$#$#\n")
                print(f"Listened: {msg_type}-{file_path}-{formatted_text}")


def write(driverNumber, queue, group_id):
    time.sleep(10)
    while True:
        #print("write thread live")
        if (config.reset == True):
            if(statusThread["listen"+driverNumber] == False):
                statusThread["write"+driverNumber] = False
                #print(f"thread write{driverNumber} parada")
                time.sleep(3)
                continue
        if not queue.empty():
            print('fila' + driverNumber)
            msg_type, path, caption = queue.get()
            print(f"Removed from queue: {msg_type}-{path}-{caption}")
            try:
                contact = config.driver[driverNumber].get_contact_from_id(group_id)
            except Exception as identifier:
                config.reset=True
                print(" ------------------ Reiniciaaando Thread por não conseguir recuperar conteudo------------------")
                print(identifier)
            if msg_type == "chat":
                send_message(contact, caption)
            elif msg_type in ['document', 'image' ,'video', 'ptt', 'audio']:           
                chat_id = contact.get_chat().id
                print(f"write in path: {path}")
                if msg_type in ['document', 'ptt', 'audio']:
                    send_media(config.driver[driverNumber], path, chat_id, "")
                    time.sleep(1)
                    contact.get_chat().send_message(caption)
                else:
                    send_media(config.driver[driverNumber], path, chat_id, caption)
                os.remove(path)
                print(f"Deleted: {path}")
            elif msg_type == "sticker":
                pass
            print(f"Writed: {msg_type}-{path}-{caption}")
            queue_file = queue_dict[queue] + "-write.csv"
            with open(queue_file, "a+") as queue_file_content:
                queue_file_content.write(f"{msg_type}###{path}###{caption}#$#$#\n")

def send_message(contact, message):
    error_counter = 0
    try:
        contact.get_chat().send_message(message)
    except Exception as e:
        print(f"[{error_counter}] Error trying to send message - {e}")
        error_counter += 1
        send_message(contact, message)

def send_media(driver, path, chat_id, caption):
    error_counter = 0
    try:
        driver.send_media(path, chat_id, caption)
    except Exception as e:
        print(f"[{error_counter}] Error trying to send media - {e}")
        error_counter += 1
        send_media(driver, path, chat_id, caption)






def init_bot(number, queue_listen, queue_write, group):
    #driver = WhatsAPIDriver(loadstyles=True, profile=prof)
    print("Waiting for QR")
    #driver.wait_for_login()
    print("Bot started")
    
    thread_listen = Thread(target=listen, args=(number, queue_listen, group), name=group+" Listen thread")
    thread_listen.start()

    thread_write = Thread(target=write, args=(number, queue_write, config.groups_id[group]), name=group+" Write thread")
    thread_write.start()
    return thread_listen, thread_write

def quit_bots(listaBots):
    for botDriver in listaBots:
        config.driver[botDriver].quit()
        time.sleep(2)
        config.driver[botDriver] = None

def pc_overloaded():
    cpu_usage = psutil.cpu_percent()
    mem = dict(psutil.virtual_memory()._asdict())
    mem_usage = mem['percent']

    if(mem_usage >= 95):
        return True
    else:
        return False

#main thread que inicia o Bot e responsável por monitorar as threads e reiniciar o bot.
if __name__ == "__main__":
    config.reset = False
    statusThread = {"listen1":True, "listen2":True, "write1":True, "write2":True}
    config.driver["1"] = WhatsAPIDriver(loadstyles=True, profile="/home/bernardo/.mozilla/firefox/pnfzoq43.default")
    thread_listen1, thread_write1 = init_bot("1", queue1, queue2, config.group1)
    contacts = get_all_contacts(config.driver["1"])
    config.driver["2"] = WhatsAPIDriver(loadstyles=True, profile="/home/bernardo/.mozilla/firefox/w9bexwm1.dois")
    thread_listen2, thread_write2 = init_bot("2", queue2, queue1, config.group2)
    
    while True:
        #Verifica se todas as threads não estão realizando nenhum processamento para iniciar o processo de reinicio do bot
        if(True not in statusThread.values()):
            print("===============resetar ===================")

            print("inicindo novos drivers")
            #função que encerra os bots recebendo um parametro com os numeros dos drivers
            quit_bots(["1","2"])
            config.driver["1"] = WhatsAPIDriver(loadstyles=True, profile="/home/bernardo/.mozilla/firefox/pnfzoq43.default")
            #contacts = get_all_contacts(driver["1"])
            config.driver["2"] = WhatsAPIDriver(loadstyles=True, profile="/home/bernardo/.mozilla/firefox/w9bexwm1.dois")
            #fechar drivers e instanciar novos
            time.sleep(5)
            statusThread = {"listen1":True, "listen2":True, "write1":True, "write2":True}
            config.reset = False
        
        now = datetime.datetime.now()
        if(now.hour == 3 and now.minute == 42 and config.reset == False):
            time.sleep(40)         
            config.reset = True
        
        if(pc_overloaded() and config.reset == False):
            print("memoria cheia reiniciar")
            config.reset = True
