from contextlib import asynccontextmanager
from uuid import uuid4
from fastapi import FastAPI, HTTPException
from temporalio.client import Client
from dotenv import load_dotenv
import uvicorn
import os 

from activities import AgentParams
from workflow import LangChainWorkflow, LoaderWorkFlow  # Объединены импорты

# Загрузка переменных окружения должна быть в начале
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Используем переменную окружения для адреса Temporal
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    try:
        app.state.temporal_client = await Client.connect(temporal_host)
        yield
    except Exception as e:
        raise RuntimeError(f"Failed to connect to Temporal: {str(e)}")
    finally:
        # Закрываем соединение при завершении
        if hasattr(app.state, 'temporal_client'):
            await app.state.temporal_client.close()

app = FastAPI(lifespan=lifespan)

@app.post("/run_agent")
async def run_agent(payload: dict, agent: str):
    if not hasattr(app.state, 'temporal_client'):
        raise HTTPException(status_code=500, detail="Temporal client not initialized")
    
    client = app.state.temporal_client
    try:
        result = await client.execute_workflow(
            LangChainWorkflow.run,
            AgentParams(payload, agent),
            id=f"langchain-{agent}-{uuid4()}",
            task_queue="langchain-task-queue",
        )
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/store_agent")
async def store_agent(payload: dict, agent: str):  # Исправлено имя функции (было run_agent)
    if not hasattr(app.state, 'temporal_client'):
        raise HTTPException(status_code=500, detail="Temporal client not initialized")
    
    client = app.state.temporal_client
    try:
        result = await client.execute_workflow(
            LoaderWorkFlow.run,
            AgentParams(payload, agent),
            id=f"langchain-loader-{uuid4()}",
            task_queue="langchain-task-queue",
        )
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Порт берем из переменных окружения
    port = int(os.getenv("APP_PORT", 7777))
    uvicorn.run(app, host="0.0.0.0", port=port)