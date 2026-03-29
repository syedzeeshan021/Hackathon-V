#!/usr/bin/env python3
# Customer Success FTE - Message Processor Worker
# Entry point for Kafka message processing worker

import asyncio
import logging
import signal
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from production.core.config import settings
from production.kafka.consumer import run_worker, MessageProcessorWorker
from production.db import init_pool, close_pool

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global worker instance
worker: MessageProcessorWorker = None
shutdown_event = asyncio.Event()


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {sig}, initiating shutdown...")
    shutdown_event.set()


async def main():
    """Main worker entry point."""
    global worker

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting Customer Success FTE Message Processor Worker...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Kafka Bootstrap Servers: {settings.kafka_bootstrap_servers}")

    try:
        # Initialize database pool
        await init_pool()
        logger.info("Database pool initialized")

        # Create and start worker
        worker = MessageProcessorWorker()
        await worker.start()

        logger.info("Worker started successfully. Press Ctrl+C to stop.")

        # Wait for shutdown signal
        await shutdown_event.wait()

    except Exception as e:
        logger.error(f"Worker error: {e}")
        raise

    finally:
        # Cleanup
        logger.info("Shutting down worker...")

        if worker:
            await worker.stop()

        await close_pool()
        logger.info("Worker shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker exited with error: {e}")
        sys.exit(1)
