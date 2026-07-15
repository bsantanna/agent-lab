import logging

import redis
from pydantic import BaseModel
from typing_extensions import Literal, Optional, Dict, Any


class TaskProgress(BaseModel):
    """Model for task progress updates"""

    agent_id: str
    status: Literal["in_progress", "completed", "failed"]
    message_content: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None


class TaskNotificationService:
    """Service for Notification pub/sub operations"""

    def __init__(self, redis_url: str, channel: str = "task_updates"):
        self.redis_client = redis.StrictRedis.from_url(redis_url)
        self.pubsub = self.redis_client.pubsub()
        self.channel = channel
        self.logger = logging.getLogger(__name__)

    def publish_update(self, task_progress: TaskProgress):
        """Publish a task update to Redis"""
        message = task_progress.model_dump_json()
        self.redis_client.publish(self.channel, message)
        self.logger.debug(f"Published update for task {task_progress.agent_id}")

    def subscribe(self):
        """Subscribe to the task updates channel"""
        self.pubsub.subscribe(self.channel)
        self.logger.info(f"Subscribed to channel: {self.channel}")

    def listen(self):
        """Listen for messages on the subscribed channel"""
        return self.pubsub.listen()

    def close(self):
        """Close Redis connections"""
        self.pubsub.unsubscribe()
        self.pubsub.close()
        self.redis_client.close()
        self.logger.info("Redis connections closed")
