from typing import NamedTuple, List, Optional
import elasticsearch


# URLs for elastic search queries
ELASTIC_SEARCH_URL_PORT_DEV = 'es5.cf.development.s2.dev.ai2'
ELASTIC_SEARCH_URL_PORT_PROD = 'es5.cf.production.s2.prod.ai2.in'

ES_CLIENTS = {
    "dev": None,
    "prod": None
}


def _get_es_client(use_prod=False):

    prod_or_dev = "prod" if use_prod else "dev"
    host = ELASTIC_SEARCH_URL_PORT_PROD if use_prod else ELASTIC_SEARCH_URL_PORT_DEV

    if ES_CLIENTS[prod_or_dev] is not None:
        return ES_CLIENTS[prod_or_dev]
    else:
        ES_CLIENTS[prod_or_dev] = elasticsearch.Elasticsearch(hosts=[{'host': host, 'port': 9200}], timeout=20)
        return ES_CLIENTS[prod_or_dev]


class PaperMetadata(NamedTuple):
    sha: str
    title: str
    venue: str
    year: int
    cited_by: int
    authors: List[str]

    def to_dict(self):
        return {
            "sha": self.sha,
            "title": self.title,
            "venue": self.venue,
            "year": self.year,
            "cited_by": self.cited_by,
            "authors": self.authors
        }


def get_paper_metadata(
    paper_sha: str,
    use_prod: bool = False
) -> Optional[PaperMetadata]:
    """
    Fetch a small metadata blob for a paper from Elasticsearch.

    paper_sha: str, required
        The paper id to search for.
    use_prod: bool, (default = False)
        Whether to use the production elastic search cluster.

    returns:
    PaperMetadata if the paper is found, otherwise None.
    """
    ES = _get_es_client(use_prod=use_prod)
    result = ES.search(
        index="paper_v3",
        body={
            "query": {"term": {"id": paper_sha}},
            "_source": ["title", "venue", "year", "numCitedBy", "authors"]
        },
    )

    if len(result["hits"]["hits"]) > 0:
        hit = result["hits"]["hits"][0]["_source"]
        return PaperMetadata(
            sha=paper_sha,
            title=hit["title"],
            venue=hit["venue"],
            year=int(hit["year"]),
            cited_by=int(hit["numCitedBy"]),
            authors=[a["name"] for a in hit["authors"]],
        )
    else:
        return None
