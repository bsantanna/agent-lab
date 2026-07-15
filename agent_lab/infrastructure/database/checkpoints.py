from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool


class GraphPersistenceFactory:
    def __init__(self, db_checkpoints: str):
        self.connection_kwargs = {
            "autocommit": True,
            "prepare_threshold": 0,
        }

        self.pool = ConnectionPool(
            open=True,
            conninfo=db_checkpoints,
            max_size=20,
            kwargs=self.connection_kwargs,
        )

        # initial setup
        checkpointer = PostgresSaver(self.pool)
        checkpointer.setup()

    def build_checkpoint_saver(self) -> BaseCheckpointSaver:
        return PostgresSaver(self.pool)
