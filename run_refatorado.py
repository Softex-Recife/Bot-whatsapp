# -*- coding: utf-8 -*-
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