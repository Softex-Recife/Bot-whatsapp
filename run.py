import os
import sys
import time
from queue import Queue
from threading import Thread
import re


from webwhatsapi import WhatsAPIDriver
from webwhatsapi.objects.message import MediaMessage, Message

groups = {
    "Python-Softex 1": 1,
    "Python-Softex 2": 2,
    "grupo1": 1,
    "grupo2": 2,
    "grupo3": 3,
    "Softex Fórum 🚀": "🚀",
    "Softex Fórum 🛸": "🛸"
}

groups_id = {
    "grupo1": '558196335770-1557432053@g.us',
    "grupo2": '558196335770-1557432066@g.us',
    "grupo3": "558196335770-1559066845@g.us",
    "Python-Softex 1": "558196335770-1556222998@g.us",
    "Python-Softex 2": "558196335770-1556566150@g.us",
    "Softex Fórum 🚀": "558198521133-1446582835@g.us",
    "Softex Fórum 🛸": "558196335770-1556222998@g.us"
}

queue1 = Queue()
queue2 = Queue()

queue_dict = {
    queue1 : "queue1",
    queue2 : "queue2"
}
with open("queue1-listen.csv", "r") as queue1_listen:
    len_queue1_listen = len(queue1_listen.readlines())
with open("queue1-write.csv", "r") as queue1_write:
    len_queue1_write = len(queue1_write.readlines())
with open("queue2-listen.csv", "r") as queue2_listen:
    len_queue2_listen = len(queue2_listen.readlines())
with open("queue2-write.csv", "r") as queue2_write:
    len_queue2_write = len(queue2_write.readlines())

diff_queue1 = len_queue1_listen - len_queue1_write
if diff_queue1 > 0:
    with open("queue1-listen.csv", "r") as queue1_listen:
        lines = queue1_listen.readlines()
        for i in range(diff_queue1):
            msg_type, path, caption = lines[len_queue1_write+i].split("###")
            queue1.put((msg_type, path, caption))
diff_queue2 = len_queue2_listen - len_queue2_write
if diff_queue2 > 0:
    with open("queue2-listen.csv", "r") as queue2_listen:
        lines = queue2_listen.readlines()
        for i in range(diff_queue2):
            msg_type, path, caption = lines[len_queue2_write+i].split("###")
            queue1.put((msg_type, path, caption))


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


def listen(driver, queue, group):
    while True:
        contacts = driver.get_unread()
        contact = select_contact(contacts, group)
        if contact:
            for message in contact.messages:
                msg_type = message.type
                sender = message.sender.name
                group_number = groups[group]
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
                    queue_file_content.write(f"{msg_type}###{file_path}###{formatted_text}\n")
                print(f"Listened: {msg_type}-{file_path}-{formatted_text}")


def write(driver, queue, group_id):
    while True:
        if not queue.empty():
            msg_type, path, caption = queue.get()
            print(f"Removed from queue: {msg_type}-{path}-{caption}")
            contact = driver.get_contact_from_id(group_id)
            if msg_type == "chat":
                send_message(contact, caption)
            elif msg_type in ['document', 'image' ,'video', 'ptt', 'audio']:           
                chat_id = contact.get_chat().id
                print(f"write in path: {path}")
                if msg_type in ['document', 'ptt', 'audio']:
                    send_media(driver, path, chat_id, "")
                    time.sleep(1)
                    contact.get_chat().send_message(caption)
                else:
                    send_media(driver, path, chat_id, caption)
                os.remove(path)
                print(f"Deleted: {path}")
            elif msg_type == "sticker":
                pass
            print(f"Writed: {msg_type}-{path}-{caption}")
            queue_file = queue_dict[queue] + "-write.csv"
            with open(queue_file, "a+") as queue_file_content:
                queue_file_content.write(f"{msg_type}###{path}###{caption}\n")

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



# group1 = "Python-Softex 1"
# group2 = "Python-Softex 2"

group1 = "grupo2"
group2 = "grupo3"

# group1 = "Softex Fórum 🚀"
# group2 = "Softex Fórum 🛸"


def init_bot(queue_listen, queue_write, group):
    driver = WhatsAPIDriver(loadstyles=True)
    print("Waiting for QR")
    driver.wait_for_login()
    print("Bot started")
    
    thread_listen = Thread(target=listen, args=(driver, queue_listen, group), name=group+" Listen thread")
    thread_listen.start()

    thread_write = Thread(target=write, args=(driver, queue_write, groups_id[group]), name=group+" Write thread")
    thread_write.start()
    return driver, thread_listen, thread_write

    
if __name__ == "__main__":
    driver1, thread_listen1, thread_write1 = init_bot(queue1, queue2, group1)
    contacts = get_all_contacts(driver1)
    driver2, thread_listen2, thread_write2 = init_bot(queue2, queue1, group2)
    while True:
        time.sleep(1)