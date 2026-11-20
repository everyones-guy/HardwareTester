#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: bash deployment/raspberry-pi/bootstrap.sh [--prefix DIRECTORY] [--plan FILE | --with-mqtt-fixture]

Install the Raspberry Pi inventory collector for the current user.
  --prefix DIRECTORY    User-owned installation directory (default: ~/.local)
  --plan FILE           Verify an exported provisioning plan before installing the collector
  --with-mqtt-fixture    Also install the mock valve and its Python dependency
  -h, --help            Show this help
EOF
}

prefix=""
plan=""
with_mqtt=false
while (($#)); do
    case "$1" in
        --prefix)
            if [[ -z "${2:-}" || "$2" == -* ]]; then
                printf 'Pass an installation directory after --prefix.\n' >&2
                exit 2
            fi
            prefix="$2"
            shift 2
            ;;
        --with-mqtt-fixture)
            with_mqtt=true
            shift
            ;;
        --plan)
            if [[ -z "${2:-}" || "$2" == -* ]]; then
                printf 'Pass a provisioning plan after --plan.\n' >&2
                exit 2
            fi
            plan="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            printf 'Unknown option: %s\n' "$1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

prefix="${prefix:-${HOME:?Set HOME or pass --prefix}/.local}"
script_dir="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
tools_dir="$script_dir/../../backend/tools"
if ! command -v python3 >/dev/null; then
    printf 'Install Python 3 using your Raspberry Pi OS package manager.\n' >&2
    exit 1
fi
if [[ ! -r "$tools_dir/capture_pi_inventory.py" ]]; then
    printf 'Run this from a HardwareTester checkout or the complete Pi bootstrap bundle.\n' >&2
    exit 1
fi
if [[ "$with_mqtt" == true && ! -r "$tools_dir/mqtt_fixture.py" ]]; then
    printf 'The mock valve is missing from the bootstrap bundle.\n' >&2
    exit 1
fi
if [[ -n "$plan" ]]; then
    if [[ "$with_mqtt" == true ]]; then
        printf 'The provisioning plan covers the inventory collector install.\n' >&2
        exit 2
    fi
    python3 "$tools_dir/pi_provisioning.py" check-bootstrap --plan "$plan" --source-root "$script_dir/../.."
fi

install_python_file() (
    local source="$1" destination="$2" mode="$3" temporary
    temporary="$(mktemp -- "$destination.XXXXXX")"
    trap 'rm -f -- "$temporary"' EXIT
    # Normalize Windows checkout line endings so the Linux shebang works.
    sed 's/\r$//' "$source" > "$temporary"
    chmod -- "$mode" "$temporary"
    mv -fT -- "$temporary" "$destination"
)

mkdir -p -- "$prefix/bin"
collector="$prefix/bin/hardware-tester-capture-pi"
install_python_file "$tools_dir/capture_pi_inventory.py" "$collector" 0755
printf 'Installed inventory collector. Capture with:\n  %q > pi-inventory.json\n' "$collector"

if [[ "$with_mqtt" == true ]]; then
    fixture_dir="$prefix/share/hardware-tester/mqtt-fixture"
    mkdir -p -- "$fixture_dir"
    if ! python3 -m venv "$fixture_dir/venv"; then
        printf 'The fixture needs a working Python venv. On Raspberry Pi OS, check that python3-venv is installed.\n' >&2
        exit 1
    fi
    fixture_python="$fixture_dir/venv/bin/python"
    "$fixture_python" -m pip install --disable-pip-version-check 'paho-mqtt==2.1.0'
    install_python_file "$tools_dir/mqtt_fixture.py" "$fixture_dir/mqtt_fixture.py" 0644
    printf 'Installed mock valve. Start it with your lab broker and a unique topic:\n'
    printf '  %q %q --broker BROKER_HOST --port 1883 --topic lab/YOUR_PI-demo-valve\n' \
        "$fixture_python" "$fixture_dir/mqtt_fixture.py"
fi
