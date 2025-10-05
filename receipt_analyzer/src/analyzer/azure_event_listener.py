from azure.servicebus.aio import ServiceBusClient
from common.utils.base_service import BaseService
import json

class AzureEventListener(BaseService):
    def __init__(self, dispatcher, connection_string : str, event_name : str):
        super().__init__(dispatcher=dispatcher)
        self._connection_string = connection_string
        self._event_name = event_name

    async def stop(self):
        if self._service_bus_client:
            await self._service_bus_client.__aexit__(None, None, None)
    
    async def _create_client(self):
        self._service_bus_client = ServiceBusClient.from_connection_string(self._connection_string)

    def get_result_event_name(self) -> str:
        return "receipt_analyzed_result"

    async def execute(self, service_id):
        await self._create_client()
        await self._listen_for_events(service_id)

    async def _listen_for_events(self, service_id):
        receiver = self._service_bus_client.get_queue_receiver(queue_name=self._event_name)
        async with self._service_bus_client:
            async with receiver:
                async for msg in receiver:
                    print(f"Received: {msg})", flush=True)
                    try:
                        event_data, meta_data = await self.read_message(msg)

                        await self.dispatcher.publish(self.get_result_event_name(), 
                                                {
                                                    "event_data" : event_data,
                                                    "meta_data" : meta_data
                                                    
                                                })
                        await receiver.complete_message(msg)
                    except Exception as e:
                        print(f"Error: {e}", flush=True)
                        await receiver.abandon_message(msg)

    async def read_message(self, msg):
        if msg.application_properties:
            print(f"Correlation ID: {msg.application_properties.get(b'correlation_id').decode('utf-8')}", flush=True)
            print(f"Step: {msg.application_properties.get(b'step').decode('utf-8')}", flush=True)
            meta_data = {
                "correlation_id" : msg.application_properties.get(b'correlation_id').decode('utf-8'),
                "step" : msg.application_properties.get(b'step').decode('utf-8'),
            }
        else:
            meta_data = {
                "correlation_id" : "None",
                "step" : "Unknown",
            }
        body_bytes = b"".join(msg.body)
        body_str = body_bytes.decode("utf-8")
        event_data = json.loads(body_str)

        return event_data, meta_data

    # async def _listen_for_storage_events(self, service_id):
    #     try:
    #         async with ServiceBusClient.from_connection_string(self._connection_string) as client:
    #             print(f"Started listening on {self._connection_string} and queue {self._queue_name}", flush=True)
    #             receiver = client.get_queue_receiver(queue_name=self._queue_name)
    #             async with receiver:
    #                 async for msg in receiver:
    #                     body_bytes = b"".join([b for b in msg.body])
    #                     body_str = body_bytes.decode("utf-8")
    #                     event_data = json.loads(body_str)
    #                     data = event_data["data"]
    #                     print(f"Received Azure Storage URL: {str(data['url'])}", flush=True)

    #                     await self.dispatcher.publish(self.get_result_event_name(), 
    #                                             {
    #                                                 "service_id" : service_id,
    #                                                 "id" : event_data["id"],
    #                                                 "type" : event_data["eventType"],
    #                                                 "file_url" : data["url"]
    #                                             })
    #                     # Process your message here
    #                     await receiver.complete_message(msg)
    #     except Exception as e:
    #         print(f"Error connecting to Service Bus: {e}", flush=True)