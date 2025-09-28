from azure.servicebus.aio import ServiceBusClient
from common.utils.base_service import BaseService
import json

class AzureStorageListener(BaseService):
    def __init__(self, dispatcher, connection_string : str, queue_name : str):
        super().__init__(dispatcher=dispatcher)
        self._connection_string = connection_string
        self._queue_name = queue_name

    def get_result_event_name(self) -> str:
        return "azure_file_storage_result"

    async def execute(self, service_id):
        await self._listen_for_storage_events(service_id)

    async def _listen_for_storage_events(self, service_id):
        try:
            async with ServiceBusClient.from_connection_string(self._connection_string) as client:
                print(f"Started listening on {self._connection_string} and queue {self._queue_name}", flush=True)
                receiver = client.get_queue_receiver(queue_name=self._queue_name)
                async with receiver:
                    async for msg in receiver:
                        body_bytes = b"".join([b for b in msg.body])
                        body_str = body_bytes.decode("utf-8")
                        event_data = json.loads(body_str)
                        data = event_data["data"]
                        print(f"Received Azure Storage URL: {str(data['url'])}", flush=True)

                        await self.dispatcher.publish(self.get_result_event_name(), 
                                                {
                                                    "service_id" : service_id,
                                                    "id" : event_data["id"],
                                                    "type" : event_data["eventType"],
                                                    "file_url" : data["url"]
                                                })
                        # Process your message here
                        await receiver.complete_message(msg)
        except Exception as e:
            print(f"Error connecting to Service Bus: {e}", flush=True)