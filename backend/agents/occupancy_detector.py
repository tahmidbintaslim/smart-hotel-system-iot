import asyncio
import json
import logging
from typing import Dict, Any
from confluent_kafka import Consumer, Producer
import aiohttp

class OccupancyDetectorAgent:
    def __init__(self, 
                 kafka_broker: str, 
                 iot_api_url: str,
                 topics: list[str] = ['life-being'],
                 control_topic: str = 'room-control'):
        """
        Initialize Occupancy Detector Agent
        
        :param kafka_broker: Kafka broker address
        :param iot_api_url: Base URL for IoT device control API
        :param topics: Kafka topics to consume
        :param control_topic: Kafka topic for publishing control commands
        """
        # Kafka Consumer Configuration
        self.kafka_consumer_config = {
            'bootstrap.servers': kafka_broker,
            'group.id': 'occupancy-detector-group',
            'auto.offset.reset': 'earliest'
        }
        self.consumer = Consumer(self.kafka_consumer_config)
        self.consumer.subscribe(topics)
        
        # Kafka Producer Configuration
        self.kafka_producer_config = {
            'bootstrap.servers': kafka_broker
        }
        self.producer = Producer(self.kafka_producer_config)
        
        self.iot_api_url = iot_api_url
        
        # Configure logging
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('OccupancyDetectorAgent')
        
        # Track room occupancy states
        self.room_occupancy = {}

    def analyze_occupancy(self, data: Dict[str, Any]) -> bool:
        """
        Analyze sensor data to determine room occupancy
        
        :param data: Sensor data dictionary
        :return: Occupancy state (True/False)
        """
        # Check presence state and sensitivity
        return (
            data.get('presence_state', False) and 
            data.get('sensitivity', 0) > 0.5 and 
            data.get('online_status', False)
        )

    def publish_control_command(self, room_id: str, command: Dict[str, Any]):
        """
        Publish control command to Kafka
        
        :param room_id: Room identifier
        :param command: Control command dictionary
        """
        try:
            self.producer.produce(
                'room-control', 
                key=room_id.encode('utf-8'),
                value=json.dumps(command).encode('utf-8')
            )
            self.producer.flush()
            self.logger.info(f"Published control command for room {room_id}: {command}")
        except Exception as e:
            self.logger.error(f"Kafka publish error: {e}")

    async def send_control_command(self, room_id: str, command: Dict[str, Any]):
        """
        Send control command via HTTP to IoT device API
        
        :param room_id: Room identifier
        :param command: Control command dictionary
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f'{self.iot_api_url}/rooms/{room_id}/control', json=command) as response:
                    result = await response.json()
                    self.logger.info(f"Control command response for room {room_id}: {result}")
            except Exception as e:
                self.logger.error(f"Error sending control command to room {room_id}: {e}")

    async def run(self):
        """
        Main agent run method - consume Kafka messages and detect occupancy
        """
        while True:
            try:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                
                if msg.error():
                    self.logger.error(f'Kafka error: {msg.error()}')
                    continue
                
                # Parse message
                value = json.loads(msg.value().decode('utf-8'))
                room_id = value.get('room_id')
                
                if not room_id:
                    continue
                
                # Determine occupancy
                is_occupied = self.analyze_occupancy(value)
                
                # Track changes in occupancy state
                previous_state = self.room_occupancy.get(room_id, False)
                
                if is_occupied != previous_state:
                    self.logger.info(f"Occupancy state changed for {room_id}: {is_occupied}")
                    
                    # If room is not occupied, send AC control command
                    if not is_occupied:
                        control_command = {
                            'device': 'ac',
                            'action': 'set_temperature',
                            'value': 26.5  # Set to energy-saving temperature
                        }
                        
                        # Publish to Kafka and send via HTTP
                        self.publish_control_command(room_id, control_command)
                        await self.send_control_command(room_id, control_command)
                
                # Update occupancy state
                self.room_occupancy[room_id] = is_occupied
                
            except Exception as e:
                self.logger.error(f"Error processing message: {e}")
                
            # Small sleep to prevent tight looping
            await asyncio.sleep(0.1)

def main():
    # Configuration can be loaded from environment variables
    agent = OccupancyDetectorAgent(
        kafka_broker='kafka:9092',  # Docker Kafka service
        iot_api_url='http://iot-simulation:8000'  # IoT simulation service
    )
    
    asyncio.run(agent.run())

if __name__ == '__main__':
    main()