# torisup
IRC bot to announce up/down status for Tor hidden services

## configuring

> $ cp config.example.yaml config.yaml

edit values as appropriate. `send` in `services` is (optional) data to send to the server, `read` is what the first line we read should be.

## running

> $ python3 -m torisup config.yaml
