from common.utils.dispatcher import Dispatcher
from .settings import settings
from .analyzer.azure_event_listener import AzureEventListener

class Orchestrator():
    def __init__(self):
        self.dispatcher = Dispatcher()
        self.azure_storage_listener = AzureEventListener(dispatcher=self.dispatcher, connection_string=settings.SERVICE_BUS_CONNECTION_STRING, event_name=settings.ANALYZE_RECEIPT_QUEUE_NAME)
        self.dispatcher.subscribe(event_name=self.azure_storage_listener.get_result_event_name(), handler=self.handle_analyze_result)
    
    async def run(self):
        await self.azure_storage_listener.execute(service_id="analyze_receipt_service_id")

    async def handle_analyze_result(self, data : dict):
        
        print(f"Handle Receipt Result: {data['event_data']} ({data['meta_data']})", flush=True)