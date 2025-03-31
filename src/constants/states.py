# ------------------------ Глобальные словари ------------------------
user_lang = {}              # user_id -> 'en'/'ru'
user_coins = {}             # user_id -> set(['bitcoin','ethereum'])
user_pages = {}
top_100_cache = []

user_first_time = {}        # user_id -> bool (впервые ли запущен бот)
user_first_interval = {}    # user_id -> bool (впервые ли пользователь ставит интервал)

user_intervals = {}         # user_id -> seconds
user_next_notify = {}       # user_id -> float (timestamp)

# Дополнительные словари для хранения message_id сообщений, которые нужно удалять
temp_coin_msg = {}          # user_id -> message_id (сообщение "Выберите монеты...")
temp_interval_msg = {}      # user_id -> message_id (сообщение "Выберите интервал...")