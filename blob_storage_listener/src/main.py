from fastapi import FastAPI
from contextlib import asynccontextmanager
from common.utils.dispatcher import Dispatcher
from .orchestrator import Orchestrator
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    orchestrator = Orchestrator()

    task = asyncio.create_task(orchestrator.run())

    print("Blob storage listener lifespan started.", flush=True)

    yield 

    task.cancel()
    print("Blob storage listener lifespan ended.", flush=True)
    try:
        await task
    except asyncio.CancelledError:
        pass

    yield

# Attach lifespan to app
app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {"status": "Storage listener running..."}