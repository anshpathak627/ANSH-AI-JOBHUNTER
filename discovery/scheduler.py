"""
discovery/scheduler.py
Background job scheduler managing automated daily discovery runs.
"""

from __future__ import annotations

import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class JobScheduler:
    """Manages periodic morning, afternoon, and evening automated job discovery scans."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._is_running = False

    def start(self, discovery_engine_factory):
        """
        Configure and start scheduled discovery cycles.

        Parameters
        ----------
        discovery_engine_factory : callable
            A callable yielding a DiscoveryEngine or an async job function.
        """
        if self._is_running:
            return

        async def _scheduled_scan(run_name: str):
            logger.info("Executing scheduled discovery run: %s", run_name)
            try:
                engine = discovery_engine_factory()
                await engine.run_discovery()
            except Exception as ex:
                logger.error("Error during scheduled discovery (%s): %s", run_name, ex)

        # 1. Morning scan — 07:00
        self.scheduler.add_job(
            _scheduled_scan,
            CronTrigger(hour=7, minute=0),
            args=["Morning 07:00"],
            id="scan_morning",
            replace_existing=True,
        )

        # 2. Afternoon scan — 13:00
        self.scheduler.add_job(
            _scheduled_scan,
            CronTrigger(hour=13, minute=0),
            args=["Afternoon 13:00"],
            id="scan_afternoon",
            replace_existing=True,
        )

        # 3. Evening scan — 20:00
        self.scheduler.add_job(
            _scheduled_scan,
            CronTrigger(hour=20, minute=0),
            args=["Evening 20:00"],
            id="scan_evening",
            replace_existing=True,
        )

        self.scheduler.start()
        self._is_running = True
        logger.info("Job discovery scheduler initialized with 3 daily scanning triggers.")

    def stop(self):
        """Halt the scheduler."""
        if self._is_running:
            self.scheduler.shutdown(wait=False)
            self._is_running = False

    def is_running(self) -> bool:
        """Check if scheduler is active."""
        return self._is_running
