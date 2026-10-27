"""Background queue, restart recovery and checkpoint resume."""

from concurrent.futures import ThreadPoolExecutor

from app.workers.run_worker import RunWorker


def test_queue_restart_resume_and_no_duplicate_findings(api_client, review_seed):
    first = review_seed()
    second = review_seed(False)
    accepted = api_client.post(f"/api/v1/reviews/{first['id']}/runs")
    assert accepted.status_code == 202, accepted.text
    run_id = accepted.json()["run_id"]
    revision_id = accepted.json()["review_id"]
    assert revision_id != first["id"]
    next_run = api_client.post(f"/api/v1/reviews/{second['id']}/runs").json()["run_id"]
    worker = RunWorker()
    worker.tick()
    assert api_client.get(f"/api/v1/runs/{run_id}").json()["status"] == "running"
    assert api_client.get(f"/api/v1/runs/{next_run}").json()["status"] == "queued"
    before = api_client.get(f"/api/v1/runs/{run_id}").json()["step_count"]
    worker.recover_interrupted()
    assert api_client.get(f"/api/v1/runs/{run_id}").json()["status"] == "interrupted"
    assert api_client.post(f"/api/v1/runs/{run_id}/resume").status_code == 202
    assert api_client.post(f"/api/v1/runs/{run_id}/resume").status_code == 409
    for _ in range(40):
        worker.tick()
    result = api_client.get(f"/api/v1/runs/{run_id}").json()
    assert result["status"] == "completed"
    assert result["step_count"] > before
    assert api_client.post(f"/api/v1/runs/{run_id}/resume").status_code == 409
    events = api_client.get(f"/api/v1/runs/{run_id}/events").json()["items"]
    assert [event["sequence"] for event in events] == list(range(1, len(events) + 1))
    findings = api_client.get(f"/api/v1/reviews/{revision_id}").json()["findings"]
    assert len({finding["id"] for finding in findings}) == len(findings)
    assert api_client.get(f"/api/v1/reviews/{first['id']}").json()["findings"] == []


def test_concurrent_start_for_same_review_is_serialized(api_client, review_seed):
    """Concurrent submissions cannot create duplicate active review runs."""
    review = review_seed(False)
    path = f"/api/v1/reviews/{review['id']}/runs"
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: api_client.post(path), range(2)))
    assert sorted(response.status_code for response in responses) == [202, 409]
    accepted = next(
        response.json() for response in responses if response.status_code == 202
    )
    assert (
        api_client.get(f"/api/v1/runs/{accepted['run_id']}").json()["status"]
        == "queued"
    )
