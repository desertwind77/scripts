FROM python:latest

LABEL Maintainer="athichart"

# The directory structure
# /home/app
# ├╴ config
# │   └╴ vocabulary.yaml
# ├╴ vocab.py
WORKDIR /home/app
COPY src/config/vocabulary.yaml ./config/vocabulary.yaml
COPY src/vocab.py ./
RUN pip install colorama pyyaml

# Unlike the CMD command, ENTRYPOINT allows the command line parameter to be
# passed through the command that will be run in the container. For example,
# the command "./vocab.py -a" will be run in the container when we run
# "docker run --rm athichart/vocalb -a".
ENTRYPOINT [ "./vocab.py", "config/vocabulary.yaml" ]
