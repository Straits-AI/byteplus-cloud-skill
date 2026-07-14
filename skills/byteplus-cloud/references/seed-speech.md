# Seed Speech text-to-speech

Treat Seed Speech as a separate BytePlus product. It is not a ModelArk model and
does not use a ModelArk API key, a `bp login` OAuth session, or ordinary BytePlus
AK/SK as a drop-in runtime credential.

## Establish the current product contract

Before integration, retrieve the current Seed Speech Console Guide, TTS product
overview, billing page, Voice List, and the chosen HTTP or WebSocket API guide.
Confirm:

- account/region availability and service activation status;
- TTS generation/version and compatible stock voice;
- application ID, current access credential type, and required resource ID;
- endpoint, headers, packet/body schema, audio format, limits, quota, and billing;
- whether the selected credential/resource can use the chosen voice.

Do not copy header names, resource IDs, voice IDs, or protocol examples from model
memory. They can differ by TTS generation and change over time.

## Handle current-console activation and credentials

Discover `bp` and official API capability first. In the verified baseline, `bp`
exposed no Seed Speech/voice service and no programmatic activation or API-key
lifecycle. If the current official catalog still lacks one, treat these as
UI-only prerequisites:

1. activate the required Seed Speech service or trial;
2. obtain or create the current-console API key;
3. select the documented TTS resource ID; and
4. accept any service terms, billing method, prepaid package, or pay-as-you-go
   commitment.

For a new-console integration, do not invent a legacy application or require an
App ID. A live July 2026 activation automatically created one long-lived default
API key. The legacy console still uses an application ID and access token, so first
identify which console and authentication contract the account actually uses.

Activation and paid terms are account-owner decisions. Give the owner the exact
Speech Console Guide link and minimal steps, but never accept terms, start billing,
create a prepaid commitment, or reveal/copy the initial secret silently. If the
owner has explicitly approved the exact trial/pay-as-you-go service and terms, UI
automation may complete that prerequisite. Resume the agent-executable workflow
through the documented data-plane API afterward.

The new console may offer a broad cross-service migration or authorization prompt.
Close it unless the user separately approves that migration; it is not required
for one bounded TTS 2.0 call.

Do not create a general IAM access key as a workaround. Do not reuse a ModelArk
key; successful ModelArk activation says nothing about Seed Speech activation.

## Keep credentials outside the transcript

App ID and resource ID may be recorded as non-secret application configuration
when the current documentation classifies them that way. Treat every access token,
API key, secret key, and authorization header as secret.

- Have the owner place the access credential directly into an ignored local secret
  file, protected environment injection, or deployment secret store without
  pasting it into chat. For a disposable local smoke test, use a mode-`0600` file
  and remove it immediately after the process exits.
- Give the agent only the environment-variable name or secret-manager reference.
- Never print credential-bearing headers, raw request bodies, base64 audio, or
  complete error/debug traces.
- If browser automation must transfer a new-console key into protected local
  storage, locate the exact API-key value cell before revealing it. After reveal,
  never capture a screenshot, DOM snapshot, whole-row text, clipboard contents,
  or raw locator result in tool output. Write the value inside the protected
  browser/runtime boundary, emit only validation booleans and length, hide it,
  and clear the runtime after use. If the browser surface cannot guarantee this
  boundary, stop and have the owner place the key in the protected file directly.
- Keep application and credential rotation/deletion ownership explicit. Deleting
  a shared app or key is destructive and requires exact approval.

## Run a bounded TTS smoke test

After activation and cost authorization:

1. Select one current stock voice compatible with the application's TTS resource.
2. Synthesize one short, benign phrase through either the documented
   unidirectional HTTP flow or bidirectional WebSocket flow. Do not add voice
   replication unless explicitly requested.
3. Write the returned audio to a mode-protected temporary file without logging
   raw chunks or base64.
4. Record only sanitized request ID, protocol status, audio format, byte length,
   duration, sample rate/channels, and digest.
5. Verify magic/content type, non-zero duration, and decoding with an available
   media probe. An HTTP/WebSocket success alone is not proof of audible output.
6. Remove the disposable audio file after verification unless the user requests
   it. Delete a test-only application or credential only when it was created by
   this run and deletion was explicitly approved; otherwise report ownership.

For the current TTS 2.0 unidirectional contract, the bundled helper keeps the key
and audio out of output and emits only sanitized verification evidence:

```bash
python3 <skill-dir>/scripts/seed_speech_smoke.py \
  --api-key-file /path/to/owner-only.key \
  --text 'Hi.'
```

It uses the currently documented `seed-tts-2.0` resource, stock English Tim
voice, fixed app-key header, terminal code `20000000`, and MP3 validation. Retrieve
the current API guide before use and patch the helper if that contract changed.

## Revoke and restore disposable state

The current console does not allow the API key selected for the default resource
to be disabled or deleted individually. Do not create an endless rotation of
replacement keys just to remove the selected key.

- If the service/key existed before the run, preserve them and report that the
  shared credential was not changed.
- If a secondary run-owned key is not selected, disable it, verify the disabled
  state, delete it, and verify absence.
- If activation created the default key solely for this approved disposable run,
  unsubscribe the run-owned service, confirm the warning only within the approved
  cleanup scope, refresh, and require `Not activated`. Remove every local key
  reference. Do not reactivate the service merely to inspect the now-inaccessible
  key table.

For deployed applications, inject the credential through the platform's protected
secret mechanism and keep App ID/resource ID configurable. Verify one real call
from the deployed workload, then confirm usage/metrics and failure handling without
capturing spoken content or authorization data.

## Current official entry points

- [Seed Speech documentation](https://docs.byteplus.com/en/docs/byteplusvoice)
- [Speech Console Guide](https://docs.byteplus.com/en/docs/byteplusvoice/Speech_Console_Guide)
- [TTS 2.0 overview](https://docs.byteplus.com/en/docs/byteplusvoice/texttospeechv2)
- [TTS billing](https://docs.byteplus.com/en/docs/byteplusvoice/TTS_Billing)
- [Voice List](https://docs.byteplus.com/en/docs/byteplusvoice/voicelist)
- [Unidirectional streaming TTS over HTTP](https://docs.byteplus.com/en/docs/byteplusvoice/unidirectional_tts_http)
- [Bidirectional streaming TTS over WebSocket](https://docs.byteplus.com/en/docs/byteplusvoice/streaming_tts)
