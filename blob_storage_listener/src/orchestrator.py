from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage

from common.utils.dispatcher import Dispatcher
from .storage_listener.azure_storage_listener import AzureStorageListener
from .settings import settings

import json

class Orchestrator():
    def __init__(self):
        self.dispatcher = Dispatcher()
        self.azure_storage_listener = AzureStorageListener(dispatcher=self.dispatcher, connection_string=settings.SERVICE_BUS_CONNECTION_STRING, queue_name=settings.QUEUE_NAME)
        self.dispatcher.subscribe(event_name=self.azure_storage_listener.get_result_event_name(), handler=self.handle_storage_event)
    
    async def run(self):
        await self.azure_storage_listener.execute(service_id="azure_storage_service_id")

    async def handle_storage_event(self, event : dict):
        print(f"HANDLE STORAGE IN SERVICE: {event['service_id']} -> {event['file_url']}", flush=True)
        
        async with ServiceBusClient.from_connection_string(settings.SERVICE_BUS_CONNECTION_STRING) as client:
            sender = client.get_queue_sender(settings.AZURE_STORAGE_BLOB_CREATED_QUEUE_NAME)
            async with sender:
                msg = ServiceBusMessage(
                    json.dumps(event),
                    application_properties={
                        "correlation_id": event["id"],
                        "step": "storage_blob_created"
                    })
                await sender.send_messages(msg)
                print(f"Sent to {settings.AZURE_STORAGE_BLOB_CREATED_QUEUE_NAME}: {event}", flush=True)