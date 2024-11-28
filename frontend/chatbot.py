from openai import AzureOpenAI
import os
import logging
import asyncio
import aiohttp
import gradio as gr

class HotelAssistant:
    def __init__(self):
        # Configure logging
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('HotelAssistant')

        # Initialize Azure OpenAI Client
        try:
            self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            self.api_key = os.getenv("AZURE_OPENAI_KEY")
            self.assistant_id = os.getenv("AZURE_ASSISTANT_ID", "asst_7y4J1Znzk3Agv6zvFTCEhj1Q")
            self.client = AzureOpenAI(
                azure_endpoint=self.azure_endpoint,
                api_key=self.api_key,
                api_version="2024-05-01-preview"
            )
            self.logger.info("Successfully connected to Azure OpenAI.")
        except Exception as e:
            self.logger.error(f"Failed to connect to Azure OpenAI: {e}")
        
        # Backend API URL
        self.backend_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")

    async def get_room_data(self, room_id: str):
        """Fetch room data from backend API"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.backend_url}/rooms/{room_id}/data") as response:
                return await response.json()

    async def send_room_control(self, room_id: str, command: dict):
        """Send control command to room"""
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.backend_url}/rooms/{room_id}/control", json=command) as response:
                return await response.json()

    def generate_llm_response(self, user_input: str, room_data: dict):
        """Generate intelligent response using Azure OpenAI"""
        try:
            # Create a thread for conversation
            thread = self.client.beta.threads.create()

            # Add user input to the thread
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"Room data: {room_data}\nUser request: {user_input}"
            )

            # Run the assistant
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )

            # Wait for the completion
            while run.status in ["queued", "in_progress", "cancelling"]:
                asyncio.sleep(1)
                run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

            if run.status == "completed":
                messages = self.client.beta.threads.messages.list(thread_id=thread.id)
                for message in messages.data:
                    if message.role == "assistant":
                        return message.content
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
            # Assume room ID is first part of message
            parts = message.split(maxsplit=2)
            room_id = parts[0] if len(parts) > 1 else 'room101'
            user_request = parts[-1]

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
            description="Chat with your smart hotel room"
        )
        iface.launch(server_name="0.0.0.0", server_port=7860)

def main():
    assistant = HotelAssistant()
    assistant.launch_interface()

if __name__ == "__main__":
    main()
