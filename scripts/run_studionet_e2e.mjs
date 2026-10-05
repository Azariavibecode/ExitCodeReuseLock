import { createClient } from "../../DependencyPatchPermit/frontend/node_modules/genlayer-js/dist/index.js";
import { studionet } from "../../DependencyPatchPermit/frontend/node_modules/genlayer-js/dist/chains/index.js";
import { TransactionStatus } from "../../DependencyPatchPermit/frontend/node_modules/genlayer-js/dist/types/index.js";
import { privateKeyToAccount } from "../../DependencyPatchPermit/frontend/node_modules/viem/_esm/accounts/index.js";
import { existsSync, readFileSync, writeFileSync } from "node:fs";

const envPath = "../DependencyPatchPermit/.env";
if (existsSync(envPath)) {
  for (const line of readFileSync(envPath, "utf8").split(/\r?\n/)) {
    const match = line.match(/^([A-Z0-9_]+)=(.+)$/);
    if (match && !process.env[match[1]]) process.env[match[1]] = match[2].trim();
  }
}

const contract = "0xe4A2325AFBb21C7159eB63421640D07Cec71AF10";
const explorer = "https://explorer-studio.genlayer.com";
const keys = [process.env.TEST_WALLET_A_PRIVATE_KEY, process.env.TEST_WALLET_B_PRIVATE_KEY];
if (keys.some((key) => !/^(0x)?[0-9a-fA-F]{64}$/.test(key || ""))) {
  throw new Error("Set both test wallet keys in the ignored DependencyPatchPermit/.env file");
}
const wallets = keys.map((key) => privateKeyToAccount(key.startsWith("0x") ? key : `0x${key}`));
if (wallets[0].address.toLowerCase() === wallets[1].address.toLowerCase()) throw new Error("Test wallets must differ");

const reader = createClient({ chain: studionet });
const writer = (wallet) => createClient({ chain: studionet, account: wallet });
const parse = async (name, args = []) => JSON.parse(await reader.readContract({ address: contract, functionName: name, args }));
const transactions = [];

async function write(wallet, functionName, args, label) {
  const hash = await writer(wallet).writeContract({ address: contract, functionName, args });
  const receipt = await reader.waitForTransactionReceipt({
    hash,
    status: TransactionStatus.FINALIZED,
    interval: 3000,
    retries: 100,
  });
  const status = receipt.status_name || receipt.status;
  const transaction = await reader.getTransaction({ hash });
  const resultName = transaction?.result_name || transaction?.resultName || transaction?.result?.name || "";
  if (status !== TransactionStatus.FINALIZED || (resultName && resultName !== "MAJORITY_AGREE")) {
    throw new Error(`${label} failed: ${status}/${resultName}`);
  }
  transactions.push({
    label,
    hash,
    explorer_url: `${explorer}/transactions/${hash}`,
    actor: wallet.address,
    status,
    result_name: resultName || "FINALIZED",
  });
  console.log(`${label}: ${hash}`);
  return hash;
}

const commits = {
  baseline: "49656b28a089b3273b9a004fd6f94d8025dc4199",
  equivalent: "cdb1280d9b896112d80a5938caf8614412c6d652",
  conflict: "24c1a7185a762608f4a85f5a4e00f55d330d2644",
  disclosed: "24b161e42517c5bffe15ac434ea0501daced0725",
  staleEquivalent: "cf3e609c0c431891c272f475a0cca4dfe8b64032",
};
const digests = {
  baseline: "0ae0ba6b9bd8183582dfd4392e824cace041b75f837e3a4fa4a47b91d3dca6a2",
  equivalent: "e85d50bd639bc0e046f77c906b8d66f8a3032bfc8f65ac4c4f0327fcbbaf3220",
  conflict: "d433b2f59bfc5d4999e405d558f76a7d997ad1e7e969356c571e59167dbb0c6f",
  disclosed: "07bad95027eda5ec1c607bb5af9e2b1bed07c957f2eb28536ffd8553a9bbac6f",
  disclosedChangelog: "4d5584b7739e610e1ff606de360330d7caeca9323d028b06d48e6f29b142aeac",
  staleEquivalent: "9d19ac0ec3614cb4935da6c75725e70dfd14b7a7ad6bd76e6aeb0cd14e6efd4e",
};
const source = (commit, path, digest) => JSON.stringify({
  owner: "Azariavibecode",
  repo: "ExitCodeReuseLock",
  commit,
  path,
  digest,
});
const doc = (name, digest = digests[name]) => source(commits[name], "/fixtures/e2e/exit-codes.md", digest);
const changelog = source(commits.disclosed, "/fixtures/e2e/CHANGELOG.md", digests.disclosedChangelog);

const before = await parse("get_counts");
const namespaceId = BigInt(before.namespace_count);
const firstReleaseId = BigInt(before.release_count);

await write(wallets[0], "create_namespace", ["acme-cli-live", 7n, "## EXIT CODE 7:", doc("baseline")], "happy_create_namespace");
const namespaceCreated = await parse("get_namespace", [namespaceId]);
if (namespaceCreated.creator.toLowerCase() !== wallets[0].address.toLowerCase()) throw new Error("Auxiliary wallet A was not recorded as creator");
if (namespaceCreated.active_source.commit !== commits.baseline || namespaceCreated.head_revision !== 0) throw new Error("Baseline namespace readback mismatch");

await write(wallets[1], "propose_release", [namespaceId, doc("equivalent"), ""], "happy_propose_equivalent");
await write(wallets[0], "propose_release", [namespaceId, doc("staleEquivalent"), ""], "race_propose_second_equivalent");
await write(wallets[1], "propose_release", [namespaceId, doc("conflict"), ""], "conflict_propose_undisclosed");
const equivalentId = firstReleaseId;
const staleId = firstReleaseId + 1n;
const conflictId = firstReleaseId + 2n;

await write(wallets[0], "evaluate_release", [conflictId], "conflict_evaluate_undisclosed");
const conflictRecord = await parse("get_release", [conflictId]);
if (conflictRecord.verdict !== "CONFLICT_UNDISCLOSED" || conflictRecord.state !== "BLOCKED") {
  throw new Error(`Conflict did not fail closed: ${JSON.stringify(conflictRecord)}`);
}
const headBeforeConflictActivation = await parse("get_namespace", [namespaceId]);
await write(wallets[1], "activate_compatible_release", [conflictId], "failure_activate_conflict");
if (JSON.stringify(await parse("get_namespace", [namespaceId])) !== JSON.stringify(headBeforeConflictActivation)) {
  throw new Error("Blocked conflict mutated namespace head");
}

await write(wallets[1], "evaluate_release", [equivalentId], "happy_evaluate_equivalent");
await write(wallets[0], "evaluate_release", [staleId], "race_evaluate_second_equivalent");
for (const id of [equivalentId, staleId]) {
  const release = await parse("get_release", [id]);
  if (release.verdict !== "VERIFIED_EQUIVALENT" || release.state !== "EVALUATED") {
    throw new Error(`Equivalent release ${id} was not evaluable: ${JSON.stringify(release)}`);
  }
}

await write(wallets[1], "activate_compatible_release", [equivalentId], "happy_activate_equivalent");
const activatedHead = await parse("get_namespace", [namespaceId]);
if (activatedHead.active_source.commit !== commits.equivalent || activatedHead.head_revision !== 1) {
  throw new Error("Equivalent activation did not reconcile authoritative head");
}
const countsBeforeStale = await parse("get_counts");
await write(wallets[0], "activate_compatible_release", [staleId], "race_reject_stale_parent");
if (JSON.stringify(await parse("get_namespace", [namespaceId])) !== JSON.stringify(activatedHead)) throw new Error("Stale activation changed head");
if (JSON.stringify(await parse("get_counts")) !== JSON.stringify(countsBeforeStale)) throw new Error("Stale activation changed counters");

const disclosedId = BigInt((await parse("get_counts")).release_count);
await write(wallets[0], "propose_release", [namespaceId, doc("disclosed"), changelog], "breaking_propose_disclosed");
await write(wallets[1], "evaluate_release", [disclosedId], "breaking_evaluate_disclosed");
const disclosedRecord = await parse("get_release", [disclosedId]);
if (disclosedRecord.verdict !== "BREAKING_DISCLOSED" || disclosedRecord.state !== "BLOCKED") {
  throw new Error(`Disclosed break not recorded safely: ${JSON.stringify(disclosedRecord)}`);
}
const headBeforeBreakingActivation = await parse("get_namespace", [namespaceId]);
await write(wallets[0], "activate_compatible_release", [disclosedId], "failure_activate_breaking");
if (JSON.stringify(await parse("get_namespace", [namespaceId])) !== JSON.stringify(headBeforeBreakingActivation)) throw new Error("Breaking release changed head");

const poisonedId = BigInt((await parse("get_counts")).release_count);
await write(wallets[1], "propose_release", [namespaceId, doc("conflict", "0".repeat(64)), ""], "failure_propose_bad_digest");
await write(wallets[0], "evaluate_release", [poisonedId], "failure_evaluate_bad_digest");
const poisonedRecord = await parse("get_release", [poisonedId]);
if (poisonedRecord.verdict !== "SOURCE_UNVERIFIED" || poisonedRecord.state !== "BLOCKED") {
  throw new Error(`Poisoned source did not fail closed: ${JSON.stringify(poisonedRecord)}`);
}

const replayBefore = {
  namespace: await parse("get_namespace", [namespaceId]),
  release: await parse("get_release", [equivalentId]),
  counts: await parse("get_counts"),
};
await write(wallets[0], "evaluate_release", [equivalentId], "failure_replay_evaluation");
await write(wallets[1], "activate_compatible_release", [equivalentId], "failure_replay_activation");
const replayAfter = {
  namespace: await parse("get_namespace", [namespaceId]),
  release: await parse("get_release", [equivalentId]),
  counts: await parse("get_counts"),
};
if (JSON.stringify(replayBefore) !== JSON.stringify(replayAfter)) throw new Error("Terminal replay mutated state");

const after = await parse("get_counts");
const result = {
  generated_at: new Date().toISOString(),
  network: "StudioNet",
  chain_id: 61999,
  contract,
  contract_explorer_url: `${explorer}/address/${contract}`,
  wallets: { auxiliary_a: wallets[0].address, auxiliary_b: wallets[1].address },
  source_commits: commits,
  source_digests: digests,
  before,
  after,
  namespace: await parse("get_namespace", [namespaceId]),
  releases: {
    equivalent: await parse("get_release", [equivalentId]),
    stale_equivalent: await parse("get_release", [staleId]),
    conflict: conflictRecord,
    disclosed: disclosedRecord,
    poisoned: poisonedRecord,
  },
  transactions,
};
writeFileSync("verification/studionet-e2e.json", JSON.stringify(result, null, 2) + "\n");
console.log(JSON.stringify(result, null, 2));
