import os

class Settings():
    def __init__(self):
        self.SERVICE_BUS_CONNECTION_STRING = os.getenv("SERVICE_BUS_CONNECTION_STRING")
        self.QUEUE_NAME = os.getenv("QUEUE_NAME")


settings = Settings()