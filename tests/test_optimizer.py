from src.optimizer import prune_context, compress_state


def test_prune_removes_irrelevant_documents():
    query = "Evaluate candidate for Python backend job"
    docs = [
        "Python is a programming language for web development.",
        "Django is a Python web framework with ORM support.",
        "Ancient Rome was a civilization that lasted centuries.",
        "Baking sourdough bread requires daily feeding of starter.",
    ]
    job_skills = ["Python", "Django", "SQL", "REST APIs"]

    relevant, removed = prune_context(query, docs, job_skills)

    assert "Python is a programming language for web development." in relevant
    assert "Django is a Python web framework with ORM support." in relevant
    assert "Ancient Rome was a civilization that lasted centuries." in removed
    assert "Baking sourdough bread requires daily feeding of starter." in removed


def test_relevant_documents_remain():
    query = "Evaluate Alex Chen for Junior Python Backend Developer"
    docs = [
        "Task Manager API built with Django REST Framework and PostgreSQL includes Python backend code.",
        "Blog Platform with Django user auth and PostgreSQL database uses Python for backend logic.",
        "Python is widely used for web backend development especially with Django and REST APIs.",
    ]
    job_skills = ["Python", "Django", "SQL", "REST APIs"]

    relevant, removed = prune_context(query, docs, job_skills)

    for doc in docs:
        assert doc in relevant
    assert len(removed) == 0


def test_empty_documents():
    relevant, removed = prune_context("test query", [], ["Python"])
    assert relevant == []
    assert removed == []


def test_compress_state_contains_required_fields():
    full = {
        "summary": "Good candidate match.",
        "matched_skills": ["Python", "Django"],
        "missing_skills": ["Docker"],
        "score": 75,
        "recommendation": "proceed",
        "thinking": "Step-by-step reasoning here...",
        "detailed_assessment": "Long paragraph of evaluation...",
    }
    compressed = compress_state(full)

    expected = {"summary", "matched_skills", "missing_skills", "score", "recommendation"}
    assert set(compressed.keys()) == expected
    assert compressed["summary"] == "Good candidate match."
    assert compressed["score"] == 75


def test_compress_state_drops_verbose_fields():
    full = {
        "summary": "summary",
        "matched_skills": ["Python"],
        "missing_skills": [],
        "score": 70,
        "recommendation": "proceed",
        "thinking": "verbose reasoning",
        "detailed_assessment": "verbose assessment",
    }
    compressed = compress_state(full)

    assert "thinking" not in compressed
    assert "detailed_assessment" not in compressed


def test_compress_state_handles_missing_fields():
    full = {
        "summary": "test",
        "matched_skills": ["Python"],
    }
    compressed = compress_state(full)

    assert "summary" in compressed
    assert "matched_skills" in compressed
    # score and recommendation are missing — they should be absent
    # (the caller is responsible for defaults; compress just filters)
    assert "score" not in compressed
    assert "recommendation" not in compressed


def test_prune_handles_empty_job_skills():
    query = "test query"
    docs = [
        "Python programming language",
        "Ancient Rome history",
    ]
    job_skills: list[str] = []

    relevant, removed = prune_context(query, docs, job_skills)

    # Without job_skills the threshold still uses query tokens
    assert len(relevant) + len(removed) == len(docs)
