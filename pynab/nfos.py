import gzip
import regex

import pynab.nzbs
import pynab.util

from pynab import log
from pynab.db import db_session, Release, NFO, Group, MetaBlack
from pynab.server import Server

NFO_MAX_FILESIZE = 50000

NFO_REGEX = [
    regex.compile('((?>\w+[.\-_])+(?:\w+-\d*[a-zA-Z][a-zA-Z0-9]*))', regex.I),
]


def attempt_parse(nfo):
    potential_names = []

    for regex in NFO_REGEX:
        result = regex.search(nfo)
        if result:
            potential_names.append(result.group(0))

    return potential_names


def get(nfo):
    """Un-gzips an NFO."""
    return gzip.decompress(nfo.data)


def process(limit=50, category=0):
    """Process releases for NFO parts and download them."""

    with Server() as server:
        with db_session() as db:
            query = db.query(Release).join(Group).filter(Release.nfo==None).filter(Release.nfo_metablack_id==None)
            if category:
                query = query.filter(Release.category_id==int(category))

            for release in query.order_by(Release.posted.desc()).limit(limit):
                found = False
                nzb = pynab.nzbs.get_nzb_details(release.nzb)

                if nzb:
                    nfos = []
                    if nzb['nfos']:
                        for nfo in nzb['nfos']:
                            for part in nfo['segments']:
                                if int(part['size']) > NFO_MAX_FILESIZE:
                                    continue
                                nfos.append(part)

                    if nfos:
                        for nfo in nfos:
                            try:
                                article = server.get(release.group.name, [nfo['message_id'], ])
                            except:
                                article = None

                            if article:
                                data = gzip.compress(article.encode('utf-8'))
                                nfo = NFO(data=data)
                                nfo.release = release
                                db.add(nfo)

                                log.info('nfo: [{}] - [{}] - nfo added'.format(
                                    release.id,
                                    release.search_name
                                ))
                                found = True
                                break

                    if not found:
                        log.warning('nfo: [{}] - [{}] - nfo not available'.format(
                            release.id,
                            release.search_name
                        ))
                        mb = MetaBlack(status='IMPOSSIBLE')
                        mb.nfo = release
                        db.add(mb)