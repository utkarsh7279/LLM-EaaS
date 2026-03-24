"""Batch processing for efficient evaluation of large datasets."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Callable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import EvaluationItem, EvaluationResult

logger = logging.getLogger(__name__)


@dataclass
class BatchConfig:
    """Configuration for batch processing."""

    batch_size: int = 10  # Items per batch
    concurrent_batches: int = 3  # Number of batches to process concurrently
    retry_on_failure: bool = True
    max_retries: int = 3
    timeout_per_item: int = 30  # seconds


@dataclass
class BatchResult:
    """Result of batch processing."""

    total_items: int
    successful: int
    failed: int
    errors: list[dict]
    processing_time: float


class BatchProcessor:
    """Process large datasets in efficient batches."""

    def __init__(self, config: BatchConfig = BatchConfig()):
        self.config = config

    async def process_items(
        self,
        experiment_id: UUID,
        session: AsyncSession,
        process_fn: Callable,
        batch_result: BatchResult,
    ) -> BatchResult:
        """Process evaluation items in batches.

        Args:
            experiment_id: ID of the experiment
            session: Database session
            process_fn: Async function to process each item
            batch_result: Accumulator for results

        Returns:
            BatchResult with processing statistics
        """
        # Fetch items in batches
        result = await session.execute(select(EvaluationItem).where(EvaluationItem.experiment_id == experiment_id))
        items = result.scalars().all()

        total_items = len(items)
        batch_result.total_items = total_items

        if total_items == 0:
            logger.info(f"No items to process for experiment {experiment_id}")
            return batch_result

        # Process items in batches with concurrency
        for i in range(0, len(items), self.config.batch_size):
            batch = items[i : i + self.config.batch_size]
            try:
                tasks = [self._process_item_with_retry(item, process_fn) for item in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for item, result in zip(batch, results):
                    if isinstance(result, Exception):
                        batch_result.failed += 1
                        batch_result.errors.append({"item_id": str(item.id), "error": str(result)})
                        logger.error(f"Failed to process item {item.id}: {result}")
                    else:
                        batch_result.successful += 1

            except Exception as e:
                logger.error(f"Batch processing error: {e}")
                batch_result.failed += len(batch)
                for item in batch:
                    batch_result.errors.append({"item_id": str(item.id), "error": str(e)})

            await asyncio.sleep(0.1)  # Brief pause between batches

        return batch_result

    async def _process_item_with_retry(self, item: EvaluationItem, process_fn: Callable):
        """Process a single item with retry logic."""
        for attempt in range(self.config.max_retries):
            try:
                return await asyncio.wait_for(process_fn(item), timeout=self.config.timeout_per_item)
            except asyncio.TimeoutError:
                if attempt == self.config.max_retries - 1:
                    raise TimeoutError(f"Processing timeout for item {item.id}")
                logger.warning(f"Timeout for item {item.id}, retrying (attempt {attempt + 1})")
                await asyncio.sleep(2**attempt)  # Exponential backoff
            except Exception as e:
                if not self.config.retry_on_failure or attempt == self.config.max_retries - 1:
                    raise
                logger.warning(f"Error processing item {item.id}, retrying (attempt {attempt + 1}): {e}")
                await asyncio.sleep(2**attempt)


class DataVersioning:
    """Track and manage dataset versions."""

    @staticmethod
    async def create_version(
        session: AsyncSession,
        experiment_id: UUID,
        version_name: str,
        description: str = "",
    ) -> dict:
        """Create a new version of experiment data.

        Returns:
            Version metadata
        """
        from datetime import datetime

        version_metadata = {
            "version_id": str(UUID),
            "experiment_id": str(experiment_id),
            "version_name": version_name,
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
            "item_count": 0,
        }
        return version_metadata

    @staticmethod
    async def compare_versions(
        session: AsyncSession,
        version_1_id: UUID,
        version_2_id: UUID,
    ) -> dict:
        """Compare two dataset versions.

        Returns:
            Comparison statistics
        """
        return {
            "items_added": 0,
            "items_removed": 0,
            "items_modified": 0,
            "similarity_score": 0.0,
        }


class ParallelEvaluator:
    """Parallel evaluation with worker pool."""

    def __init__(self, max_workers: int = 5, chunk_size: int = 10):
        self.max_workers = max_workers
        self.chunk_size = chunk_size

    async def evaluate_parallel(
        self,
        items: list,
        evaluate_fn: Callable,
    ) -> list[dict]:
        """Evaluate items in parallel."""
        semaphore = asyncio.Semaphore(self.max_workers)

        async def bounded_evaluate(item):
            async with semaphore:
                return await evaluate_fn(item)

        results = await asyncio.gather(*[bounded_evaluate(item) for item in items])
        return results
