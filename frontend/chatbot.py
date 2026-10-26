import os
import logging
import asyncio
import time
import aiohttp
import gradio as gr
from openai import AzureOpenAI

# Rooms 100 to 109 are preloaded by the sensor API
DEFAULT_ROOM_ID = "101"


def parse_message(message: str) -> tuple[str, str]:
    """Split "<room id> <question>" into the room ID and the question.

    A one-word message is a question about the default room.
    """
    parts = message.split(maxsplit=1)
    if len(parts) == 2:
        return parts[0], parts[1].strip()
    return DEFAULT_ROOM_ID, message.strip()


def message_text(message) -> str:
    """Join the text blocks of an Assistants API message"""
    return "\n".join(
        block.text.value for block in message.content if block.type == "text"
    )


class HotelAssistant:
    def __init__(self):
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger("HotelAssistant")

        # Initialize Azure OpenAI Client
        try:
            self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            self.api_key = os.getenv("AZURE_OPENAI_KEY")
            self.assistant_id = os.getenv("AZURE_ASSISTANT_ID")
            self.client = AzureOpenAI(
                azure_endpoint=self.azure_endpoint,
                api_key=self.api_key,
                api_version="2024-05-01-preview",
            )
            self.logger.info("Successfully connected to Azure OpenAI.")
        except Exception as e:
            self.logger.error(f"Failed to connect to Azure OpenAI: {e}")

        # Backend API URL
        self.backend_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")

    async def get_room_data(self, room_id: str):
        """Fetch room data from backend API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.backend_url}/rooms/{room_id}/data"
                ) as response:
                    data = await response.json()
                    self.logger.info(f"Fetched room data: {data}")
                    return data
        except Exception as e:
            self.logger.error(f"Error fetching room data: {e}")
            return {"error": "Unable to fetch room data"}

    async def send_room_control(self, room_id: str, command: dict):
        """Send control command to room"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/rooms/{room_id}/control", json=command
                ) as response:
                    result = await response.json()
                    self.logger.info(f"Sent room control command: {result}")
                    return result
        except Exception as e:
            self.logger.error(f"Error sending room control: {e}")
            return {"error": "Unable to send control command"}

    def generate_llm_response(self, user_input: str, room_data: dict):
        """Generate intelligent response using Azure OpenAI"""
        try:
            # Create a conversation thread
            thread = self.client.beta.threads.create()
            self.logger.info(f"Created thread: {thread.id}")

            # Add user message to the thread
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"Room data: {room_data}\nUser request: {user_input}",
            )

            # Run the conversation
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id, assistant_id=self.assistant_id
            )
            self.logger.info(f"Started run: {run.id}")

            # Wait for completion
            while run.status in ["queued", "in_progress", "cancelling"]:
                time.sleep(1)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id, run_id=run.id
                )

            if run.status == "completed":
                messages = self.client.beta.threads.messages.list(thread_id=thread.id)
                for message in messages.data:
                    if message.role == "assistant":
                        return message_text(message)
            elif run.status == "requires_action":
                return "The assistant requires further input."
            else:
                return "The assistant encountered an error."

        except Exception as e:
            self.logger.error(f"Error in Azure OpenAI interaction: {e}")
            return f"An error occurred: {e}"

    def chat_interface(self, message, history):
        """Main chat interface handler"""
        try:
            # The room ID is the first word of the message
            room_id, user_request = parse_message(message)

            # Fetch room data
            room_data = asyncio.run(self.get_room_data(room_id))
            self.logger.info(f"Room data fetched: {room_data}")

            # Generate response
            response = self.generate_llm_response(user_request, room_data)
            self.logger.info(f"Generated response: {response}")

            return response
        except Exception as e:
            self.logger.error(f"Error in chat interface: {e}")
            return f"An error occurred: {str(e)}"

    def launch_interface(self):
        """Launch Gradio interface"""
        iface = gr.ChatInterface(
            self.chat_interface,
            title="Hotel Room Assistant",
            description="Chat with your smart hotel room",
        )
        iface.launch(server_name="0.0.0.0", server_port=7860)


def main():
    assistant = HotelAssistant()
    assistant.launch_interface()


if __name__ == "__main__":
    main()
