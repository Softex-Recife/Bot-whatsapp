import logging
from os import path, mkdir
from datetime import date


PROJECT_DIRECTORY = path.dirname(__file__)
LOG_DIRECTORY = path.join(PROJECT_DIRECTORY, "LOG")
LOG_FORMAT = '%(asctime)s - %(message)s'

class Log:

    """
        Folders hierarchy:
            |LOG
            ----|Year
                ----|Month
                    ----|Day.log
        
        Usage:  Logger.error('This will get logged to a file') 
    """
    
    def __init__(self):
        pass

    def __create_file(self, year, month, day):
        if not path.exists(LOG_DIRECTORY):
            mkdir(LOG_DIRECTORY)
        year_folder = path.join(LOG_DIRECTORY, str(year))
        if not path.exists(year_folder):
            mkdir(year_folder)
        month_folder = path.join(year_folder, str(month))
        if not path.exists(month_folder):
            mkdir(month_folder)
        log_file = path.join(month_folder, f"{day}.log")
        if not path.exists(log_file):
            file = open(log_file, "w")
            file.close()
        return log_file
    
    def error(self, error_message):
        today = date.today()
        log_file = self.__create_file(today.year, today.month, today.day)
        logging.basicConfig(format=LOG_FORMAT, filename=log_file)
        logging.error(error_message)

Logger = Log()