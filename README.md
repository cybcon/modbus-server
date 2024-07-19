# Quick reference

Maintained by: [Michael Oberdorf IT-Consulting](https://www.oberdorf-itc.de/)

Source code: [GitHub](https://github.com/cybcon/modbus-server)

Container image: [DockerHub](https://hub.docker.com/r/oitc/modbus-server)

# Supported tags and respective `Dockerfile` links

* [`latest`, `1.3.2`](https://github.com/cybcon/modbus-server/blob/v1.3.2/Dockerfile)
* [`1.3.1`](https://github.com/cybcon/modbus-server/blob/v1.3.1/Dockerfile)
* [`1.3.0`](https://github.com/cybcon/modbus-server/blob/v1.3.0/Dockerfile)
* [`1.2.0`](https://github.com/cybcon/modbus-server/blob/v1.2.0/Dockerfile)

# What is Modbus TCP Server?

The Modbus TCP Server is a simple, in python written, Modbus TCP server.
The Modbus registers can be also predefined with values.

The Modbus server was initially created to act as a Modbus slave mock system
for enhanced tests with modbus masters and to test collecting values from different registers.

The Modbus specification can be found here: [PDF](https://modbus.org/docs/Modbus_Application_Protocol_V1_1b3.pdf)


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
"registers": {
  "description": "initial values for the register types",
  "zeroMode": false,
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
| `server.listenerAddress`                 | String  | The IPv4 Address to bound to when starting the server. `"0.0.0.0"` let the server listens on all interface addresses. |
| `server.listenerPort`                    | Integer | The TCP port number of the modbus slave to listen to.                                                                 |
| `server.tlsParams`                       | Object  | Configuration parameters to use TLS encrypted modbus tcp slave. (untested)                                            |
| `server.tlsParams.description`           | String  | No configuration option, just a description of the parameters.                                                        |
| `server.tlsParams.privateKey`            | String  | Filesystem path of the private key to use for a TLS encrypted communication.                                          |
| `server.tlsParams.certificate`           | String  | Filesystem path of the TLS certificate to use for a TLS encrypted communication.                                      |
| `server.logging`                         | Object  | Log specific configuration.                                                                                           |
| `server.logging.format`                  | String  | The format of the log messages as described here: https://docs.python.org/3/library/logging.html#logrecord-attributes |
| `server.logging.logLevel`                | String  | Defines the maximum level of severity to log to std out. Possible values are `DEBUG`, `INFO`, `WARN` and `ERROR`.     |
| `registers`                              | Object  | Configuration parameters to predefine registers.                                                                      |
| `registers.description`                  | String  | No configuration option, just a description of the parameters.                                                        |
| `registers.zeroMode`                     | Boolean | By default the modbus registers starts at 1 (`false`) but some implementation requires to start at 0 (`true`).        |
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
```

# Donate
I would appreciate a small donation to support the further development of my open source projects.

<a href="https://www.paypal.com/donate/?hosted_button_id=BHGJGGUS6RH44" target="_blank"><img src="https://raw.githubusercontent.com/stefan-niedermann/paypal-donate-button/master/paypal-donate-button.png" alt="Donate with PayPal" width="200px"></a>


# License

Copyright (c) 2020-2024 Michael Oberdorf IT-Consulting

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
