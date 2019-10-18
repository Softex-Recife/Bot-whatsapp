from os import path, mkdir
from queue import Queue

QUEUE_DIR = path.join(path.dirname(__file__), "queue")
LINE_SEPARATOR = "#$#$#\n"

queues = [
    "queue1-listen.csv",
    "queue1-write.csv",
    "queue2-listen.csv",
    "queue2-write.csv"
]

def create_message(msg_type, file_path, formatted_text):
    return f"{msg_type}###{file_path}###{formatted_text}#$#$#\n"

def check_files():
    if not path.exists(QUEUE_DIR):
        print("Creating directory queue")
        mkdir(QUEUE_DIR)
    for file_name in queues:
        if not path.exists(path.join(QUEUE_DIR, file_name)):
            print(f"Creating file for queue {file_name}")
            f = open(path.join(QUEUE_DIR, file_name), "w")
            f.close()

def write_on_backup_file(queue, mode, msg_type, file_path, formatted_text):
    queue_file = f"{queue}-{mode}.csv"
    with open(path.join(QUEUE_DIR, queue_file), "a+") as queue_file_content:
        message = create_message(msg_type, file_path, formatted_text)
        queue_file_content.write(message)

def get_file_text(file):
    text = open(file, "r").read()
    text_list = text.split(LINE_SEPARATOR)
    return text_list

def get_not_sent_messages(listen_queue, write_queue):
    listen_text_list = get_file_text(path.join(QUEUE_DIR, listen_queue))[:-1]
    write_text_list = get_file_text(path.join(QUEUE_DIR, write_queue))[:-1]
    diff = len(listen_text_list) - len(write_text_list)
    not_sent_messages = []
    if diff > 0:
        not_sent_messages = listen_text_list[-diff:]
    return not_sent_messages
        
def load_offline_messages():
    messages = []
    for i in [0,2]:
        listen_queue = queues[i]
        write_queue = queues[i+1]
        not_sent = get_not_sent_messages(listen_queue, write_queue)
        messages.append(not_sent)
    queue1 = list_to_queue(messages[0])
    queue2 = list_to_queue(messages[1])
    return queue1, queue2

def list_to_queue(full_list):
    queue = Queue()
    for list_item in full_list:
        element = tuple(list_item.split("###"))
        queue.put(element)
    return queue
