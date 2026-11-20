# Bootstrap an additional Raspberry Pi

Use this bundle on a Raspberry Pi already running Raspberry Pi OS. It installs
the Hardware Tester inventory command in the current user's home directory.
For a blank device, use Raspberry Pi Imager to write the Raspberry Pi OS Lite
variant for that board. Give the Pi a unique hostname and configure SSH public
key access if deploying remotely. [Raspberry Pi Imager setup](https://www.raspberrypi.com/documentation/computers/getting-started.html)

## Install the inventory collector

Run both commands from the repository root on the Pi with your regular account.

```bash
bash deployment/raspberry-pi/bootstrap.sh
~/.local/bin/hardware-tester-capture-pi > pi-inventory.json
```

For a planned 64-bit Pi 3 Model B installation, add
`--plan /path/to/pi3b-provisioning-plan.json`. The installer checks the
bootstrap file hashes, running board and revision, kernel architecture,
and expected OS release before installing. Use the boot runner to verify
the image bytes separately. [Create a plan](../../RASPBERRY-PI.md#plan-and-verify-a-pi-3b-deployment)

For a Pi without a checkout, create and copy the same bundle from the repository
root on your workstation. Replace `USER@PI_HOST` with the Pi account you enrolled.
Verify and add the Pi's SSH host key to `known_hosts` before copying the bundle.

```sh
tar -czf hardware-tester-pi.tgz deployment/raspberry-pi/bootstrap.sh backend/tools/capture_pi_inventory.py backend/tools/pi_provisioning.py backend/tools/mqtt_fixture.py
scp -o StrictHostKeyChecking=yes hardware-tester-pi.tgz USER@PI_HOST:hardware-tester-pi.tgz
```

Run the following commands on the Pi to extract the bundle, install the
collector, and capture inventory.

```bash
mkdir -p "$HOME/hardware-tester-pi-bootstrap"
tar -xzf "$HOME/hardware-tester-pi.tgz" -C "$HOME/hardware-tester-pi-bootstrap"
bash "$HOME/hardware-tester-pi-bootstrap/deployment/raspberry-pi/bootstrap.sh"
~/.local/bin/hardware-tester-capture-pi > pi-inventory.json
```

Copy the JSON back to the workstation and import it into the workbench's
**Raspberry Pi** panel. Rerun the bootstrap with a newer bundle to update the tool.
Use `--prefix DIRECTORY` to install to a different user-owned location.
Default installation uses only local files and Python 3. It can be run again on
each already-provisioned Pi as its tools are updated. [Inventory and QEMU workflow](../../RASPBERRY-PI.md)

## Optional MQTT mock valve

Add `--with-mqtt-fixture` when a Pi should also host a software-only valve test
peer. This option needs Python's venv support (`python3-venv` on Raspberry Pi OS)
and access to a package index for the pinned Paho MQTT dependency. Start the
fixture in the foreground with the command printed by the bootstrap. Use a
private lab broker reachable from both the Pi and the Hardware Tester backend,
and choose a separate topic for each Pi.

For example, configure an MQTT valve endpoint
`mqtt://BROKER_HOST:1883/lab/YOUR_PI-demo-valve`, connect it, and run
**Connection & health** or **Control response**. The broker included on the
workstation publishes its port on loopback. The remote fixture exercises
MQTT commands and replies with an in-memory valve value. Its output cannot
measure or actuate a connected device. Use Ctrl+C to stop the foreground peer.
