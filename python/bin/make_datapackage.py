#!/usr/bin/env python
"""
Basic CLI to create the knesset-data datapackages

Simple interface to the relevant classes that do the actual work
"""
from knesset_data.datapackages.root import RootDatapackage
import os
import logging
import sys
import argparse
import zipfile

parser = argparse.ArgumentParser(description='Make a datapackage containing all Knesset data')
parser.add_argument('--days', type=int, default=5, help='generate data for last DAYS days where relevant (default is last 5 days)')
parser.add_argument('-f', '--force', action="store_true", help='force to continue, ignoring errors / warnings')
parser.add_argument('-i', '--include', nargs="*", type=str, help="include only datapackages / resources that start with the given string/s")
parser.add_argument('-e', '--exclude', nargs="*", type=str, help="exclude datapackages / resources that start with the given string/s")
parser.add_argument('-c', '--committee-id', nargs="*", type=int, help="only make data for the given committee ids")
parser.add_argument('-d', '--debug', action="store_true", help="provide more information and debug details")
parser.add_argument('--http-proxy', type=str, help='url to SOCKS http proxy')
parser.add_argument('-z', '--zip', action="store_true", help="create the datapackage in a zip file")

args = parser.parse_args()

logLevel = logging.DEBUG if args.debug else logging.INFO
[logging.root.removeHandler(handler) for handler in tuple(logging.root.handlers)]
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(logging.Formatter("%(name)s:%(lineno)d\t%(levelname)s\t%(message)s"))
stdout_handler.setLevel(logLevel)
logging.root.addHandler(stdout_handler)
logging.root.setLevel(logLevel)
logger = logging.getLogger()

data_root = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
if not os.path.exists(data_root):
    os.mkdir(data_root)

datapackage_root = os.path.join(data_root, 'datapackage')

logger.info("Generating data for the last {} days".format(args.days))
logger.info("Datapackage will be written in directory {}".format(datapackage_root))

if not os.path.exists(datapackage_root):
    os.mkdir(datapackage_root)
elif len(os.listdir(datapackage_root)) > 0 and not args.force:
    raise Exception('datapackage directory must be empty')

proxies = {proxy_type: proxy_url for proxy_type, proxy_url in {
    'http': args.http_proxy
}.iteritems() if proxy_url}

if len(proxies) > 0:
    logger.info('using proxies: {}'.format(proxies))

RootDatapackage(datapackage_root).make(days=args.days,
                                       force=args.force,
                                       exclude=args.exclude,
                                       include=args.include,
                                       committee_ids=args.committee_id,
                                       debug=args.debug,
                                       proxies=proxies)

if args.zip:
    logger.info('creating datapackage.zip')
    zipf = zipfile.ZipFile(os.path.join(data_root, "datapackage.zip"), 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(datapackage_root):
        for file in files:
            real_file = os.path.join(root, file)
            rel_file = real_file.replace(data_root, "")
            zipf.write(real_file, rel_file)
    zipf.close()

logger.info('GREAT SUCCESS!')