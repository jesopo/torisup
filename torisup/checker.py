import asyncio, struct, time
from asyncio import StreamReader, StreamWriter
from sys     import stderr
from typing  import Dict, Optional

from irctokens     import build
from ircrobots     import Bot as BaseBot
from async_timeout import timeout as timeout_
from .config       import Config, Service

async def _recv(
        reader: StreamReader,
        length: int
        ) -> bytes:

    buff = b""
    while len(buff) < length:
        byte = await reader.read(1)
        buff += byte
    return buff

async def _socks4a(
        reader: StreamReader,
        writer: StreamWriter,
        target_name: str,
        target_port: int) -> bool:

    writer.write(struct.pack(
        "!BBH",
        0x04, # SOCKS version
        0x01, # connect command
        target_port,
    ))
    # this is an empty/invalid IP (0.0.0.1\0), used to
    # denote that we're going to request a DNS name instead
    writer.write(b"\x00\x00\x00\x01\x00")
    # null terminated DNS name
    writer.write(target_name.encode("idna") + b"\x00")
    await writer.drain()

    resp = await _recv(reader, 2)
    if not resp == b"\x00\x5a":
        return False

    # we don't actually need to parse these
    port = await _recv(reader, 2) # ([0]<<8) + [1]
    addr = await _recv(reader, 4) # inet_ntoa

    return True

async def _get_banner(
        target_name: str,
        target_port: int,
        send:        Optional[str],
        timeout:     int
        ) -> Optional[str]:

    try:
        async with timeout_(timeout):
            reader, writer = await asyncio.open_connection("localhost", 9050)
            socks = await _socks4a(reader, writer, target_name, target_port)

            if socks:
                buff = b""
                if send is not None:
                    writer.write(send.encode("utf8"))
                    await writer.drain()

                while not b"\n" in buff:
                    data = await reader.read(1024)
                    buff += data
                    if not data:
                        break
                return buff.split(b"\n", 1)[0].rstrip(b"\r").decode("utf8")
            else:
                stderr.write("failed to handshake\n")
    except asyncio.TimeoutError:
        stderr.write("overall timeout\n")
    except Exception as e:
        stderr.write(f"{type(e)} {str(e)}\n")

async def loop(
        bot:       BaseBot,
        config:    Config,
        successes: Dict[str, float],
        fails:     Dict[str, int]):

    async def _report(out: str):
        if bot.servers:
            server = list(bot.servers.values())[0]
            await server.send(build("PRIVMSG", [config.channel, out]))

    start = time.monotonic()

    while True:
        # make sure each connection attempt is at an INTERVAL
        # from when we first started up
        wait = config.interval-((time.monotonic()-start)%config.interval)
        if wait > 0:
            await asyncio.sleep(wait)

        for service_name in sorted(config.services.keys()):
            service = config.services[service_name]

            banner = await _get_banner(service.host, service.port, service.send, 20)
            match  = banner == service.read
            diff   = str(round(time.monotonic()-(successes[service_name]), 2))

            if match:
                if fails[service_name] > 1:
                    out = f"BACK: '{service_name}' reconnected after {fails[service_name]} failures"
                    if successes[service_name]:
                        out += f" (down {diff} seconds)"
                    await _report(out)
                elif not successes[service_name]:
                    await _report(f"GOOD: '{service_name}' is happy")

                fails[service_name]   = 0
                successes[service_name] = time.monotonic()

            else:
                if banner is not None:
                    await _report(f"WARN: '{service_name}' unexpected banner: {banner}")

                fails[service_name] += 1
                our_fails = fails[service_name]

                if our_fails == 1:
                    await _report(f"WARN: '{service_name}' failed to check in")
                elif our_fails == 2:
                    await _report(f"DOWN: '{service_name}' failed to check in twice")
                elif (our_fails % 5) == 0:
                    out = f"DOWN: '{service_name}' failing to check in after {our_fails} tries"
                    if successes[service_name]:
                        out += f" (last seen {diff} seconds ago)"
                    await _report(out)
