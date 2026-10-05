from pathlib import Path


SOURCE = (Path(__file__).parents[1] / "contracts/ExitCodeReuseLock.py").read_text(encoding="utf-8")


def test_runtime_header_and_storage_rules():
    assert SOURCE.startswith("# v0.2.16")
    assert "from genlayer import *" in SOURCE
    assert "class Contract(gl.Contract):" in SOURCE
    for item in ["namespaces: TreeMap[str, str]", "releases: TreeMap[str, str]", "release_keys: TreeMap[str, str]"]:
        assert item in SOURCE
    assert "self.namespaces =" not in SOURCE and "self.releases =" not in SOURCE


def test_architecture_is_slot_activation_not_court_clone():
    for item in ["create_namespace", "propose_release", "evaluate_release", "activate_compatible_release", "STALE_PARENT"]:
        assert item in SOURCE
    for forbidden in ["challenge_deadline", "submit_rebuttal", "CONTESTED", "revise_context", "SUPERSEDED"]:
        assert forbidden not in SOURCE


def test_authenticated_fetch_and_positive_gate_exist():
    for item in ["/git/commits/", "/git/trees/", "_blob_sha1(body)", "hashlib.sha256(body).hexdigest()",
                 "same_condition", "same_operator_action", "same_retry_semantics", "gl.eq_principle.prompt_comparative"]:
        assert item in SOURCE


def test_no_deployer_or_admin_privilege_and_no_clock_deadline():
    for forbidden in ["self.owner", "deployer", "only_owner", "datetime.now", "time.time", "deadline"]:
        assert forbidden not in SOURCE
