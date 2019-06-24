#!/usr/bin/env python3
import daemon
import logging
import logging.handlers
import argparse
import re
from cinaptic.cinaptic.api.library.semantic.GraphBuilder import GraphBuilder
from cinaptic.cinaptic.api.library.semantic.Config import Config

logging.basicConfig()

file_logger = logging.FileHandler("app.log", "w")

logger = logging.getLogger()
logger.addHandler(file_logger)
logger.setLevel(logging.DEBUG)

def check_string(value):    
    ivalue = str(value).strip()
    regex = re.compile('^([a-zA-Z ]+)+$')
    if not regex.match(ivalue):
        raise argparse.ArgumentTypeError(
            "%s is an invalid string value" % value)
    return ivalue

def check_int(value):
    try:
        ivalue = int(value)
        if ivalue <= 0:
            raise argparse.ArgumentTypeError(
                "%s must be a positive integer" % value)
        return ivalue
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            "%s must be a positive integer" % value)

parser = argparse.ArgumentParser(description="Cinaptic Semantic Analizer")
parser.add_argument("keys", type=check_string,
                    help="Search keys for the knowledge graph")
parser.add_argument("-d", "--depth", type=check_int,
                    help="depth of the knowlegde graph")

config = Config().getParameters()
args = parser.parse_args()
config["keys"] = args.keys.strip()
if args.depth is not None:
    config["depth"] = int(args.depth)
with daemon.DaemonContext(files_preserve=[file_logger.stream.fileno()]):
    builder = GraphBuilder()
    builder.build(config)