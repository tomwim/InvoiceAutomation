from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.base.dispatcher import Dispatcher
from app.orchestrator.service_orchestrator import ServiceOrchestrator

import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    dispatcher = Dispatcher()
    orchestrator = ServiceOrchestrator(dispatcher)
    task = asyncio.create_task(orchestrator.run_pipeline())

    print("Application lifespan started.", flush=True)

    yield 

    task.cancel()
    asyncio.create_task(orchestrator.stop())
    print("Application lifespan ended.", flush=True)
    try:
        await task
    except asyncio.CancelledError:
        pass

# Attach lifespan to app
app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {"status": "orchestrator running..."}