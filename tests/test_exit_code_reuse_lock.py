import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
OWNER = "AzariaFixture"
REPO = "ExitCodeReuseLock-Sources"
PATH = "/docs/exit-codes.md"
CHANGELOG_PATH = "/CHANGELOG.md"
COMMITS = {
    "baseline": "1" * 40,
    "equivalent": "2" * 40,
    "conflict": "3" * 40,
    "disclosed": "4" * 40,
    "injection": "5" * 40,
    "second_equivalent": "6" * 40,
}
TREES = {commit: format(index + 10, "x") * 40 for index, commit in enumerate(COMMITS.values())}
BODIES = {
    (COMMITS["baseline"], PATH): (ROOT / "fixtures/baseline/exit-codes.md").read_bytes(),
    (COMMITS["equivalent"], PATH): (ROOT / "fixtures/equivalent/exit-codes.md").read_bytes(),
    (COMMITS["conflict"], PATH): (ROOT / "fixtures/conflict/exit-codes.md").read_bytes(),
    (COMMITS["disclosed"], PATH): (ROOT / "fixtures/disclosed/exit-codes.md").read_bytes(),
    (COMMITS["disclosed"], CHANGELOG_PATH): (ROOT / "fixtures/disclosed/CHANGELOG.md").read_bytes(),
    (COMMITS["injection"], PATH): (ROOT / "fixtures/injection/exit-codes.md").read_bytes(),
    (COMMITS["second_equivalent"], PATH): (ROOT / "fixtures/equivalent/exit-codes.md").read_bytes(),
}


def sha256(body):
    return hashlib.sha256(body).hexdigest()


def blob_sha(body):
    return hashlib.sha1((f"blob {len(body)}\0").encode() + body).hexdigest()


def source(name, path=PATH, digest=None):
    commit = COMMITS[name]
    body = BODIES[(commit, path)]
    return json.dumps({"owner": OWNER, "repo": REPO, "commit": commit, "path": path, "digest": digest or sha256(body)})


def verdict(kind, release_id=0, namespace_id=0):
    values = {
        "equivalent": (False, "HIGH", "MEANING_EQUIVALENT", True, True, True, "VERIFIED_EQUIVALENT"),
        "disclosed": (True, "HIGH", "DISCLOSED_BREAK", False, False, False, "BREAKING_DISCLOSED"),
        "conflict": (False, "HIGH", "UNDISCLOSED_REASSIGNMENT", False, False, False, "CONFLICT_UNDISCLOSED"),
        "ambiguous": (False, "LOW", "AMBIGUOUS_SEMANTICS", False, False, False, "INCONCLUSIVE"),
    }
    disclosed, confidence, reason, condition, action, retry, result = values[kind]
    return json.dumps({
        "change_disclosed": disclosed,
        "confidence": confidence,
        "namespace_id": namespace_id,
        "reason_code": reason,
        "release_id": release_id,
        "same_condition": condition,
        "same_operator_action": action,
        "same_retry_semantics": retry,
        "verdict": result,
    })


def deploy(vm, direct_deploy, actor):
    vm.strict_mocks = True
    vm.check_pickling = True
    with vm.prank(actor):
        return direct_deploy("contracts/ExitCodeReuseLock.py")


@pytest.fixture
def setup(direct_vm, direct_deploy, direct_alice):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    return direct_vm, contract, direct_alice


def namespace(vm, contract, actor):
    with vm.prank(actor):
        return contract.create_namespace("acme-cli", 7, "## EXIT CODE 7:", source("baseline"))


def mock_commit(vm, commit, paths, missing=None, truncated=False, wrong_blob=False):
    api = f"https://api.github.com/repos/{OWNER}/{REPO}"
    tree_sha = TREES[commit]
    entries = []
    for path in paths:
        body = BODIES[(commit, path)]
        entries.append({"path": path[1:], "type": "blob", "mode": "100644", "size": len(body),
                        "sha": "0" * 40 if wrong_blob else blob_sha(body)})
    vm.mock_web((api + "/git/commits/" + commit).replace(".", r"\.") + "$",
                {"status": 200, "body": json.dumps({"sha": commit, "tree": {"sha": tree_sha}}).encode()})
    vm.mock_web((api + "/git/trees/" + tree_sha + r"\?recursive=1$").replace(".", r"\."),
                {"status": 200, "body": json.dumps({"truncated": truncated, "tree": entries}).encode()})
    if not truncated:
        for path in paths:
            body = BODIES[(commit, path)]
            url = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{commit}{path}"
            vm.mock_web(url.replace(".", r"\.") + "$", {"status": 404 if path == missing else 200, "body": body})


def mock_pair(vm, candidate, changelog=False, **kwargs):
    mock_commit(vm, COMMITS["baseline"], [PATH])
    paths = [PATH, CHANGELOG_PATH] if changelog else [PATH]
    mock_commit(vm, COMMITS[candidate], paths, **kwargs)


def propose(vm, contract, actor, candidate, changelog=False):
    payload = source(candidate, CHANGELOG_PATH) if changelog else ""
    with vm.prank(actor):
        return contract.propose_release(0, source(candidate), payload)


def test_happy_path_activates_exact_candidate(setup, direct_bob):
    vm, contract, deployer = setup
    assert namespace(vm, contract, direct_bob) == 0
    assert propose(vm, contract, direct_bob, "equivalent") == 0
    mock_pair(vm, "equivalent")
    vm.mock_llm(r"Compare the documented operational meaning.*", verdict("equivalent"))
    assert contract.evaluate_release(0) == "VERIFIED_EQUIVALENT"
    with vm.prank(direct_bob):
        assert contract.activate_compatible_release(0) == "ACTIVATED"
    current = json.loads(contract.get_namespace(0))
    assert current["active_source"]["commit"] == COMMITS["equivalent"]
    assert current["head_revision"] == 1
    assert json.loads(contract.get_release(0))["state"] == "ACTIVATED"


def test_undisclosed_conflict_is_blocked_without_head_mutation(setup, direct_bob):
    vm, contract, deployer = setup
    namespace(vm, contract, direct_bob)
    propose(vm, contract, direct_bob, "conflict")
    before = contract.get_namespace(0)
    mock_pair(vm, "conflict")
    vm.mock_llm(r"Compare the documented operational meaning.*", verdict("conflict"))
    assert contract.evaluate_release(0) == "CONFLICT_UNDISCLOSED"
    assert contract.activate_compatible_release(0) == "RELEASE_NOT_ACTIVATABLE"
    assert contract.get_namespace(0) == before
    assert json.loads(contract.get_release(0))["state"] == "BLOCKED"


def test_disclosed_break_is_recorded_but_not_activated(setup, direct_bob):
    vm, contract, deployer = setup
    namespace(vm, contract, direct_bob)
    propose(vm, contract, direct_bob, "disclosed", changelog=True)
    mock_pair(vm, "disclosed", changelog=True)
    vm.mock_llm(r"Compare the documented operational meaning.*", verdict("disclosed"))
    assert contract.evaluate_release(0) == "BREAKING_DISCLOSED"
    assert contract.activate_compatible_release(0) == "RELEASE_NOT_ACTIVATABLE"
    assert json.loads(contract.get_namespace(0))["active_source"]["commit"] == COMMITS["baseline"]


@pytest.mark.parametrize("failure", ["bad_digest", "missing", "truncated", "wrong_blob"])
def test_source_failures_are_fail_closed_and_preserve_head(setup, direct_bob, failure):
    vm, contract, deployer = setup
    namespace(vm, contract, direct_bob)
    candidate_json = source("equivalent", digest="0" * 64) if failure == "bad_digest" else source("equivalent")
    with vm.prank(direct_bob):
        assert contract.propose_release(0, candidate_json, "") == 0
    before = contract.get_namespace(0)
    mock_commit(vm, COMMITS["baseline"], [PATH])
    mock_commit(vm, COMMITS["equivalent"], [PATH], missing=PATH if failure == "missing" else None,
                truncated=failure == "truncated", wrong_blob=failure == "wrong_blob")
    assert contract.evaluate_release(0) == "SOURCE_UNVERIFIED"
    assert contract.get_namespace(0) == before
    assert contract.activate_compatible_release(0) == "RELEASE_NOT_ACTIVATABLE"


def test_prompt_injection_cannot_change_identity_or_positive_gate(setup, direct_bob):
    vm, contract, deployer = setup
    namespace(vm, contract, direct_bob)
    propose(vm, contract, direct_bob, "injection")
    mock_pair(vm, "injection")
    vm.mock_llm(r"Compare the documented operational meaning.*", verdict("equivalent", release_id=999))
    assert contract.evaluate_release(0) == "INCONCLUSIVE"
    assert contract.activate_compatible_release(0) == "RELEASE_NOT_ACTIVATABLE"


@pytest.mark.parametrize("payload", [
    json.dumps({"change_disclosed": False, "confidence": "HIGH", "namespace_id": 0,
                "reason_code": "MEANING_EQUIVALENT", "release_id": 0, "same_condition": True,
                "same_operator_action": False, "same_retry_semantics": True, "verdict": "VERIFIED_EQUIVALENT"}),
    json.dumps({"change_disclosed": False, "confidence": "HIGH", "namespace_id": 0,
                "reason_code": "DISCLOSED_BREAK", "release_id": 0, "same_condition": False,
                "same_operator_action": False, "same_retry_semantics": False, "verdict": "BREAKING_DISCLOSED"}),
])
def test_inconsistent_positive_or_disclosure_output_becomes_inconclusive(setup, direct_bob, payload):
    vm, contract, deployer = setup
    namespace(vm, contract, direct_bob)
    propose(vm, contract, direct_bob, "equivalent")
    mock_pair(vm, "equivalent")
    vm.mock_llm(r"Compare the documented operational meaning.*", payload)
    assert contract.evaluate_release(0) == "INCONCLUSIVE"


def test_stale_parent_race_cannot_overwrite_new_head(setup, direct_bob):
    vm, contract, deployer = setup
    namespace(vm, contract, direct_bob)
    assert propose(vm, contract, direct_bob, "equivalent") == 0
    assert propose(vm, contract, direct_bob, "second_equivalent") == 1
    mock_commit(vm, COMMITS["baseline"], [PATH])
    mock_commit(vm, COMMITS["equivalent"], [PATH])
    mock_commit(vm, COMMITS["second_equivalent"], [PATH])
    vm.mock_llm(r"Compare the documented operational meaning.*", verdict("equivalent", release_id=0))
    assert contract.evaluate_release(0) == "VERIFIED_EQUIVALENT"
    vm._llm_mocks.clear()
    vm.mock_llm(r"Compare the documented operational meaning.*", verdict("equivalent", release_id=1))
    assert contract.evaluate_release(1) == "VERIFIED_EQUIVALENT"
    assert contract.activate_compatible_release(0) == "ACTIVATED"
    before_namespace = contract.get_namespace(0)
    before_counts = contract.get_counts()
    assert contract.activate_compatible_release(1) == "STALE_PARENT"
    assert contract.get_namespace(0) == before_namespace
    assert contract.get_counts() == before_counts


def test_replay_duplicate_and_terminal_guards_preserve_state(setup, direct_bob):
    vm, contract, deployer = setup
    namespace(vm, contract, direct_bob)
    assert propose(vm, contract, direct_bob, "equivalent") == 0
    assert propose(vm, contract, direct_bob, "equivalent") == "DUPLICATE_RELEASE"
    mock_pair(vm, "equivalent")
    vm.mock_llm(r"Compare the documented operational meaning.*", verdict("equivalent"))
    contract.evaluate_release(0)
    contract.activate_compatible_release(0)
    before = (contract.get_namespace(0), contract.get_release(0), contract.get_counts())
    assert contract.evaluate_release(0) == "RELEASE_NOT_PROPOSED"
    assert contract.activate_compatible_release(0) == "RELEASE_NOT_ACTIVATABLE"
    assert before == (contract.get_namespace(0), contract.get_release(0), contract.get_counts())


def test_deployer_has_no_special_business_role(setup, direct_bob):
    vm, contract, deployer = setup
    with vm.prank(direct_bob):
        assert contract.create_namespace("reviewer-cli", 7, "## EXIT CODE 7:", source("baseline")) == 0
    record = json.loads(contract.get_namespace(0))
    assert record["creator"].lower() != str(deployer).lower()
    assert "owner" not in json.loads(contract.get_counts())


def test_authority_revision_and_input_guards(setup, direct_bob):
    vm, contract, deployer = setup
    namespace(vm, contract, direct_bob)
    foreign = json.loads(source("equivalent")); foreign["repo"] = "OtherRepo"
    with vm.prank(direct_bob):
        assert contract.propose_release(0, json.dumps(foreign), "") == "AUTHORITY_MISMATCH"
        assert contract.create_namespace("bad", 7, "marker-without-code", source("baseline")) == "INVALID_NAMESPACE"
        assert contract.propose_release(99, source("equivalent"), "") == "NAMESPACE_NOT_FOUND"
