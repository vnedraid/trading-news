from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from contextlib import asynccontextmanager
import logging
import uvicorn
import asyncio
from temporalio.client import Client
from uuid import uuid4
from typing import Optional
from pydantic_settings import BaseSettings

from activities import TranslateParams
from workflow import LangChainWorkflow

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Конфигурация через Pydantic


class Settings(BaseSettings):
    # Основные настройки бота
    BOT_TOKEN: str
    WEBHOOK_URL: Optional[str] = None
    USE_WEBHOOK: bool = False
    WEB_SERVER_HOST: str = "127.0.0.1"
    WEB_SERVER_PORT: int = 8487
    TEMPORAL_HOST: str = "localhost:7233"
    TEMPORAL_TASK_QUEUE: str = "langchain-task-queue"

    # Дополнительные настройки из вашего .env
    GIGA_KEY: Optional[str] = None
    LANGFUSE_URL: Optional[str] = None
    LANGFUSE_PK: Optional[str] = None
    LANGFUSE_SK: Optional[str] = None
    MILVUS_URI: Optional[str] = None
    EMBEDDINGS_MODEL: Optional[str] = None
    USER_AGENT: Optional[str] = None
    PGVECTOR_URI: Optional[str] = None
    PG_NAME: Optional[str] = None
    PG_USER: Optional[str] = None
    PG_PASS: Optional[str] = None
    PG_HOST: Optional[str] = None
    PG_PORT: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Это разрешит дополнительные переменные без ошибок


# Загрузка конфигурации
try:
    settings = Settings()
except Exception as e:
    logger.error(f"Ошибка загрузки конфигурации: {e}")
    raise

# Инициализация бота и диспетчера
bot = Bot(token=settings.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def get_temporal_client() -> Client:
    """Создает и возвращает клиент Temporal."""
    return await Client.connect(settings.TEMPORAL_HOST)


async def execute_translation_workflow(phrase: str, language: str = "ru") -> str:
    """Выполняет workflow перевода через Temporal."""
    try:
        client = await get_temporal_client()
        result = await client.execute_workflow(
            LangChainWorkflow.run,
            TranslateParams(phrase, language),
            id=f"langchain-translation-{uuid4()}",
            task_queue=settings.TEMPORAL_TASK_QUEUE,
        )
        return result.get("content", "")
    except Exception as e:
        logger.error(f"Ошибка выполнения workflow: {e}")
        raise


@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Обработчик команды /start."""
    try:
        if not message.text or len(message.text.split()) < 2:
            await message.answer(
                "Пожалуйста, введите текст для перевода после команды /start"
            )
            return

        phrase = " ".join(message.text.split()[1:])
        translation = await execute_translation_workflow(phrase)
        await message.answer(translation)
    except Exception as e:
        logger.error(f"Ошибка обработки команды /start: {e}")
        await message.answer("Произошла ошибка при обработке запроса")


async def setup_webhook():
    """Настройка вебхука при запуске."""
    if settings.USE_WEBHOOK:
        if not settings.WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL не указан в конфигурации")

        webhook_info = await bot.get_webhook_info()
        logger.info(f"Текущая информация о вебхуке: {webhook_info}")

        await bot.set_webhook(
            url=settings.WEBHOOK_URL,
            drop_pending_updates=True,
            allowed_updates=dp.resolve_used_update_types(),
        )
        logger.info(f"Вебхук установлен на {settings.WEBHOOK_URL}")


async def remove_webhook():
    """Удаление вебхука при завершении."""
    if settings.USE_WEBHOOK:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Вебхук удалён")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    try:
        await setup_webhook()
        yield
    finally:
        await remove_webhook()


app = FastAPI(
    lifespan=lifespan,
    title="Telegram Bot API",
    description="API для Telegram бота с интеграцией Temporal",
    version="1.0.0",
)


@app.post("/webhook")
async def bot_webhook(request: Request):
    """Обработчик вебхука для Telegram бота."""
    if not settings.USE_WEBHOOK:
        raise HTTPException(status_code=400, detail="Webhook mode is disabled")

    try:
        update_data = await request.json()
        logger.debug(f"Получено обновление: {update_data}")
        update = types.Update(**update_data)
        await dp.feed_update(bot, update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
        raise HTTPException(status_code=400, detail="Invalid update data")


async def start_polling():
    """Запуск бота в режиме поллинга."""
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Запуск бота в режиме поллинга...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        if settings.USE_WEBHOOK:
            uvicorn.run(
                app,
                host=settings.WEB_SERVER_HOST,
                port=settings.WEB_SERVER_PORT,
                log_level="info",
                reload=False,
            )
        else:
            asyncio.run(start_polling())
    except Exception as e:
        logger.critical(f"Фатальная ошибка: {e}")
        raise
