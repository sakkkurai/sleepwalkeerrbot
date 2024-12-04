# Creating config file at first launch
import os


def createcfg():
    file_path = "config.py"

    if not os.path.exists(file_path):
        config_content = '''\
TOKEN = ""  # Bot token
CHANNEL_ID = ""  # Id of your channel
MODER_CHAT_ID = ""  # Id of moderator chat
ADMIN_ID =  # Admin's ID
SENIOR_ADMIN =  # Your own ID. Needs for high permissions
    '''

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(config_content)

        print("config.py init succesfully !")
    else:
        print("config.py exists, skipping !")
