import asyncio
from argparse  import ArgumentParser

from .irc      import Bot
from .config   import load_config
from .checker  import loop

from ircrobots import ConnectionParams, SASLUserPass

async def main():
    parser = ArgumentParser(
        description="announce tor hidden service up/down status on IRC"
    )
    parser.add_argument("config")
    args   = parser.parse_args()

    config = load_config(args.config)
    host, port, tls = config.server

    params = ConnectionParams(config.nickname, host, port, tls)
    params.autojoin = [config.channel]

    if config.password:
        params.password = config.password
    if config.sasl:
        username, password = config.sasl
        params.sasl = SASLUserPass(username, password)

    successes: Dict[str, float] = {n: 0.0 for n in config.services.keys()}
    fails:     Dict[str, int] =   {n: 0   for n in config.services.keys()}

    bot = Bot(successes, fails)
    await bot.add_server("server", params)
    await asyncio.wait([
        loop(bot, config, successes, fails),
        bot.run()
    ])

if __name__ == "__main__":
    asyncio.run(main())

