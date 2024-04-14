FROM python:latest

LABEL Maintainer="athichart"

# The directory structure
# /home/app
# ├╴ lib
# │   └╴ __init__.py
# ├╴ config
# │   └╴ vocabulary.yaml
# ├╴ vocab.py
# └╴ vocab
WORKDIR /home/app
COPY src/utils/__init__.py ./utils/__init__.py
COPY src/config/vocabulary.yaml ./config/vocabulary.yaml
COPY src/vocab.py ./
RUN pip install colorama pyyaml

# Unlike the CMD command, ENTRYPOINT allows the command line parameter to be
# passed through the command that will be run in the container. For example,
# the command "./vocab.py -a" will be run in the container when we run
# "docker run --rm athichart/vocalb -a".
ENTRYPOINT [ "./vocab.py" ]
