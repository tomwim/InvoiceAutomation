from common.utils.dispatcher import Dispatcher
from .settings import settings
from .analyzer.azure_event_listener import AzureEventListener
from .analyzer.receipt_reader import ReceiptReader, AzureCredentials
from .analyzer.receipt import AnalyzedReceipt, remove_confidence
from dataclasses import asdict

is_debug = True
use_example_json = False

class Orchestrator():
    def __init__(self):
        self.dispatcher = Dispatcher()
        self._create_services()
        self._subscribe_to_events()

        if is_debug and use_example_json:
            self.test()


    def _create_services(self):
        self.event_listener = AzureEventListener(dispatcher=self.dispatcher, connection_string=settings.SERVICE_BUS_CONNECTION_STRING, event_name=settings.ANALYZE_RECEIPT_QUEUE_NAME)
        
        self.receipt_reader_service = ReceiptReader(
            dispatcher=self.dispatcher, 
            credentials=AzureCredentials(
                account_name=settings.BLOB_STORAGE_ACCOUNT_NAME,
                container_name=settings.BLOB_STORAGE_CONTAINER_NAME,
                endpoint=settings.AI_RECEIPT_READER_ENDPOINT,
                key=settings.AI_RECEIPT_READER_KEY
            )
        )

    def _subscribe_to_events(self):
        self.dispatcher.subscribe(event_name=self.event_listener.get_result_event_name(), handler=self.handle_analyze_result)
        self.dispatcher.subscribe(event_name=self.receipt_reader_service.get_result_event_name(), handler=self.handle_receipt_read_result)

    async def run(self):
        await self.event_listener.execute(service_id="analyze_receipt_service_id")

    async def handle_analyze_result(self, data : dict):
        print(f"Handle Receipt Result: {data['event_data']} ({data['meta_data']})", flush=True)

        await self.receipt_reader_service.execute(service_id=data['event_data']['file'], file_url=data['event_data']['file'])

    async def handle_receipt_read_result(self, event : dict):
        print(f"{event['service_id']} -> {event['result']}", flush=True)

        document = event['result'].documents[0]
        receipt = AnalyzedReceipt.from_analyzed_document(id="debug", document=document)

        print(f"RECEIPT: {receipt}", flush=True)

        

        print(f"Is debug? {is_debug}", flush=True)
        if is_debug:
            # Convert to a dictionary
            result_dict = event['result'].as_dict()

            

            # Save as JSON
            import json

            print(f"Receipt: {receipt.id} is in {receipt.country.value}")

            receipt_dict = asdict(receipt)
            receipt_dict["time"]["value"] = receipt_dict["time"]["value"].isoformat()
            # receipt_dict["date"]["value"] = receipt_dict["date"]["value"].isoformat()
            receipt_json = json.dumps(receipt_dict, indent=4)

            print(f"Dict: {receipt_dict}", flush=True)
            print(f"Json: {receipt_json}", flush=True)

            with open("sample_result.json", "w") as f:
                json.dump(result_dict, f, indent=2)
            print(f"Written to sample_result.json", flush=True)

    def test(self):
        import json

        with open("sample_result_doc.json", "r") as f:
            data = json.load(f)

        print(f"Loaded: {data}", flush=True)

        receipt = AnalyzedReceipt(**data)

        print(f"Is debug? {is_debug}", flush=True)
        if is_debug:
            # Save as JSON
            import json

            print(f"Receipt: {receipt.id} is in {receipt.country}")

            receipt_dict = asdict(receipt)
            receipt_json = json.dumps(receipt_dict, indent=4)

            print(f"{receipt_json}", flush=True)