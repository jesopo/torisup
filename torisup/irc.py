from irctokens import Line
from ircrobots import Bot as BaseBot
from ircrobots import Server as BaseServer

class Server(BaseServer):
    def line_preread(self, line: Line):
        print(f"{self.name} < {line.format()}")
    def line_presend(self, line: Line):
        print(f"{self.name} > {line.format()}")

class Bot(BaseBot):
    def create_server(self, name: str):
        return Server(self, name)

