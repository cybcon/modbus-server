# Quick reference

Maintained by: [Michael Oberdorf IT-Consulting](https://www.oberdorf-itc.de/)

Source code: [GitHub](https://github.com/cybcon/modbus-server)

Container image: [DockerHub](https://hub.docker.com/r/oitc/modbus-server)

<!-- SHIELD GROUP -->
[![][github-action-test-shield]][github-action-test-link]
[![][github-action-release-shield]][github-action-release-link]
[![][github-release-shield]][github-release-link]
[![][github-releasedate-shield]][github-releasedate-link]
[![][github-stars-shield]][github-stars-link]
[![][github-forks-shield]][github-forks-link]
[![][github-issues-shield]][github-issues-link]
[![][github-license-shield]][github-license-link]

[![][docker-release-shield]][docker-release-link]
[![][docker-pulls-shield]][docker-pulls-link]
[![][docker-stars-shield]][docker-stars-link]
[![][docker-size-shield]][docker-size-link]

# Supported tags and respective `Dockerfile` links

* [`latest`, `2.2.0`](https://github.com/cybcon/modbus-server/blob/v2.2.0/Dockerfile)
* [`2.1.0`](https://github.com/cybcon/modbus-server/blob/v2.1.0/Dockerfile)
* [`2.0.0`](https://github.com/cybcon/modbus-server/blob/v2.0.0/Dockerfile)
* [`1.4.1`](https://github.com/cybcon/modbus-server/blob/v1.4.1/Dockerfile)
* [`1.4.0`](https://github.com/cybcon/modbus-server/blob/v1.4.0/Dockerfile)
* [`1.3.2`](https://github.com/cybcon/modbus-server/blob/v1.3.2/Dockerfile)

# What is Modbus TCP Server?

The Modbus TCP Server is a simple, written in python, Modbus TCP server.
The Modbus registers can also be predefined with values.

The Modbus server was initially created to act as a Modbus slave mock system
for enhanced tests with modbus masters and to test collecting values from different registers.

The Modbus specification can be found here: [PDF](https://modbus.org/docs/Modbus_Application_Protocol_V1_1b3.pdf)

# Own Docker builds and version pinning

If you want to build your own container image with the [Dockerfile](./Dockerfile) you should know that the file uses version pinning to have a deterministic environment for the application.
This is a best practice and described in [Hadolint DL3018](https://github.com/hadolint/hadolint/wiki/DL3018).

The problem is, that Alpine Linux doesn't keep old versions inside the software repository. When software will be updated, the old (pinned) version will be removed and is so no longer available.
Docker builds will be successful today and fail tomorrow.

See also here: https://github.com/hadolint/hadolint/issues/464


The [Dockerfile](./Dockerfile) in this repo may have an not working stand of pinned versions. When you run in errors during your own build, please:

1. Update the versions inside the Dockerfile for your own
2. Don't create an issue in the Github repo, because this is a known issue


# QuickStart with Modbus TCP Server and Docker

Step - 1 : Pull the Modbus TCP Server

```bash
docker pull oitc/modbus-server
```

Step - 2 : Run the Modbus TCP Server

```bash
docker run --rm -p 5020:5020 oitc/modbus-server:latest
```

Step - 3 : Predefine registers

The default configuration file is configured to initialize every register with a `0x0000`.
To set register values, you need to create your own configuration file.

```bash
docker run --rm -p 5020:5020 -v ./server_config.json:/server_config.json oitc/modbus-server:latest -f /server_config.json
```

or you mount the config file over the default file, then you can skip the file parameter:

```bash
docker run --rm -p 5020:5020 -v ./server_config.json:/app/modbus_server.json oitc/modbus-server:latest
```

# Configuration
## Container configuration

The container reads some configuration via environment variables.

| Environment variable name    | Description                                                                        | Required     | Default value             |
|------------------------------|------------------------------------------------------------------------------------|--------------|---------------------------|
| `CONFIG_FILE`                | The configuration file that that should be used to build the initial Modbus slave. | **OPTIONAL** | `/app/modbus_server.json` |


## Parameter
Alternatively, the container can also be configured with a command line option `-f <file>` instead of an environment variable. By default, the script will use `/app/modbus_server.json`.


## Configuration file
### Default configuration file of the container

The `/app/modbus_server.json` file comes with following content:

```json
{
"server": {
  "listenerAddress": "0.0.0.0",
  "listenerPort": 5020,
  "protocol": "TCP",
  "tlsParams": {
    "description": "path to certificate and private key to enable tls",
    "privateKey": null,
    "certificate": null
    },
  "logging": {
    "format": "%(asctime)-15s %(threadName)-15s  %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s",
    "logLevel": "INFO"
    }
  },
  "persistence": {
    "enabled": false,
    "file": "/data/modbus_registers.json",
    "saveInterval": 30
  },
"metrics": {
  "enabled": false,
  "address": "0.0.0.0",
  "port": 9090,
  "path": "/metrics"
},
"registers": {
  "description": "initial values for the register types",
  "initializeUndefinedRegisters": true,
  "discreteInput": {},
  "coils": {},
  "holdingRegister": {},
  "inputRegister": {}
  }
}
```

### Field description

| Field                                    | Type    | Description                                                                                                           |
|------------------------------------------|---------|-----------------------------------------------------------------------------------------------------------------------|
| `server`                                 | Object  | Modbus slave specific runtime parameters.                                                                             |
| `server.listenerAddress`                 | String  | The IPv4 address to bind to, when starting the server. `"0.0.0.0"` lets the server listen on all interface addresses. |
| `server.listenerPort`                    | Integer | The port number of the modbus slave to listen to.                                                                     |
| `server.protocol`                        | String  | Defines if the server should use `TCP` or `UDP` (default: `TCP`)                                                      |
| `server.tlsParams`                       | Object  | Configuration parameters to use TLS encrypted modbus tcp slave. (untested)                                            |
| `server.tlsParams.description`           | String  | No configuration option, just a description of the parameters.                                                        |
| `server.tlsParams.privateKey`            | String  | Filesystem path of the private key to use for a TLS encrypted communication.                                          |
| `server.tlsParams.certificate`           | String  | Filesystem path of the TLS certificate to use for a TLS encrypted communication.                                      |
| `server.logging`                         | Object  | Log specific configuration.                                                                                           |
| `server.logging.format`                  | String  | The format of the log messages as described here: https://docs.python.org/3/library/logging.html#logrecord-attributes |
| `server.logging.logLevel`                | String  | Defines the maximum level of severity to log to std out. Possible values are `DEBUG`, `INFO`, `WARN` and `ERROR`.     |
| `server.persistence`                     | Object  | Configuration for the persistence layer to  automatically saved and restored after the server is restarted.           |
| `server.persistence.enabled`             | Boolean | If `true` the persistence will be enabled.                                                                            |
| `server.persistence.file`                | String  | The file to store the persistent data (if enabled).                                                                   |
| `server.persistence.saveInterval`        | Integer | The interval in seconds when to save the registers (this will be only done if there are changes).                     |
| `metrics`                                | Object  | Configuration of the Prometheus/Open Telemetry exporter.                                                              |
| `metrics.enabled`                        | Boolean | If `true` the metrics endpoint will be enabled.                                                                       |
| `metrics.address`                        | String  | The IPv4 address to bind to for the metrics endpoint. `0.0.0.0` lets the server listen on all interface addresses.    |
| `metrics.port`                           | Integer | TCP port of the HTTP metrics endpoint (default: `9090`).                                                              |
| `metrics.path`                           | String  | The URL path, where the endpoint serves the metrics (default: `/metrics`).                                            |
| `registers`                              | Object  | Configuration parameters to predefine registers.                                                                      |
| `registers.description`                  | String  | No configuration option, just a description of the parameters.                                                        |
| `registers.initializeUndefinedRegisters` | Boolean | If `true` the server will initialize all not defined registers with a default value of `0`.                           |
| `registers.discreteInput`                | Object  | The pre-defined registers of the register type "Discrete Input".                                                      |
| `registers.coils`                        | Object  | The pre-defined registers of the register type "Coils".                                                               |
| `registers.holdingRegister`              | Object  | The pre-defined registers of the register type "Holding Registers".                                                   |
| `registers.inputRegister`                | Object  | The pre-defined registers of the register type "Input Registers".                                                     |

### Pre-define Registers within the configuration file

Pre-define registers always starts with the register number. We use a json format as configuration file, so the "key" needs to be a string. So, the register number needs also to be a string. During server initialization, the json key that represents the register number will be converted to an integer.

As by the modbus spec, the "Discrete Input" and "Coils" registers contains a single bit. In the json configuration file, we use `true` or `false` as register values.

Example configuration of pre-defined registers from type "Discrete Input" or "Coils":
```
[..]
  "<register_type>": {
    "0": true,
    "1": true,
    "42": true,
    "166": false
  }
[..]
```

As by the modbus spec, the "Holding Registers" and "Input Registers" tables contains a 16-bit word. In the json configuration file, we use a hexadecimal notation, starting with `0x`, as register values.
With v1.2.0 of the modbus-server, you can also use integer values (0-65535) instead.

Example configuration of pre-defined registers from type "Holding Registers" or "Input Registers":
```
[..]
  "<register_type>": {
    "9": "0xAA00",
    "23": "0xBB11",
    "142": "0x1FC3",
    "2346": "0x00FF"
  }
[..]
```


## Configuration file examples

- [src/app/modbus_server.json](https://github.com/cybcon/modbus-server/blob/main/src/app/modbus_server.json)
- [examples/abb_coretec_example.json](https://github.com/cybcon/modbus-server/blob/main/examples/abb_coretec_example.json)
- [examples/test.json](https://github.com/cybcon/modbus-server/blob/main/examples/test.json)
- [examples/udp.json](https://github.com/cybcon/modbus-server/blob/main/examples/udp.json)


# Data persistence

The persistence layer enables all register changes (made by Modbus write accesses) to be automatically saved and restored after the server is restarted.

## Functionality

### When starting up
- The server checks whether a persistence file exists.
- **If YES**: Loads all register values from the file (initial configuration is skipped)
- **If NO**: Use the initial configuration from `modbus_server.json`

### During operation
- A background thread periodically saves the register data (default: every 30 seconds).
- Only changed data is saved (optimized for performance)
- Uses atomic writes (prevents data loss in case of crashes)

### When shutting down
- A final save is performed.
- All current register values are backed up.

## Configuration

### Enable persistence

Add the following section to your `modbus_server.json`:

```json
{
  "server": { ... },
  "persistence": {
    "enabled": true,
    "file": "/app/modbus_registers.json",
    "saveInterval": 30
  },
  "registers": { ... }
}
```

## Persistence file format

The persistence file is saved as JSON:

```json
{
  "discrete_inputs": {
    "0": false,
    "1": true,
    "100": true
  },
  "coils": {
    "0": true,
    "1": false,
    "50": true
  },
  "holding_registers": {
    "0": 1234,
    "1": 5678,
    "100": 42
  },
  "input_registers": {
    "0": 100,
    "1": 200
  }
}
```

**Hint:** Only registers with values ≠ 0 are stored (space-saving).

## Backup

For critical applications, you should create regular backups. When using Docker, you need to mount a local directory as volume to `/data` inside the container first.

```bash
# Cron-Job for daily backup
0 2 * * * cp /local/path/to/modbus_registers.json /local/backuppath/to/modbus_registers_$(date +\%Y\%m\%d).json
```

# Metrics endpoint

TODO



# Docker compose configuration

```yaml
services:
  modbus-server:
    container_name: modbus-server
    image: oitc/modbus-server:latest
    restart: always
    command: -f /server_config.json
    ports:
      - 5020:5020
    volumes:
      - ./server.json:/server_config.json:ro
      - ./data:/data:rw
```

# Donate
I would appreciate a small donation to support the further development of my open source projects.

<a href="https://www.paypal.com/donate/?hosted_button_id=BHGJGGUS6RH44" target="_blank"><img src="https://raw.githubusercontent.com/stefan-niedermann/paypal-donate-button/master/paypal-donate-button.png" alt="Donate with PayPal" width="200px"></a>


# License

Copyright (c) 2020-2026 Michael Oberdorf IT-Consulting

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

<!-- LINK GROUP -->
[docker-pulls-link]: https://hub.docker.com/r/oitc/modbus-server
[docker-pulls-shield]: https://img.shields.io/docker/pulls/oitc/modbus-server?color=45cc11&labelColor=black&style=flat-square
[docker-release-link]: https://hub.docker.com/r/oitc/modbus-server
[docker-release-shield]: https://img.shields.io/docker/v/oitc/modbus-server?color=369eff&label=docker&labelColor=black&logo=docker&logoColor=white&style=flat-square
[docker-size-link]: https://hub.docker.com/r/oitc/modbus-server
[docker-size-shield]: https://img.shields.io/docker/image-size/oitc/modbus-server?color=369eff&labelColor=black&style=flat-square
[docker-stars-link]: https://hub.docker.com/r/oitc/modbus-server
[docker-stars-shield]: https://img.shields.io/docker/stars/oitc/modbus-server?color=45cc11&labelColor=black&style=flat-square
[github-action-release-link]: https://github.com/cybcon/modbus-server/actions/workflows/release-from-label.yaml
[github-action-release-shield]: https://img.shields.io/github/actions/workflow/status/cybcon/modbus-server/release-from-label.yaml?label=release&labelColor=black&logo=githubactions&logoColor=white&style=flat-square
[github-action-test-link]: https://github.com/cybcon/modbus-server/actions/workflows/test.yaml
[github-action-test-shield-original]: https://github.com/cybcon/modbus-server/actions/workflows/test.yaml/badge.svg
[github-action-test-shield]: https://img.shields.io/github/actions/workflow/status/cybcon/modbus-server/test.yaml?label=tests&labelColor=black&logo=githubactions&logoColor=white&style=flat-square
[github-forks-link]: https://github.com/cybcon/modbus-server/network/members
[github-forks-shield]: https://img.shields.io/github/forks/cybcon/modbus-server?color=8ae8ff&labelColor=black&style=flat-square
[github-issues-link]: https://github.com/cybcon/modbus-server/issues
[github-issues-shield]: https://img.shields.io/github/issues/cybcon/modbus-server?color=ff80eb&labelColor=black&style=flat-square
[github-license-link]: https://github.com/cybcon/modbus-server/blob/main/LICENSE
[github-license-shield]: https://img.shields.io/badge/license-MIT-blue?labelColor=black&style=flat-square
[github-release-link]: https://github.com/cybcon/modbus-server/releases
[github-release-shield]: https://img.shields.io/github/v/release/cybcon/modbus-server?color=369eff&labelColor=black&logo=github&style=flat-square
[github-releasedate-link]: https://github.com/cybcon/modbus-server/releases
[github-releasedate-shield]: https://img.shields.io/github/release-date/cybcon/modbus-server?labelColor=black&style=flat-square
[github-stars-link]: https://github.com/cybcon/modbus-server
[github-stars-shield]: https://img.shields.io/github/stars/cybcon/modbus-server?color=ffcb47&labelColor=black&style=flat-square
