from app.storage_listener.storage_listener_service import StorageListener
from app.base.dispatcher import Dispatcher
from app.settings import settings

class ServiceOrchestrator():
    def __init__(self, dispatcher : Dispatcher):
        self.dispatcher = dispatcher
        self._create_services()
        self._subscribe_to_services()

    async def run_pipeline(self):
        await self.storage_listener_service.execute(service_id="storage_service_id")

    def _create_services(self):
        self.storage_listener_service = StorageListener(dispatcher=self.dispatcher, connection_string=settings.SERVICE_BUS_CONNECTION_STRING, queue_name=settings.QUEUE_NAME)

    def _subscribe_to_services(self):
        self.dispatcher.subscribe(event_name=self.storage_listener_service.get_result_event_name(), handler=self.handle_storage_event)

    async def handle_storage_event(self, event : dict):
        print(f"{event['service_id']} -> {event['file_url']}", flush=True)