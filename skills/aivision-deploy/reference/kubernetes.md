# Kubernetes target

Depth for the Kubernetes path of the [`aivision-deploy`](../SKILL.md) skill. Use
it only when the user asked for Kubernetes: the target needs a cluster that
already exists (or one you bootstrap below), so it is never the default answer.

This file provides the executable Kubernetes recipe for this Skill, including
the local kind setup. Manual user instructions live in the
[Kubernetes guide](https://aivision.mintlify.site/en/deployment/kubernetes).
The matching released CLI embeds fixed product resources and pinned upstream
dependencies; a product source checkout is not required.
`aiv generate --target kubernetes` is a deprecated generic conversion, not this
product installation path: do not apply its output as a replacement for `cast`.
Keep target/context/namespace and existing physical names, selectors, DNS,
Secrets and PVCs across updates. New role selectors and
`app.kubernetes.io/component` labels use the bundled
[component mapping](operations.md#component-names-and-configuration);
old CLI aliases remain valid. Verify the installed CLI contains these source
changes before relying on the new names.

## Helm status

Helm is a committed future deployment path, but no product Chart or supported
Helm installation/upgrade commands are available in this delivery. Continue using
`aiv cast --target kubernetes`; installing a Helm client does not enable another
product path. No executable Helm values schema is provided.
Do not add speculative templates or change existing ownership labels, Secrets,
PVCs or saved identity to prepare a deployment for Helm.

## Datastore limitation

The fixed Kubernetes CLI deploys OceanBase CE through OB Operator. It does not
support bundled or external seekdb, `OB_BACKEND=seekdb`, or external OceanBase.
Use the Docker path for seekdb; Docker datastore vars do not apply to this target.

## Native Langfuse v1 limitation

The current fixed Kubernetes CLI does not accept
`AIVISION_NATIVE_TRACE_HISTORY_START` in `--var` or `--vars-file` and does not
inject it into the backend. The Docker history-start recipe therefore does not
enable v1 reads on this target. Do not claim native Langfuse v1 readiness from
the health checks below; report this capability as unavailable through the
current one-command Kubernetes path. Do not work around it by editing generated
manifests. Use the Docker path when v1 reads are required, if the user authorizes
that target. Kubernetes CLI support is separate from this Docker skill fix.

## Target requirements

Complete the shared [CLI check or installation](prerequisites.md#find-the-cli-before-installing)
before either branch, including making the installed command available on `PATH`.

This path targets a **Linux** host:

- `aiv` and `kubectl` installed; Docker is needed only to create a local kind
  cluster, and `gh` only for restricted release downloads
- a cluster with at least **4 CPU / 16Gi** RAM, **~140Gi** disk, **Kubernetes
  1.33–1.36**, admin rights and a default StorageClass
- Web and OTLP HTTP share the configured public Ingress address; the local
  kind mapping below exposes both at `127.0.0.1:5174`

The source lifecycle changes require matching images: backend
`/api/v1/ready`, diagnosis `/internal/readyz`, bounded shutdown, and the gateway
`/app/collector healthcheck --ready`, plus data-backend `/api/v1/ready` and
`/app/signoz healthcheck --ready`. A released `dev` tag alone does not establish those
capabilities. Do not use source manifests with older incompatible images.
Main's two-second `/app/collector healthcheck` liveness subcommand does not
provide readiness by itself. The readiness variant makes three checks with
two-second timeouts; Kubernetes allows ten seconds and keeps downstream checks
out of liveness.

The **4 CPU / 16Gi** figure is an evaluation scheduling floor, not a measured
production capacity. Current source `gauge` requires at least **3.4 CPU / 14Gi
free by Pod requests**, including one node with 2 CPU / 10Gi for the observer.
Application limits may burst beyond a 16Gi node's capacity. Allow additional
resources for Kubernetes, storage agents, upstream controllers and workload
peaks. The probe, replica and deadline limits below are configured budgets,
not a measured production capacity guarantee.

Source defaults use `TIMEOUT=30m` independently for each application stage.
Saved or explicit timeouts remain authoritative; choose a value beyond the
longest startup allowance (backend 1200s) plus rollout margin. Health probes do
not establish bootstrap or telemetry completion. Readiness failure removes
traffic without restarting the container; local liveness can trigger restart.
Backend, diagnosis and data-backend SQL failures should affect readiness without
causing a dependency restart loop. The data-backend endpoint runs a read-only
telemetry-store `SELECT 1` with a one-second deadline and returns HTTP 503 on
failure; its local `/api/v1/health` is not a readiness substitute. Older images
without `/api/v1/ready` must fail readiness rather than be treated as healthy.

All five application Deployments use one replica and `Recreate`; do not change
replicas, PVC names or the data backend's single SQLite writer to speed an
upgrade. Initialization Jobs run serially with a 900s deadline. Application
termination grace is 60s, except diagnosis at 300s; this does not promise
zero-loss completion under active work. Do not force-delete database or data
backend Pods to bypass the grace period. Track live startup, recovery, retained
data and load results separately from these configured budgets.

For anonymously accessible images, pass `--var IMAGE_AUTH=anonymous`. Otherwise,
pass an existing same-namespace image pull Secret via `IMAGE_PULL_SECRET`, or
use the cast prompt for an authorized GitHub username and PAT with `read:packages`
([prerequisites](prerequisites.md)). Later deployments reuse the stored credential;
host Docker login does not configure cluster pull credentials.

## Select the versioned service images

For an explicitly requested source deployment, use the matching source CLI and
validated image references, following [source build identity and verification](prerequisites.md#source-build-identity-and-verification).
Keep the same Kubernetes configuration boundaries below; no published release
manifest is required for that local validation.

For published builds, choose Release or Daily using the [shared channel flow](../SKILL.md#choose-release-or-daily)
and download the [matching CLI and verified manifest](prerequisites.md#resolve-the-version-and-download-matching-assets).
Restricted Daily uses an exact published `delivery-v<product-version>`
prerelease in `ob-labs/ai-vision-skills`; the current target
`delivery-v0.0.1-daily.20261028.2` selects Linux x64/ARM64 CLI archives and
both native Linux service-image architectures. Confirm the exact published
assets and actual CLI host/cluster-node support. Docker smoke checks do not
establish Kubernetes acceptance. Missing published assets or platform support
stop this flow. The earlier x86-only delivery retains its original bytes.
Copy `SIGNOZ_IMAGE`, `GATEWAY_IMAGE`, `BE_IMAGE`, `AGENTLENS_IMAGE`, `FE_IMAGE`
and `AIVISION_RELEASE_MANIFEST_BASE64` from its verified CE vars asset into one private
`aivision.k8s.vars.yaml`, retaining existing Kubernetes settings. These digest
references pin all five bundled services, including SigNoz. The release metadata
key supplies the installed product version to About without rewriting original
component build information.
For restricted Daily, service digest references come from the manifest under
`ghcr.io/ob-labs/ai-vision-skills/`; do not infer tags from the Release name.
Keep `NATIVE_PYTHON_RUNTIME: "true"` from native vars when supported by the
selected CLI's Kubernetes configuration, and verify support before deployment.
Do not copy Docker-only `OB_BACKEND` or its `OB_IMAGE`: Kubernetes uses its own
Operator-compatible OceanBase image. Do not copy the Docker history-start or
password keys, which this target does not accept. Keep the file outside source
control with mode `600` and use the same file, target, context and namespace
for the deployment. The release manifest's Docker smoke does not establish
Kubernetes acceptance.

## Branch A — a cluster already exists

Select the actual context and a node IP reachable by clients. Replace both
placeholders before running; keep the same target, context, and namespace on
subsequent commands:

```bash
kubectl config get-contexts
kubectl --context YOUR_CONTEXT get nodes
kubectl --context YOUR_CONTEXT get storageclass
aiv gauge --target kubernetes --context YOUR_CONTEXT --namespace aivision \
  --vars-file ./aivision.k8s.vars.yaml --var PUBLIC_HOST=YOUR_REACHABLE_NODE_IP --var PUBLIC_PORT=30080
aiv cast --target kubernetes --context YOUR_CONTEXT --namespace aivision \
  --vars-file ./aivision.k8s.vars.yaml --var PUBLIC_HOST=YOUR_REACHABLE_NODE_IP --var PUBLIC_PORT=30080
aiv status --target kubernetes --context YOUR_CONTEXT --namespace aivision
aiv logs --target kubernetes --context YOUR_CONTEXT --namespace aivision -n 80 backend
```

## Branch B — there is no cluster yet

For a local Linux trial without a cluster, install `kind` — the `command -v kind` guard skips
this when it is already on `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"; command -v kind >/dev/null || (set -eu; case "$(uname -m)" in x86_64|amd64) AIV_KIND_ARCH=amd64 ;; aarch64|arm64) AIV_KIND_ARCH=arm64 ;; *) echo 'Unsupported architecture' >&2; exit 1 ;; esac; AIV_KIND_TMP=$(mktemp -d); trap 'rm -rf -- "$AIV_KIND_TMP"' EXIT; cd "$AIV_KIND_TMP"; AIV_KIND_URL="https://github.com/kubernetes-sigs/kind/releases/download/v0.33.0/kind-linux-$AIV_KIND_ARCH"; curl -fLO "$AIV_KIND_URL"; curl -fLO "$AIV_KIND_URL.sha256sum"; sha256sum -c "kind-linux-$AIV_KIND_ARCH.sha256sum"; mkdir -p "$HOME/.local/bin"; install -m 755 "kind-linux-$AIV_KIND_ARCH" "$HOME/.local/bin/kind")
```

Pick the host directory that backs the cluster's local-path storage, then create
the `aivision` cluster. `--wait 5m` means this takes minutes on a first run, and
the resulting cluster binds the shared Web and OTLP HTTP ingress to `127.0.0.1:5174`:

```bash
AIV_K8S_DATA="$HOME/aiv-k8s-data"
```

```bash
(set -eu; case "$AIV_K8S_DATA" in *$'\n'*|*$'\r'*) echo 'Invalid data directory' >&2; exit 1 ;; esac; mkdir -p -- "$AIV_K8S_DATA"; AIV_K8S_DATA=$(cd -- "$AIV_K8S_DATA" && pwd -P); AIV_CGROUP=$(stat -fc %T /sys/fs/cgroup); printf "kind: Cluster\napiVersion: kind.x-k8s.io/v1alpha4\nnetworking:\n  apiServerAddress: 127.0.0.1\nnodes:\n- role: control-plane\n  extraMounts:\n  - hostPath: '%s'\n    containerPath: /var/local-path-provisioner\n  extraPortMappings:\n  - {containerPort: 30080, hostPort: 5174, listenAddress: 127.0.0.1}\n" "${AIV_K8S_DATA//\'/\'\'}" > aiv-kind.yaml; if [ "$AIV_CGROUP" != cgroup2fs ]; then printf 'containerdConfigPatches:\n- |-\n  [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]\n    SystemdCgroup = false\nkubeadmConfigPatches:\n- |-\n  apiVersion: kubelet.config.k8s.io/v1beta1\n  kind: KubeletConfiguration\n  cgroupDriver: cgroupfs\n' >> aiv-kind.yaml; fi; KIND_EXPERIMENTAL_PROVIDER=docker kind create cluster --name aivision --image kindest/node:v1.34.11 --config aiv-kind.yaml --wait 5m)
```

Then cast against the new context:

```bash
aiv cast --target kubernetes --context kind-aivision --namespace aivision \
  --vars-file ./aivision.k8s.vars.yaml
aiv status --target kubernetes --context kind-aivision --namespace aivision
aiv logs --target kubernetes --context kind-aivision --namespace aivision -n 80 backend
```

After registration or login, use **Help → About** or `/about` to compare frontend
and backend identity with the selected manifest, or the recorded source-build
metadata for local validation. A Daily displays its full
derived version; update checks still reference the latest stable Release.

When the cast prints `Deployment ready.`, open the **Web** address it reports —
`http://127.0.0.1:5174` on the local host.

Confirm ready Pods, bound PVCs, no persistent startup errors, and HTTP 200 from
the actual Web address. Bare `aiv status` targets Docker. A Web response does not
verify Agent collection; follow onboarding with an identifiable new record.
The current Kubernetes path has no Docker-style `destroy`/`redeploy` and no
external OceanBase support. Repeated casts may interrupt service; failures retain
resources without automatic rollback. Keep the [consistent restore set](operations.md#backup-and-rollback)
before an update.

Report Kubernetes checks separately from Docker. Schema validation and simulated
lifecycle tests do not prove a live cluster install, admission behavior or retained
data after an image upgrade. After an actual update compare organization identity,
credentials and PVC bindings, and report telemetry/readback only to the capability
level supported by this target.

## Native query recovery configuration

Matching fixed-CLI builds accept `BACKEND_QUERY_MODE=auto|raw` and `DATA_BACKEND_PROJECTION_MAINTENANCE_ENABLED=true|false`; defaults are `auto` and `true`. Legacy environment spellings remain aliases. Save changes in the original private vars file, retain context/namespace/PVCs and reapply the supported `cast --target kubernetes` entrypoint. The matching released CLI owns the embedded fixed deployment resources.

Gunicorn and projection maintenance share a backend supervisor; bootstrap Jobs retain explicit one-shot commands. Maintenance OFF persists across restarts and requires the [privileged recovery procedure](operations.md#kubernetes-recovery) after repair. Only that recovery process may receive the existing internal ingest key; do not add it to ordinary backend configuration. Verify complete fixed-window queries after rebuilding. This does not add database combinations, replicas, native-v1 history configuration or a claim of live Kubernetes acceptance.
