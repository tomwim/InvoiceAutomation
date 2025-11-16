from app.storage_listener.storage_listener_service import StorageListener
# from receipt_analyzer.src.analyzer.receipt_reader import ReceiptReader, AzureCredentials
from app.base.dispatcher import Dispatcher
from app.settings import settings

from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage

import asyncio
import json

# from azure.ai.documentintelligence.models import AnalyzeResult

is_debug = False

class ServiceOrchestrator():
    def __init__(self, dispatcher : Dispatcher):
        self.dispatcher = dispatcher
        self.queues = {
            settings.AZURE_STORAGE_BLOB_CREATED_QUEUE_NAME : self.handle_azure_storage_blob_created,
            # settings.ANALYZE_RECEIPT_QUEUE_NAME : self.handle_receipt,
        }

        if is_debug:
            self._debug()

    async def run_pipeline(self):
        await self._create_client()
        await self._subscribe_to_queues()

    async def stop(self):
        if self._service_bus_client:
            await self._service_bus_client.__aexit__(None, None, None)

    async def _create_client(self):
        self._service_bus_client = ServiceBusClient.from_connection_string(settings.SERVICE_BUS_CONNECTION_STRING)

    async def _subscribe_to_queues(self):
        # async with ServiceBusClient.from_connection_string(settings.SERVICE_BUS_CONNECTION_STRING) as client:
        async with self._service_bus_client:
            tasks = [self._receive_from_queue(self._service_bus_client, q) for q in self.queues.keys()]
            print(f"TASKS FOR QUEUES {self.queues}", flush=True)
            await asyncio.gather(*tasks)

    async def _receive_from_queue(self, client, queue_name):
        receiver = client.get_queue_receiver(queue_name)
        async with receiver:
            async for msg in receiver:
                print(f"Received from {queue_name}: {msg})", flush=True)
                try:
                    event_data, meta_data = await self.read_message(msg)
                    await receiver.complete_message(msg)
                    await self.queues[queue_name](data=event_data, meta_data=meta_data)
                except Exception as e:
                    print(f"[{queue_name}] Error: {e}", flush=True)
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

    async def _send_message(self, queue_name, data : dict, application_properties : dict):
        sender = self._service_bus_client.get_queue_sender(queue_name=queue_name)
        async with sender:
            msg = ServiceBusMessage(
                json.dumps(data),
                application_properties=application_properties
            )
            await sender.send_messages(msg)
            await sender.__aexit__()

    async def handle_azure_storage_blob_created(self, data : dict, meta_data : dict):
        print(f"Handle Blob Created: {data['id']} and {data['file_url']}", flush=True)
        receipt = {
            "id" : data['id'],
            "file" : data['file_url']
        }
        meta_data["step"] = "analyze_document_requested"
        await self._send_message(queue_name=settings.ANALYZE_RECEIPT_QUEUE_NAME, data=receipt, application_properties=meta_data)

    async def handle_receipt(self, data : dict, meta_data : dict):
        print(f"Handle Receipt: {data['id']} and {data['file']} ({meta_data['correlation_id']})", flush=True)


    # OLD
    def _create_services(self):
        self.storage_listener_service = StorageListener(dispatcher=self.dispatcher, connection_string=settings.SERVICE_BUS_CONNECTION_STRING, queue_name=settings.QUEUE_NAME)
        self.receipt_reader_service = ReceiptReader(
            dispatcher=self.dispatcher,
            credentials=AzureCredentials(
                account_name=settings.BLOB_STORAGE_ACCOUNT_NAME,
                container_name=settings.BLOB_STORAGE_CONTAINER_NAME,
                endpoint=settings.AI_RECEIPT_READER_ENDPOINT,
                key=settings.AI_RECEIPT_READER_KEY
            )
        )

    def _subscribe_to_services(self):
        self.dispatcher.subscribe(event_name=self.storage_listener_service.get_result_event_name(), handler=self.handle_storage_event)
        self.dispatcher.subscribe(event_name=self.receipt_reader_service.get_result_event_name(), handler=self.handle_receipt_read_event)

    async def handle_storage_event(self, event : dict):
        print(f"{event['service_id']} -> {event['file_url']}", flush=True)
        await self.receipt_reader_service.execute(service_id=event['file_url'], file_url=event['file_url'])

    async def handle_receipt_read_event(self, event : dict):
        print(f"{event['service_id']} -> {event['result']}", flush=True)

        document = event['result'][0]
        receipt = AnalyzedReceipt.from_analyzed_document(id="debug", document=document)

        if is_debug:
            # Convert to a dictionary
            result_dict = event['result'].as_dict()

            # Save as JSON
            import json
            with open("sample_result.json", "w") as f:
                json.dump(result_dict, f, indent=2)

    def _debug(self):
        import json
        with open("sample_result.json") as f:
            data = json.load(f)

        unsupported = ["apiVersion", "modelId", "stringIndexType", "contentFormat"]
        for key in unsupported:
            data.pop(key, None)

        result_obj = AnalyzeResult(**data)  # reconstructs a real object

        for document in result_obj.documents:
            for field_name, field in document.fields.items():
                print(f"{field_name} -> {field}", flush=True)

            receipt = AnalyzedReceipt.from_analyzed_document(id="debug", document=document)
            print(f"CTR: {receipt.country.value} -> {receipt.country.confidence}")