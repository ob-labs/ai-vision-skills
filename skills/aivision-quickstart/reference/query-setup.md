# Query profile setup and troubleshooting

Reuse the confirmed profile, endpoint and space for the requested telemetry.
The endpoint must be reachable **from the machine running these commands**;
`localhost` points to this machine, not a remote deployment. Existing telemetry
needs neither redeployment nor a local Agent hook. Set `PROFILE` and inspect
`aiv auth status --profile "$PROFILE"`:

- A SpaceKey-only profile can query directly; it needs no email, account login
  or `space list`. If an account session is expired but its scoped query still
  succeeds, continue reading with the saved SpaceKey. Re-login only for account
  operations that need it.
- If the profile is absent, choose a new name. With an existing account, set
  `ENDPOINT` and `EMAIL` from confirmed details and use the hidden password prompt:

  ```bash
  : "${PROFILE:?Choose a profile name}" "${ENDPOINT:?Confirm platform URL}" \
    "${EMAIL:?Set the account email}"
  aiv auth login --profile "$PROFILE" --endpoint "$ENDPOINT" --email "$EMAIL"
  ```

  With only an authorized SpaceKey, confirm `SPACE_ID` and `AGENT_PRODUCT`, then
  use an interactive terminal to select key mode and enter the key at the hidden
  prompt (the empty environment override prevents accidentally importing a stale shell key):

  ```bash
  : "${PROFILE:?Choose a profile name}" "${ENDPOINT:?Confirm platform URL}" \
    "${SPACE_ID:?Confirm the key space}" "${AGENT_PRODUCT:?Confirm product}"
  AIVISION_SPACE_KEY= aiv auth login --profile "$PROFILE" --endpoint "$ENDPOINT" \
    --space "$SPACE_ID" --agent-product "$AGENT_PRODUCT" --space-key '' \
    --no-env-file --no-shell
  ```

For non-interactive use, reuse an already configured query profile. To create
a fresh SpaceKey-only profile without a TTY, set the confirmed values above and
`KEY_FILE` to the absolute path of the user's existing key file outside the
repository, with mode `600`. Read it only inside a subshell; the key stays out
of arguments and the parent shell's environment:

```bash
(
  set -eu
  set +x
  : "${PROFILE:?Choose a new profile name}" "${ENDPOINT:?Confirm platform URL}" \
    "${SPACE_ID:?Confirm the key space}" "${AGENT_PRODUCT:?Confirm product}" \
    "${KEY_FILE:?Set the protected key file absolute path}"
  case "$KEY_FILE" in
    /*) ;;
    *) echo 'KEY_FILE must be an absolute path' >&2; exit 1 ;;
  esac
  AIVISION_SPACE_KEY=$(cat "$KEY_FILE")
  [ -n "$AIVISION_SPACE_KEY" ] || { echo 'Key file is empty' >&2; exit 1; }
  export AIVISION_SPACE_KEY
  aiv auth login --profile "$PROFILE" --endpoint "$ENDPOINT" \
    --space "$SPACE_ID" --agent-product "$AGENT_PRODUCT" --space-key '' \
    --no-env-file --no-shell
)
```

An unreadable or empty file stops before login; the CLI validates the key and
its space before saving the new profile. No shell startup or env file is written.

If the existing query scope and key are confirmed, query directly. When an
account profile needs its space context established or changed, use its valid
account session to run `aiv space list --profile "$PROFILE"` and then, when
needed, `aiv space use --profile "$PROFILE" "$SPACE_ID"`. Re-login for these
management operations if that account session has expired.
Reuse that space's saved query key. If missing or rejected, import an authorized
key with `aiv key import --profile "$PROFILE"` (hidden prompt), or use
`--key-stdin < /secure/space-key.txt`. A permitted administrator may instead
create one with `aiv key create --profile "$PROFILE" --name cli`. Keep key values
out of command arguments and shared output. Inspect the installed command's
`--help` for optional modes. Use a separate profile for another platform; changing a query's
endpoint does not transfer its credentials.

Confirm `AGENT_PRODUCT` and, for an instance request, `AGENT_UUID` from the
existing platform Agent details or the user's known instance. Product and UUID
are different selectors. Pass the explicit product on every command below and
in the referenced recipes, even when a saved default exists. Do not use a local
`agent status` check to infer a remote instance's UUID.

Metadata verifies query access and schema, then a list/metrics request verifies
the chosen scope and bounds. On 401/403, check the key and its space; on 404,
check endpoint, space, product/UUID and endpoint support. Preserve metadata or
metrics failures as failures. Failed metadata does not erase an independently
verified query; use default fields while its schema/capability remains unknown.
An empty successful result means no matching data in that scope/window: verify
selectors, time and ingestion delay before proposing a separately recorded wider
window. It does not establish that collection is broken or require a new Agent.
