from environs import Env

env = Env()
env.read_env()
BOT_TOKEN = env.str('BOT_TOKEN')
DB_URL = env.str('DB_URL')
SYNC_DB_URL = env.str('SYNC_DB_URL')
ADMINS = env.list('ADMINS')
PRIVATE_CHANNEL = env.str('PRIVATE_CHANNEL')
API_KEY = env.str('API_KEY')
GOOGLE_API_KEY = env.str('GOOGLE_API_KEY')
PAYME_TOKEN = env.str('PAYME_TOKEN')
CLICK_TOKEN = env.str('CLICK_TOKEN')
