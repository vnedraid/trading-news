from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langchain_gigachat import GigaChat
import os

def book_hotel(hotel_name: str):
    """Book a hotel"""
    return f"Successfully booked a stay at {hotel_name}."

def book_flight(from_airport: str, to_airport: str):
    """Book a flight"""
    return f"Successfully booked a flight from {from_airport} to {to_airport}."

llm = GigaChat(
    credentials=os.getenv("GIGA_KEY"),
    model="GigaChat-2", # GigaChat-2-Pro
    verify_ssl_certs=False,
    streaming=False,
)

# flight_assistant = create_react_agent(
#     model=llm,
#     tools=[book_flight],
#     prompt="You are a flight booking assistant",
#     name="flight_assistant"
# )

# hotel_assistant = create_react_agent(
#     model=llm,
#     tools=[book_hotel],
#     prompt="You are a hotel booking assistant",
#     name="hotel_assistant"
# )

# supervisor = create_supervisor(
#     agents=[flight_assistant, hotel_assistant],
#     model=llm,
#     prompt=(
#         "You manage a hotel booking assistant and a"
#         "flight booking assistant. Assign work to them."
#     )
# ).compile()