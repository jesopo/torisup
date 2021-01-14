import yaml
from dataclasses import dataclass
from typing      import Dict, Optional, Tuple

@dataclass
class Service(object):
    host: str
    port: int
    send: Optional[str]
    read: str

@dataclass
class Config(object):
    server:   Tuple[str, int, bool]
    nickname: str
    channel:  str
    password: Optional[str]
    interval: int
    sasl:     Optional[Tuple[str, str]]

    services: Dict[str, Service]

def load_config(filepath: str) -> Config:
    with open(filepath) as file:
        config_yaml = yaml.safe_load(file.read())

    server_s = config_yaml["server"]
    hostname, port = server_s.split(":", 1)
    tls      = port.startswith("+")
    if tls:
        port.lstrip("+")
    server   = (hostname, int(port), tls)

    nickname = config_yaml["nickname"]
    channel  = config_yaml["channel"]
    password = config_yaml.get("password", None)
    interval = config_yaml.get("interval", 120)

    sasl: Optional[Tuple[str, str]] = None
    if "sasl" in config_yaml:
        sasl = (config_yaml["sasl"]["username"], config_yaml["sasl"]["password"])

    services: Dict[str, Dict[str, str]] = {}
    for service_name in config_yaml["services"]:
        services[service_name] = Service(
            config_yaml["services"][service_name]["host"],
            config_yaml["services"][service_name]["port"],
            config_yaml["services"][service_name].get("send", None),
            config_yaml["services"][service_name]["read"]
        )

    return Config(
        server,
        nickname,
        channel,
        password,
        interval,
        sasl,
        services
    )
