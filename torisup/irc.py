from typing    import Dict, List

from irctokens import build, Line
from ircrobots import Bot as BaseBot
from ircrobots import Server as BaseServer

HIGHLIGHT_SEP = [":", "," , ""]

class Server(BaseServer):
    def __init__(self,
            bot:  BaseBot,
            name: str,
            successes: Dict[str, float],
            fails:     Dict[str, int]):

        self._successes = successes
        self._fails     = fails
        super().__init__(bot, name)

    def set_throttle(self, rate: int, time: float):
        pass

    def line_preread(self, line: Line):
        print(f"{self.name} < {line.format()}")
    def line_presend(self, line: Line):
        print(f"{self.name} > {line.format()}")

    async def line_read(self, line: Line):
        if (line.command == "PRIVMSG" and
                line.source is not None and
                self.is_channel(line.params[0]) and
                not self.is_me(line.hostmask.nickname)):
            # it's a channel message from not-me

            n = self.nickname_lower
            highlights = [f"{self.nickname_lower}{s}" for s in HIGHLIGHT_SEP]
            channel    = line.params[0]
            message    = line.params[1]
            start, _, message = message.partition(" ")

            if self.casefold(start) in highlights:
                # speak when spoken to!

                command, _, args = message.partition(" ")
                command = command.lower()

                if command == "status":
                    statuses: Dict[bool, List[str]] = {True: [], False: []}
                    for service_name in sorted(self._fails.keys()):
                        up = self._fails[service_name] == 0
                        statuses[up].append(service_name)

                    async def _report(state: str, services: List[str]):
                        services_s = ", ".join(services)
                        await self.send(build("PRIVMSG", [channel, f"services {state}: {services_s}"]))

                    if statuses[True]:
                        await _report("up", statuses[True])
                    elif statuses[False]:
                        await _report("down", statuses[False])

class Bot(BaseBot):
    def __init__(self,
            successes: Dict[str, float],
            fails:     Dict[str, int]):

        self._successes = successes
        self._fails     = fails
        super().__init__()

    def create_server(self, name: str):
        return Server(self, name, self._successes, self._fails)

