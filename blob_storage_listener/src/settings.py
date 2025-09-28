import os

class Settings():
    def __init__(self):
        self.SERVICE_BUS_CONNECTION_STRING = os.getenv("SERVICE_BUS_CONNECTION_STRING")
        self.QUEUE_NAME = os.getenv("QUEUE_NAME")
        self.AZURE_STORAGE_BLOB_CREATED_QUEUE_NAME = os.getenv("AZURE_STORAGE_BLOB_CREATED_QUEUE_NAME")

settings = Settings()