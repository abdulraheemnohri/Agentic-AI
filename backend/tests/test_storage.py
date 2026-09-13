from app.storage import SQLiteStore


def test_task_round_trip(tmp_path):
    store = SQLiteStore(tmp_path / "test.db")
    task = {"id": "t1", "created_at": "now", "updated_at": "now", "status": "completed", "goal": "hello", "autonomy": 1}
    store.save_task(task)
    assert store.load_tasks()[0]["id"] == "t1"


def test_evaluation_history(tmp_path):
    store = SQLiteStore(tmp_path / "test.db")
    store.save_evaluation("t1", {"overall_score": 1}, "now")
    assert store.list_evaluations("t1")[0]["overall_score"] == 1


def test_memory_search(tmp_path):
    store = SQLiteStore(tmp_path / "test.db")
    store.save_memory({"memory_id": "m1", "created_at": "now", "kind": "semantic", "importance": 0.9, "content": "python agent", "metadata": {}})
    assert store.search_memories("python")[0]["memory_id"] == "m1"
