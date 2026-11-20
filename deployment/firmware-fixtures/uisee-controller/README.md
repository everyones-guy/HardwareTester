# Compiled UI controller fixture

`controller.cpp` provides a synthetic `setValveTarget` handler. It accepts a
percentage from 0 to 100, including decimal values, and stores the requested
target until it receives a new one or the process restarts. A read returns that
stored target. This fixture covers the compiled command and readback path. Valve
travel, feedback sensors, interlocks and timing require separate models or hardware.

The image compiles the checked-in source with pinned linux/amd64 bases. The
Python bridge starts only that fixed build output, reuses the Workbench MQTT
request decoder, and publishes correlated replies. Uploaded artifacts are not run
by this fixture. The controller container is non-root and read-only, with no host
devices, no added capabilities, and only an internal network shared with the lab
broker.

## Run locally

In PowerShell, start the fixture and broker in a disposable project from the
HardwareTester root. This uses automatically allocated host ports so the normal
workbench can remain up.

```powershell
$project = 'ht-compiled-demo-' + [guid]::NewGuid().ToString('N').Substring(0, 8)
$env:LAB_MQTT_PORT = '0'
$env:LAB_HTTP_PORT = '0'
$stack = @('-p', $project, '-f', 'docker-compose.yml', '-f', 'deployment/firmware-fixtures/uisee-controller/compose.yml')
docker compose @stack up --build -d --wait compiled-controller
docker compose @stack exec -T compiled-controller python smoke.py
docker compose @stack exec -T compiled-controller cat /app/bin/controller-elf.txt
docker compose @stack down --volumes
```

The smoke checks the compiled binary directly, then uses the same
`MQTTTransport` as Workbench to set 37.5%, read it back, reject 101%, and restore
the starting target. It prints the executable SHA-256. The ELF report includes
architecture, interpreter and dynamic dependencies. It was generated with
`readelf` during the build.

To use it through the normal Workbench, include `workbench` as a second service
in the `up` command. Run `docker compose @stack port workbench 80`, open the
reported loopback URL, and add an MQTT valve at
`mqtt://broker:1883/lab/compiled-valve`. The same saved valve tests can run on this
device. For a source mapping, `setValveTarget` calls the compiled handler via the
Workbench's MQTT `set` command. Its target is verified by a separate `read`.
