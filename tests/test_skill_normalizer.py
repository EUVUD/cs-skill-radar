from cs_skill_radar.extraction.skill_normalizer import normalize_skill


def test_common_skill_aliases_normalize_to_canonical_names():
    assert normalize_skill("Postgres") == "PostgreSQL"
    assert normalize_skill("K8s") == "Kubernetes"
    assert normalize_skill("Node") == "Node.js"
    assert normalize_skill("React.js") == "React"
    assert normalize_skill("Amazon Web Services") == "AWS"


def test_unknown_skill_is_cleaned_but_not_rewritten():
    assert normalize_skill("  custom internal platform  ") == "custom internal platform"
