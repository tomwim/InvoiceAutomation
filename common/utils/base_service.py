from .dispatcher import Dispatcher

class BaseService:
    def __init__(self, dispatcher: Dispatcher):
        self.dispatcher = dispatcher
        self._is_running = False

    async def run(self, service_id: str):
        self._is_running = True
        print(f"Running [{self.__class__.__name__}]", flush=True)
        await self._execute(service_id)

    async def _execute(self, service_id: str):
        raise NotImplementedError
    
    def get_result_event_name(self) -> str:
        raise NotImplementedError