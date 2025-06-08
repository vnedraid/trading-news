from contextlib import asynccontextmanager
from uuid import uuid4
from fastapi import FastAPI, HTTPException
from temporalio.client import Client
from dotenv import load_dotenv
import uvicorn

from activities import AgentParams


load_dotenv()

from workflow import LangChainWorkflow
from workflow import LoaderWorkFlow


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.temporal_client = await Client.connect("localhost:7233")
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/run_agent")
async def run_agent(payload: dict, agent: str):
    client = app.state.temporal_client
    try:
        result = await client.execute_workflow(
            LangChainWorkflow.run,
            AgentParams(payload, agent),
            id=f"langchain-{agent}-{uuid4()}",
            task_queue="langchain-task-queue",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return result

@app.post("/store_agent")
async def run_agent(payload: dict, agent: str):
    client = app.state.temporal_client
    try:
        result = await client.execute_workflow(
            LoaderWorkFlow.run,
            AgentParams(payload, agent),
            id=f"langchain-loader-{uuid4()}",
            task_queue="langchain-task-queue",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return result


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8008)
