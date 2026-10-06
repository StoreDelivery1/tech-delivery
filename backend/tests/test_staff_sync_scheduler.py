import logging
import threading
import unittest
from unittest.mock import Mock, patch

from apscheduler.schedulers.base import STATE_STOPPED

from app.services.staff_sync_scheduler import (
    _JOB_ID,
    build_staff_sync_scheduler,
    get_next_staff_sync_run,
    run_scheduled_staff_sync,
)
from app.services.staff_sync_service import SyncReport


class TestStaffSyncScheduler(unittest.TestCase):
    def test_scheduler_registers_daily_job_without_starting_it(self):
        scheduler = build_staff_sync_scheduler()

        try:
            job = scheduler.get_job(_JOB_ID)
            self.assertEqual(scheduler.state, STATE_STOPPED)
            self.assertIsNotNone(job)
            self.assertEqual(job.max_instances, 1)
            self.assertTrue(job.coalesce)
            self.assertEqual(job.misfire_grace_time, 3600)
            self.assertEqual(str(job.trigger.fields[5].expressions[0]), "3")
            self.assertEqual(str(job.trigger.fields[6].expressions[0]), "15")
            self.assertEqual(job.trigger.timezone.key, "Europe/Kyiv")
        finally:
            if scheduler.running:
                scheduler.shutdown(wait=False)

    def test_schedule_check_computes_next_run_without_executing_sync(self):
        with patch("app.services.staff_sync_scheduler.run_scheduled_staff_sync") as sync_job:
            next_run = get_next_staff_sync_run()

        self.assertIsNotNone(next_run)
        self.assertEqual(str(next_run.tzinfo), "Europe/Kyiv")
        sync_job.assert_not_called()

    def test_job_calls_sync_and_logs_summary(self):
        session = Mock()
        report = SyncReport(created=2, updated=3, blocked=1, skipped=4, errors=["bad row"])
        with (
            patch("app.services.staff_sync_scheduler._acquire_distributed_lock", return_value=(None, True)),
            patch("app.services.staff_sync_scheduler.GoogleSheetsService.read_staff_rows", return_value=[["header"]]),
            patch("app.services.staff_sync_scheduler.SessionLocal", return_value=session),
            patch("app.services.staff_sync_scheduler.sync_staff_rows", return_value=report) as sync,
            self.assertLogs("app.services.staff_sync_scheduler", level="INFO") as logs,
        ):
            result = run_scheduled_staff_sync()

        self.assertIs(result, report)
        sync.assert_called_once_with(session, [["header"]], dry_run=False)
        session.close.assert_called_once()
        self.assertTrue(any("created=2 updated=3 blocked=1 skipped=4 errors=1" in line for line in logs.output))

    def test_job_failure_is_logged_and_rolled_back_without_raising(self):
        session = Mock()
        with (
            patch("app.services.staff_sync_scheduler._acquire_distributed_lock", return_value=(None, True)),
            patch("app.services.staff_sync_scheduler.GoogleSheetsService.read_staff_rows", return_value=[["header"]]),
            patch("app.services.staff_sync_scheduler.SessionLocal", return_value=session),
            patch("app.services.staff_sync_scheduler.sync_staff_rows", side_effect=RuntimeError("sync failed")),
            self.assertLogs("app.services.staff_sync_scheduler", level="ERROR") as logs,
        ):
            result = run_scheduled_staff_sync()

        self.assertIsNone(result)
        session.rollback.assert_called_once()
        session.close.assert_called_once()
        self.assertTrue(any("sync failed" in line for line in logs.output))

    def test_concurrent_job_is_skipped_while_first_run_is_active(self):
        entered_sync = threading.Event()
        release_sync = threading.Event()
        session = Mock()

        def blocking_sync(*args, **kwargs):
            entered_sync.set()
            release_sync.wait(timeout=3)
            return SyncReport(created=1)

        with (
            patch("app.services.staff_sync_scheduler._acquire_distributed_lock", return_value=(None, True)),
            patch("app.services.staff_sync_scheduler.GoogleSheetsService.read_staff_rows", return_value=[["header"]]),
            patch("app.services.staff_sync_scheduler.SessionLocal", return_value=session),
            patch("app.services.staff_sync_scheduler.sync_staff_rows", side_effect=blocking_sync) as sync,
            self.assertLogs("app.services.staff_sync_scheduler", level="WARNING"),
        ):
            first_result = []
            worker = threading.Thread(target=lambda: first_result.append(run_scheduled_staff_sync()))
            worker.start()
            try:
                self.assertTrue(entered_sync.wait(timeout=2))
                second_result = run_scheduled_staff_sync()
            finally:
                release_sync.set()
                worker.join(timeout=3)

        self.assertFalse(worker.is_alive())
        self.assertIsNone(second_result)
        self.assertEqual(sync.call_count, 1)
        self.assertEqual(first_result[0].created, 1)


if __name__ == "__main__":
    unittest.main()