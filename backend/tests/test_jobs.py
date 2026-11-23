import time

from app.jobs import LocalVideoJobRunner


def test_local_video_job_runner_completes_task():
    runner = LocalVideoJobRunner(max_workers=1)
    job = runner.submit('cam01', 'sample.mp4', lambda _job_id: {'status': 'completed', 'frames_processed': 3})

    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        current = runner.get(job.id)
        if current and current.status == 'completed':
            assert current.result == {'status': 'completed', 'frames_processed': 3}
            assert current.progress == 100
            return
        time.sleep(0.01)

    raise AssertionError('job did not complete within the test deadline')


def test_local_video_job_runner_reports_failure():
    runner = LocalVideoJobRunner(max_workers=1)
    job = runner.submit('cam01', 'sample.mp4', lambda _job_id: (_ for _ in ()).throw(ValueError('bad input')))

    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        current = runner.get(job.id)
        if current and current.status == 'failed':
            assert current.error == 'bad input'
            return
        time.sleep(0.01)

    raise AssertionError('failed job was not reported within the test deadline')
