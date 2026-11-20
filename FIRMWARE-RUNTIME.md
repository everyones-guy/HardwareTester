# Pinned firmware smoke tests

In the Workbench **Firmware** library, upload a reviewed release ZIP, then open
**Inspect release → Runtime profile**. Choose an inspected ELF executable and,
if needed, supply one smoke-test flag such as `--self-test`. Generate and export
the profile. For releases with a single executable the Workbench selects it on
open. The same release bytes, entry point, and argument produce the same lock.

The supported input is a bounded ZIP containing a Debian 12 `etc/os-release` or
`usr/lib/os-release`, one selected 64-bit little-endian glibc executable, and
its additional shared libraries. The profile names the architecture, exact
Debian image digest and observed `libc6` version. It records the ZIP digest,
selected file hashes, build manifest evidence, and resolution of transitive
`DT_NEEDED` edges. Matching library names from the ZIP are staged under their
locked names. The profile blocks unresolved dependencies, ambiguous matches
and path-based dependencies. For a missing name, supply the approved library
from the same release and ABI inside a replacement ZIP and inspect it again.

| ELF architecture | Docker platform | Allowlisted base image digest |
| --- | --- | --- |
| x86-64 | `linux/amd64` | `sha256:c67e92c8099ba22853ab4cfda7cfb494d253d6012ca82dee98ba8976772af018` |
| AArch64 | `linux/arm64` | `sha256:ec8534cda2cb30f29f44f23e135297af7a1496f2990fd8e4e84aa36b081a757a` |

The base library catalog comes from `ldconfig -p` in these official Debian
images. `dpkg-query -W libc6` reported `2.36-9+deb12u14` on both platforms. The
image digest pins the libraries supplied by the base. Source manifests are
available for review. Building from source and installing new dependencies
require separate trusted inputs.

## Preflight and smoke test

With the release and profile available locally, run from `backend` in an
installed Workbench Python environment. Use fresh report filenames.

```powershell
python -m tools.run_firmware_runtime --profile .\release.runtime.json `
  --bundle .\release.zip --report .\runtime-preflight.json
```

Preflight takes a private byte snapshot, checks the ZIP hash, reinspects the
files, and compares the regenerated lock with the export. It produces a JSON
report without Docker. A modified archive, edited lock, or blocked profile
returns exit 2.

On a local Linux Docker daemon or Docker Desktop in Linux mode, pre-cache the
specific official base with `docker pull --platform <platform> <baseImage>`
using the reviewed profile values. Then run only reviewed release bytes. Use
the SHA-256 from the approved release as the local approval value.

```powershell
python -m tools.run_firmware_runtime --profile .\release.runtime.json `
  --bundle .\release.zip --report .\runtime-smoke.json `
  --run --approved-sha256 <approved-release-sha256>
```

The Workbench only plans and exports. The CLI mounts the selected executable
and locked libraries read-only in a temporary non-root container with network
access disabled, all capabilities dropped, and CPU, memory, process, time and
output limits. The pinned glibc loader starts the executable. The CLI passes
the optional flag literally. Use a short smoke operation that exits. The JSON
report records the exact runtime command, program exit code and captured
output. The caller gets exit 1 for a failed runtime and 0 for a passing smoke
test. [Docker run reference](https://docs.docker.com/reference/cli/docker/container/run/) · [glibc loader invocation](https://sourceware.org/glibc/manual/latest/html_node/Dynamic-Linker-Invocation.html)

The lock covers file identities, ABI selection, and static library-name
resolution. A real smoke test is still needed for symbol versions, late-loaded
libraries, and program behavior. This layout supports one executable and its
linked libraries. Firmware services, additional runtime files, booting an OS
image, GPIO, timing guarantees, and physical peripherals require separate
planning and verification.
