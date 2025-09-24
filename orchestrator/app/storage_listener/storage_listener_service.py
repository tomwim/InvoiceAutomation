from app.base.base_service import BaseService
from azure.servicebus.aio import ServiceBusClient
import json

class StorageListener(BaseService):
    def __init__(self, dispatcher, connection_string : str, queue_name : str):
        super().__init__(dispatcher=dispatcher)
        self._connection_string = connection_string
        self._queue_name = queue_name

    def get_result_event_name(self) -> str:
        return "file_storage_result"

    async def execute(self, service_id):
        await self._listen_for_storage_events(service_id)

    async def _listen_for_storage_events(self, service_id):
        print(f"Started listening on {self._connection_string} and queue {self._queue_name}", flush=True)
        try:
            async with ServiceBusClient.from_connection_string(self._connection_string) as client:
                print("Before receiver...", flush=True)
                receiver = client.get_queue_receiver(queue_name=self._queue_name)
                print("Created receiver...", flush=True)
                async with receiver:
                    async for msg in receiver:
                        print(f"Received: {str(msg)}", flush=True)
                        body_bytes = b"".join([b for b in msg.body])
                        body_str = body_bytes.decode("utf-8")
                        event_data = json.loads(body_str)
                        data = event_data["data"]
                        print(f"Received URL: {str(data['url'])}", flush=True)

                        await self.dispatcher.publish(self.get_result_event_name(), 
                                                {
                                                    "service_id" : service_id,
                                                    "file_url" : str(data["url"])
                                                })
                        # Process your message here
                        await receiver.complete_message(msg)
        except Exception as e:
            print(f"Error connecting to Service Bus: {e}", flush=True)