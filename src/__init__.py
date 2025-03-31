import os
from dotenv import load_dotenv
from yookassa import Configuration


_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_SRC = f'{_ROOT}/src'
DIR_DATA = f'{_ROOT}/data'
DIR_MODEL = f'{_ROOT}/models'
DIR_CONFIG = f'{_ROOT}/configs'
DIR_TESTS = f'{_ROOT}/tests'

# ------------ Настройки конфигурации --------------
load_dotenv()
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")

SHOP_ID = os.getenv("SHOP_ID")
YOOKASSA_API_KEY = os.getenv("YOOKASSA_API_KEY")
Configuration.account_id = SHOP_ID
Configuration.secret_key = YOOKASSA_API_KEY