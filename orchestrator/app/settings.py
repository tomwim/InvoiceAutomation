import os

class Settings():
    def __init__(self):
        self.SERVICE_BUS_CONNECTION_STRING = os.getenv("SERVICE_BUS_CONNECTION_STRING")

        self.QUEUE_NAME = os.getenv("QUEUE_NAME")
        self.AZURE_STORAGE_BLOB_CREATED_QUEUE_NAME = os.getenv("AZURE_STORAGE_BLOB_CREATED_QUEUE_NAME")
        self.ANALYZE_RECEIPT_QUEUE_NAME = os.getenv("ANALYZE_RECEIPT_QUEUE_NAME")


        self.BLOB_STORAGE_ACCOUNT_NAME = os.getenv("BLOB_STORAGE_ACCOUNT_NAME")
        self.BLOB_STORAGE_CONTAINER_NAME = os.getenv("BLOB_STORAGE_CONTAINER_NAME")

        self.AI_RECEIPT_READER_ENDPOINT = os.getenv("AI_RECEIPT_READER_ENDPOINT")
        self.AI_RECEIPT_READER_KEY = os.getenv("AI_RECEIPT_READER_KEY")


settings = Settings()