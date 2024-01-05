import logging


# Создаем объект логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Создаем форматтер
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# Создаем обработчик для вывода в файл
file_handler = logging.FileHandler("logfile.log", mode='w')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Создаем обработчик для вывода в консоль
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Добавляем обработчики к логгеру
logger.addHandler(file_handler)
logger.addHandler(console_handler)
