import asyncio
import json
import logging
from typing import Dict, Any
from confluent_kafka import Consumer, KafkaError
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class LifeBeingSensorLog(Base):
    __tablename__ = 'life_being_sensor_logs'
    
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    room_id = sa.Column(sa.String(50), nullable=False)
    presence_state = sa.Column(sa.Boolean, nullable=False)
    sensitivity = sa.Column(sa.Float, nullable=False)
    online_status = sa.Column(sa.Boolean, nullable=False)
    timestamp = sa.Column(sa.DateTime, nullable=False)

class IAQSensorLog(Base):
    __tablename__ = 'iaq_sensor_logs'
    
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    room_id = sa.Column(sa.String(50), nullable=False)
    noise = sa.Column(sa.Float, nullable=False)
    co2 = sa.Column(sa.Float, nullable=False)
    pm25 = sa.Column(sa.Float, nullable=False)
    humidity = sa.Column(sa.Float, nullable=False)
    temperature = sa.Column(sa.Float, nullable=False)
    illuminance = sa.Column(sa.Float, nullable=False)
    online_status = sa.Column(sa.Boolean, nullable=False)
    device_status = sa.Column(sa.String(50), nullable=False)
    timestamp = sa.Column(sa.DateTime, nullable=False)

class DataLoggerAgent:
    def __init__(self, 
                 kafka_broker: str, 
                 database_url: str,
                 topics: list[str] = ['life-being', 'iaq']):
        """
        Initialize Data Logger Agent
        
        :param kafka_broker: Kafka broker address
        :param database_url: Async database connection URL
        :param topics: Kafka topics to consume
        """
        # Kafka Consumer Configuration
        self.kafka_config = {
            'bootstrap.servers': kafka_broker,
            'group.id': 'data-logger-group',
            'auto.offset.reset': 'earliest'
        }
        self.consumer = Consumer(self.kafka_config)
        self.consumer.subscribe(topics)
        
        # Database Configuration
        self.engine = create_async_engine(database_url, echo=True)
        self.async_session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
        
        # Configure logging
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('DataLoggerAgent')

    async def create_tables(self):
        """Create database tables if they don't exist"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def log_life_being_data(self, session: AsyncSession, data: Dict[str, Any]):
        """Log Life Being sensor data to database"""
        log_entry = LifeBeingSensorLog(
            room_id=data.get('room_id'),
            presence_state=data.get('presence_state'),
            sensitivity=data.get('sensitivity'),
            online_status=data.get('online_status'),
            timestamp=data.get('timestamp')
        )
        session.add(log_entry)
        await session.commit()

    async def log_iaq_data(self, session: AsyncSession, data: Dict[str, Any]):
        """Log IAQ sensor data to database"""
        log_entry = IAQSensorLog(
            room_id=data.get('room_id'),
            noise=data.get('noise'),
            co2=data.get('co2'),
            pm25=data.get('pm25'),
            humidity=data.get('humidity'),
            temperature=data.get('temperature'),
            illuminance=data.get('illuminance'),
            online_status=data.get('online_status'),
            device_status=data.get('device_status'),
            timestamp=data.get('timestamp')
        )
        session.add(log_entry)
        await session.commit()

    async def run(self):
        """
        Main agent run method - consume Kafka messages and log to database
        """
        # Create tables first
        await self.create_tables()
        
        while True:
            try:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        self.logger.info('Reached end of partition')
                    else:
                        self.logger.error(f'Kafka error: {msg.error()}')
                    continue
                
                # Parse message
                topic = msg.topic()
                value = json.loads(msg.value().decode('utf-8'))
                
                # Log to database
                async with self.async_session() as session:
                    if topic == 'life-being':
                        await self.log_life_being_data(session, value)
                    elif topic == 'iaq':
                        await self.log_iaq_data(session, value)
                
            except Exception as e:
                self.logger.error(f"Error processing message: {e}")
                
            # Small sleep to prevent tight looping
            await asyncio.sleep(0.1)

def main():
    # Configuration can be loaded from environment variables
    agent = DataLoggerAgent(
        kafka_broker='kafka:9092',  # Docker Kafka service
        database_url='postgresql+asyncpg://user:password@postgres:5432/iotdb'
    )
    
    asyncio.run(agent.run())

if __name__ == '__main__':
    main()