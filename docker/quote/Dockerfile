FROM python:latest

LABEL Maintainer="athichart"

# The directory structure
# /home/app
# ├╴ config
# │   └╴Quotes.md
# ├╴ quote.py
WORKDIR /home/app
COPY src/config/Quotes.md ./config/Quotes.md
COPY src/quote.py ./
RUN pip install colorama

# Unlike the CMD command, ENTRYPOINT allows the command line parameter to be
# passed through the command that will be run in the container. For example,
# the command "./vocab.py -a" will be run in the container when we run
# "docker run --rm athichart/quote -a".
ENTRYPOINT [ "./quote.py", "config/Quotes.md" ]
