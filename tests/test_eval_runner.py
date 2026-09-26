def test_run_one_uses_safe_refusal_when_retrieval_returns_no_chunks(monkeypatch):
    from scripts import run_ab_eval

    monkeypatch.setattr(run_ab_eval, "retrieve", lambda *args, **kwargs: [])

    result = run_ab_eval.run_one("Cách nướng cá basa?", use_reranking=False)

    assert result == {
        "answer": run_ab_eval.SAFE_REFUSAL,
        "contexts": [],
        "source_ids": [],
        "latency_seconds": 0.0,
    }
