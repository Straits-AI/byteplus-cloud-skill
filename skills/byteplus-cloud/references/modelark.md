# ModelArk

Use ModelArk for Seed text and multimodal inference, Seedream image generation,
Seedance video generation, and managed inference endpoints. Read
[seed-speech.md](seed-speech.md) instead for text-to-speech; Seed Speech is a
separate product with separate activation and credentials.

## Keep the control, inference, and voice planes separate

```text
Endpoint/model lifecycle -> BytePlus IAM credentials via bp, Cloud Control, or API
ModelArk inference        -> ModelArk API key via the current Ark SDK/API
Seed Speech TTS           -> Seed Speech application credentials and resource ID
```

Never use a ModelArk API key for Seed Speech or treat console OAuth credentials as
a ModelArk runtime key. Never place any runtime key in Terraform,
`byteplus.project.yaml`, source code, command output, or the agent transcript.

## Contents

- [Retrieve the current model contract](#retrieve-the-current-model-contract)
- [Handle model activation as a real gate](#handle-model-activation-as-a-real-gate)
- [Choose the control path](#choose-the-control-path)
- [Isolate a temporary GetApiKey bridge](#isolate-a-temporary-getapikey-bridge)
- [Run bounded inference smoke tests](#run-bounded-inference-smoke-tests)
- [Current official entry points](#current-official-entry-points)

## Retrieve the current model contract

Before every integration or smoke test:

1. Retrieve the current Model list, model-specific tutorial, API reference,
   pricing, and region-availability page.
2. Copy the exact public runtime model ID or inference endpoint ID documented for
   the selected API. Model IDs are versioned and volatile; never reuse an ID from
   this skill, an earlier run, or model memory.
3. Confirm the current regional base URL, request fields, minimum image/video
   sizes, task states, output URL lifetime, quotas, and billing behavior.
4. Discover current control-plane capability with `bp ark --help`, exact action
   help, and the official API catalog. Do not assume `bp ark` is complete.
5. Confirm account and model-service activation before planning a successful
   end-to-end claim.

Do not translate a catalog display name into a guessed provider-qualified runtime
ID. A live July 2026 validation showed that the documented public preset aliases
were accepted by `GetApiKey`, while a guessed provider-qualified alias returned
`NotFound.Presetendpoint`.

## Handle model activation as a real gate

Activation can include service terms and postpaid billing. Search the current
official action catalog for a supported activation API. If none exists, activation
is a UI-only account prerequisite, not an agent-executable cloud action.

- State the one minimal Activation Management step and its billing/legal effect.
- Require the account owner to accept terms and enable paid use; never click or
  accept those terms silently. If the owner explicitly authorizes the exact model,
  agreement, and pay-as-you-go boundary, UI automation may complete only that
  prerequisite; inference must still use the documented API or SDK.
- Keep **Select all** and automatic activation of future models off. Select only
  the exact approved model and verify the final row status rather than treating
  dialog closure as success.
- Do not create an endpoint, buy a resource pack, or substitute another model to
  evade this gate.
- Activation and deactivation can be eventually consistent. Poll or refresh with
  a bounded deadline until the row says `Activated` or `Not activated`.
- Resume automation after activation is verified, then rerun one bounded smoke
  call.

If a correctly formed call returns `ModelNotOpen`, recheck the runtime model ID,
region/base URL, project, key scope, and activation row once. If they match current
documentation, classify model activation as the blocker and stop retrying aliases.

A July 2026 acceptance run subsequently proved bounded Seed text, Seedream image,
and Seedance video paths after targeted activation. The exact versioned IDs belong
in that run's evidence ledger, not this reference: retrieve the current IDs again.
The then-current Seedance 2.0 tutorial required a prepaid resource pack, so the
no-prepaid test used Seedance 1.5 Pro instead.

## Choose the control path

- Repeatable endpoint infrastructure: current `bytepluscc_ark_endpoint` resource.
- Supported one-off/read operations: current `bp ark` action.
- Operations absent from `bp`: current ModelArk control-plane API/SDK.
- Inference and generation: current Ark SDK or documented compatible API.

For an endpoint lifecycle, retrieve the model/capacity contract, inspect existing
endpoints, plan throughput and cost, create/update, poll to a documented ready
state, run a bounded inference check, and verify metrics. Treat replacement or
deletion as disruptive and confirm downstream consumers first.

## Isolate a temporary `GetApiKey` bridge

`bp ark GetApiKey` returns secret material. Never invoke it through a terminal or
tool path whose stdout, stderr, debug trace, exception, or raw response reaches the
agent transcript.

For a user-approved disposable smoke test, use a local credential-isolating helper
that:

1. retrieves the current `GetApiKey` request schema and requests the narrowest
   documented model scope and shortest useful lifetime;
2. spawns `bp` with an argument array and explicit profile/region, capturing stdout
   privately inside the helper;
3. parses the key in memory and passes it directly to an SDK or HTTP client without
   a shell, command argument, global environment variable, or temporary file;
4. disables request/debug logging and never prints the key, authorization header,
   raw `bp` response, signed artifact URL, prompt, or generated content;
5. emits only sanitized request IDs, model ID, terminal status, usage counts,
   artifact metadata/digest, and non-secret expiration; and
6. revokes the key when a current API supports revocation, otherwise records its
   automatic expiry and exits promptly.

If such a helper must be written, test it offline with fake `bp` and HTTP fixtures
that use a canary secret. Assert that the canary appears in no stdout, stderr,
exception, file, or process argument before using the helper against BytePlus.

Do not use this temporary bridge as the deployed application's secret strategy.
Provision a long-term application key only through the current supported key
management surface, deliver it directly into a protected secret store, give the
agent only the secret reference, and define rotation/revocation ownership.

## Run bounded inference smoke tests

Run only after the exact low-cost test plan and any billable use are authorized.
Use benign, non-sensitive prompts and one request per modality.

### Seed text

- Use the current documented Seed runtime model ID and Responses or Chat API.
- Set the smallest useful supported output cap; for a smoke test, do not exceed 32
  output tokens when the selected API/model permits it.
- Verify the terminal response, non-empty output in memory, model identity, finish
  reason, and usage. Log no prompt, reasoning, or generated text.

### Seedream image

- Request one image with batch/streaming disabled, no reference input, and the
  smallest currently supported resolution and format.
- Download a URL response before it expires without printing or recording the
  signed URL. For base64 output, decode in memory instead of logging it.
- Verify magic bytes/content type, non-zero length, decoded dimensions, one
  successful image in usage, and a digest. Keep or remove the artifact according
  to the disclosed test plan.

### Seedance video

- Request one task using the shortest currently supported duration and lowest
  suitable resolution. Disable generated audio when the selected model supports
  that choice and audio is not under test.
- Poll with bounded backoff and a deadline across the currently documented states.
  Treat `succeeded`, `failed`, `cancelled`, and `expired` as terminal; do not leave
  an unbounded polling process.
- On success, download the video before its URL expires without exposing the URL.
  Verify container/magic, non-zero length, duration, resolution, decodability, and
  digest. Record usage without recording generated content.
- After a task ID exists, put task cleanup in an unconditional `finally` path.
  Success is not cleanup: do not return after artifact verification until the
  run-owned task record has been deleted through the current API and a fresh GET
  returns the documented absent status (normally `404` or `410`). On interruption,
  cancel or delete a queued task as documented. If cleanup cannot be proved, keep
  the exact task ID in the open resource ledger and do not report `CLEAN`.

For all modalities, preserve sanitized request/task IDs and errors. Delete local
disposable artifacts after verification unless the user asked to retain them.

If a model was inactive before an approved disposable test, return it to that
state afterward. Use Activation Management's `De-activate` action, accept the
model-specific close confirmation only within the approved cleanup scope, wait
for eventual consistency, refresh, and require a fresh `Not activated` row. Never
deactivate a model that was already active before the run.

## Current official entry points

- [ModelArk overview and quick start](https://docs.byteplus.com/en/docs/modelark/1099455)
- [Model list](https://docs.byteplus.com/en/docs/ModelArk/1330310)
- [Activation Management](https://docs.byteplus.com/en/docs/modelark/1159200)
- [API key management](https://docs.byteplus.com/en/docs/ModelArk/1361424)
- [GetApiKey API Explorer](https://api.byteplus.com/api-docs/view?action=GetApiKey&serviceCode=ark&version=2024-01-01)
- [Text generation with the Responses API](https://docs.byteplus.com/en/docs/modelark/1958520)
- [Image generation API](https://docs.byteplus.com/en/docs/ModelArk/1541523)
- [Create a video generation task](https://docs.byteplus.com/en/docs/ModelArk/1520757)
- [Retrieve a video generation task](https://docs.byteplus.com/en/docs/ModelArk/1521309)
- [Cancel or delete a video generation task](https://docs.byteplus.com/en/docs/ModelArk/1521720)
- [Common SDK examples](https://docs.byteplus.com/en/docs/ModelArk/1544136)
- [Cloud Control Ark endpoint resource](https://github.com/byteplus-sdk/terraform-provider-bytepluscc/blob/main/docs/resources/ark_endpoint.md)

Retrieve the current inference base URL and exact model IDs from these sources;
never freeze them into application code without configuration.
