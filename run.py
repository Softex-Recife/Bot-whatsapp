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
from offline import write_on_backup_file, check_files, load_offline_messages


from WebWhatsapp.webwhatsapi import WhatsAPIDriver
from WebWhatsapp.webwhatsapi.objects.message import MediaMessage, Message

check_files()

queue1, queue2 = load_offline_messages()

queue_dict = {
    queue1 : "queue1",
    queue2 : "queue2"
}


def get_all_contacts(driver):
    """
    Returns a dictionary, formatted as {'558198543685': 'Name'} of all contacts

    Params
        driver {Driver} : webwhatsapi driver object

    Eg: 
    """
    wrapper_contact_list = driver.get_my_contacts()
    contacts = {}
    for wrapper_contact in wrapper_contact_list:
        json = wrapper_contact._js_obj
        contact_number = json['id']['user']
        contact_name = json['formattedName']
        contacts[contact_number] = contact_name
    return contacts

def replace_number_to_contact(text, contacts):
    """
    Changes numbers in text to contact name\n

    Params
        text     {String}                       : message text
        contacts {Dict('558198543685': 'Name')} : contacts dictionary (returns of get_all_contacts() method)

    Eg:     'Message example to @558198543685'
    Return: 'Message example to @Name'
    """
    mentions = re.findall(r"\d{12}", text)
    for mention in mentions:
        if mention in contacts.keys():
            contactName = contacts[mention]
            text = text.replace(mention, contactName)
        else:
            print(f"Contact not found, number {mention}")
    return text

def select_contact(unread_messages, chat_name):
    """
    Change to a single filter
    """
    for message in unread_messages:
        if chat_name == message.chat.name:
            return message
    return False


directory_path = os.path.normpath(os.getcwd())
temp_folder = os.path.normpath(directory_path + os.sep + "temp")

def text_formatting(group_number, sender, text):
    text = replace_number_to_contact(text, contacts)
    return f'[{group_number}] *_{sender}_*: {text}'

def save_media(message):
    file_name = message.filename
    file_path = temp_folder + os.sep + file_name
    message.save_media(temp_folder, force_download=True)
    return file_path


def listen(driverNumber, queue, group):
    #time.sleep(40)
    while True:
        if (config.reset == True):
            statusThread["listen"+driverNumber] = False
            while(config.reset==True):
                time.sleep(1)
            statusThread["listen"+driverNumber] = True
  
        try:
            unread_messages = config.driver[driverNumber].get_unread(use_unread_count=True)
        except TypeError as identifier:
            print()
            print(f"Erro ao carregar as mensagens não lida {identifier}, sem internet")
            continue
        message_group = list(filter(lambda message: message.chat.name == group, unread_messages))
        if message_group:
            message_group = message_group[0]
            for message in message_group.messages:
                msg_type = message.type
                sender = message.sender.name
                group_number =config.groups[group]
                chat_id = message.chat_id
                text = ""
                file_path = "no path"
                if msg_type in ['document', 'image' ,'video', 'ptt', 'audio']:
                    if msg_type in ['image' ,'video']:
                        text = message.caption
                    file_path = save_media(message)
                    print("SAAALVEEEI")
                    formatted_text = text_formatting(group_number, sender, text)
                    queue.put((msg_type, file_path, formatted_text))
                    # print(msg_type)
                elif msg_type == "chat":
                    text = message.content
                    formatted_text = text_formatting(group_number, sender, text)
                    if(text == "reset"):
                        config.reset = True
                    # print(f'[{group_number}] *_{sender}_*: {text}')
                    queue.put((msg_type, file_path, formatted_text))
                config.driver[driverNumber].chat_send_seen(chat_id)
                write_on_backup_file(queue_dict[queue], "write", msg_type, file_path, formatted_text)
                print(f"Listened: {msg_type}-{file_path}-{formatted_text}")


def write(driverNumber, queue, group_id):
    #time.sleep(40)
    while True:
        #print("write thread live")
        if (config.reset == True):
            statusThread["write"+driverNumber] = False
            while(config.reset==True):
                time.sleep(1)
            statusThread["write"+driverNumber] = True
                #print(f"thread write{driverNumber} parada")
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
                    send_media(config.driver[driverNumber], path, chat_id, "", contact)
                    time.sleep(1)
                    contact.get_chat().send_message(caption)
                else:
                    send_media(config.driver[driverNumber], path, chat_id, caption, contact)
                os.remove(path)
                print(f"Deleted: {path}")
            elif msg_type == "sticker":
                pass
            write_on_backup_file(queue_dict[queue], "write", msg_type, path, caption)
            print(f"Writed: {msg_type}-{path}-{caption}")

def send_message(contact, message):
    error_counter = 0
    try:
        contact.get_chat().send_message(message)
    except Exception as e:
        print(f"[{error_counter}] Error trying to send message - {e}")
        error_counter += 1
        time.sleep(5)
        send_message(contact, message)

def send_media(driver, path, chat_id, caption, contact):
    error_counter = 0
    try:
        driver.send_media(path, chat_id, caption)
    except Exception as e:
        print(f"[{error_counter}] Error trying to send media -")
        with open("test.txt", "a") as myfile:
            myfile.write(str(e) + "\n")
        error_counter += 1
        send_message(contact, f"Não foi possível enviar a media do {chat_id}" )
        send_media(driver, path, chat_id, caption,contact)






def init_threads(number, queue_listen, queue_write, group):
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
    config.driver["1"] = WhatsAPIDriver(loadstyles=True, profile=config.profile1)
    config.driver["2"] = WhatsAPIDriver(loadstyles=True, profile=config.profile2)
    time.sleep(20)
    config.reset = False
    statusThread = {"listen1":True, "listen2":True, "write1":True, "write2":True}
    contacts = get_all_contacts(config.driver["1"])
    thread_listen1, thread_write1 = init_threads("1", queue1, queue2, config.group1)
    thread_listen2, thread_write2 = init_threads("2", queue2, queue1, config.group2)
    
    while True:
        if(True not in statusThread.values()):
            print("===============resetar ===================")

            print("inicindo novos drivers")
            #função que encerra os bots recebendo um parametro com os numeros dos drivers
            quit_bots(["1","2"])
            config.driver["1"] = WhatsAPIDriver(loadstyles=True, profile=config.profile1)
            config.driver["2"] = WhatsAPIDriver(loadstyles=True, profile=config.profile2)
            time.sleep(20)
            #statusThread = {"listen1":True, "listen2":True, "write1":True, "write2":True}
            config.reset = False
            
            #contacts = get_all_contacts(driver["1"])
            #fechar drivers e instanciar novos
        
        now = datetime.datetime.now()
        if(now.hour == 16 and now.minute == 45 and config.reset == False):
            time.sleep(40)         
            config.reset = True
        
        if(pc_overloaded() and config.reset == False):
            print("memoria cheia reiniciar")
            config.reset = True
