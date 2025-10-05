import os

class Settings():
    def __init__(self):
        self.ANALYZE_RECEIPT_QUEUE_NAME = os.getenv("ANALYZE_RECEIPT_QUEUE_NAME")
        self.RECEIPT_ANALYZE_RESULT_QUEUE_NAME = os.getenv("RECEIPT_ANALYZE_RESULT_QUEUE_NAME")
        self.SERVICE_BUS_CONNECTION_STRING = os.getenv("SERVICE_BUS_CONNECTION_STRING")


settings = Settings()