# poke

poke - A command line podcast client to subscribe and download podcasts.

# Install

## From source

pip install requests[socks] feedparser argparse

## Docker

``` shell
docker pull zblinuxfun/poke:latest
docker run --name poke -d -v /path/to/poke_path/:/poke zblinuxfun/poke:latest
```