from typing import List
from article.schemas import Article
from author.schemas import Author

class CatalogService():

    def __init__(self, neo4j_graph_client):
        self.neo4j_graph_client = neo4j_graph_client

    def create_base_node(self, username: str, catalog_base_name: str):
            
        query = """
            MERGE (cb:CatalogBase {name: $catalog_base_name})
            MERGE (u:User {username: $username})
            MERGE (cb)-[:OWNED_BY]->(u)
        """

        self.neo4j_graph_client.run(query, parameters={"catalog_base_name": catalog_base_name, "username": username})

    def delete_base_node(self, username: str, catalog_base_name: str):

        query = """
            MATCH (cb:CatalogBase {name: $catalog_base_name})-[:OWNED_BY]->(u:User {username: $username})
            DETACH DELETE cb
        """

        self.neo4j_graph_client.run(query, parameters={"catalog_base_name": catalog_base_name, "username": username})

    def create_extension_node(self, username: str, catalog_base_name: str, catalog_extension_name: str):

        query = """
            MATCH (cb:CatalogBase {name: $catalog_base_name})-[:OWNED_BY]->(u:User {username: $username})
            MERGE (ce:CatalogExtension {name: $catalog_extension_name})
            MERGE (ce)-[:EXTENDS]->(cb)
        """

        self.neo4j_graph_client.run(query, parameters={"catalog_base_name": catalog_base_name, "username": username, "catalog_extension_name": catalog_extension_name})

    def create_article_node(self, article: Article, authors: List[Author] ,inbound_citation_dois: List[str], outbound_citation_dois: List[str]):
        
        query = """
            MERGE (a:Article {doi: $article.doi})
            SET a.external_ids = $article.external_ids,
                a.s2ag_url = $article.s2ag_url,
                a.title = $article.title,
                a.abstract = $article.abstract,
                a.venue = $article.venue,
                a.year = $article.year,
                a.outbound_citation_count = $article.outbound_citation_count,
                a.inbound_citation_count = $article.inbound_citation_count,
                a.s2ag_influential_inbound_citation_count = $article.s2ag_influential_inbound_citation_count,
                a.is_open_access = $article.is_open_access,
                a.open_access_pdf_url = $article.open_access_pdf_url,
                a.fields_of_study = $article.fields_of_study,
                a.publication_venue = $article.publication_venue,
                a.publication_types = $article.publication_types,
                a.publication_date = $article.publication_date,
                a.journal = $article.journal
            WITH a, $author_names AS author_names
            UNWIND author_names AS author_name
            MATCH (au:Author)
            WHERE au.name = author_name
            MERGE (a)-[:AUTHORED_BY]->(au)
            WITH a, $inbound_citation_dois AS inbound_citation_dois
            UNWIND inbound_citation_dois AS inbound_citation_doi
            MATCH (c:Article)
            WHERE c.doi = inbound_citation_doi
            MERGE (c)-[:CITES]->(a)
            WITH a, $outbound_citation_dois AS outbound_citation_dois
            UNWIND outbound_citation_dois AS outbound_citation_doi
            MATCH (c:Article)
            WHERE c.doi = outbound_citation_doi
            MERGE (a)-[:CITES]->(c)

        """

        author_names = [author["name"] for author in authors]

        self.neo4j_graph_client.run(query, parameters={"doi": article["doi"], "article": article, "author_names": author_names, "inbound_citation_dois": inbound_citation_dois, "outbound_citation_dois": outbound_citation_dois})

    def create_author_node(self, author: Author):
        
        query = """
            MERGE (a:Author {name: $author_name})
            SET a.name = $author.name,
                a.s2ag_url = $author.s2ag_url,
                a.aliases = $author.aliases,
                a.affiliations = $author.affiliations,
                a.homepage = $author.homepage,
                a.paper_count = $author.paper_count,
                a.citation_count = $author.citation_count,
                a.h_index = $author.h_index
        """

        self.neo4j_graph_client.run(query, parameters={"author_name": author["name"], "author": author})

    def add_article_to_base(self, username, catalog_base_name, doi):

        query = """
            MATCH (a:Article), (cb:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE a.doi = $doi AND cb.name = $catalog_base_name AND u.username = $username
            MERGE (a)-[i:IN]->(cb)
        """

        self.neo4j_graph_client.run(query, parameters={"doi": doi, "catalog_base_name": catalog_base_name, "username": username})

    def add_article_to_extension(self, username, catalog_base_name, catalog_extension_name, doi):
            
            query = """
                MATCH (ce:CatalogExtension)-[e:EXTENDS]->(cb:CatalogBase)-[o:OWNED_BY]->(u:User), (a:Article)
                WHERE ce.name = $catalog_extension_name AND cb.name = $catalog_base_name AND u.username = $username AND a.doi = $doi
                MERGE (a)-[i:IN]->(ce)
                RETURN a, ce
            """
    
            self.neo4j_graph_client.run(query, parameters={"doi": doi, "catalog_base_name": catalog_base_name, "catalog_extension_name": catalog_extension_name, "username": username})

    def remove_article_from_base(self, username, catalog_base_name, doi):

        query = """
            MATCH (a:Article)-[i:IN]->(cb:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE a.doi = $doi AND cb.name = $catalog_base_name AND u.username = $username
            DELETE i
        """

        self.neo4j_graph_client.run(query, parameters={"doi": doi, "catalog_base_name": catalog_base_name, "username": username})

    def get_base_articles(self, username, catalog_base_name) -> List[Article]:
        
        query = """
            MATCH (a:Article)-[i:IN]->(c:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE c.name = $catalog_base_name AND u.username = $username
            RETURN a AS article
        """

        result = self.neo4j_graph_client.run(query, parameters={"catalog_base_name": catalog_base_name, "username": username})

        articles = [Article(**record["article"]) for record in result]

        return articles
    
    def get_extension_articles(self, username, catalog_base_name, extension_name) -> List[Article]:

        query = """
            MATCH (a:Article)-[i:IN]->(c:CatalogExtension)-[e:EXTENDS]->(cb:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE cb.name = $catalog_base_name AND u.username = $username AND c.name = $extension_name
            RETURN a AS article
        """

        result = self.neo4j_graph_client.run(query, parameters={"catalog_base_name": catalog_base_name, "username": username, "extension_name": extension_name})

        articles = [Article(**record["article"]) for record in result]

        return articles
    
    def check_if_article_in_base(self, username, catalog_base_name, doi) -> bool:
        
        query = """
            MATCH (a:Article)-[i:IN]->(c:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE c.name = $catalog_base_name AND u.username = $username AND a.doi = $doi
            RETURN a AS Article
        """.format(catalog_base_name=catalog_base_name, username=username, doi=doi)

        result = self.neo4j_graph_client.run(query, parameters={"catalog_base_name": catalog_base_name, "username": username, "doi": doi})

        if len(result) > 0:
            return True
        else:
            return False
        
    def check_if_base_exists(self, username, catalog_base_name) -> bool:
        
        query = """
            MATCH (c:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE c.name = $catalog_base_name AND u.username = $username
            RETURN c AS CatalogBase
        """

        result = self.neo4j_graph_client.run(query, parameters={"catalog_base_name": catalog_base_name, "username": username})

        if len(result) != 0:
            return True
        else:
            return False
        
    def check_if_extension_exists(self, username, base_name, extension_name) -> bool:
        
        query = """
            MATCH (ce:CatalogExtension)-[e:EXTENDS]->(cb:CatalogBase)-[o:OWNED_BY]->(u:User)
            WHERE ce.name = $extension_name AND cb.name = $base_name AND u.username = $username
            RETURN e AS CatalogExtension
        """

        result = self.neo4j_graph_client.run(query, parameters={"extension_name": extension_name, "base_name": base_name, "username": username})

        if len(result) != 0:
            return True
        else:
            return False
        
    def get_existing_articles(self, dois) -> bool:
        
        query = """
            MATCH (a:Article)
            WHERE a.doi IN $doi_list
            RETURN a AS article
        """

        result = self.neo4j_graph_client.run(query, parameters={"doi_list": list(dois)})

        articles = [Article(**record["article"]) for record in result]

        return articles
    
    def get_existing_authors(self, author_name_list) -> bool:

        query = """
            MATCH (a:Author)
            WHERE a.name IN $author_name_list
            RETURN a AS author
        """

        result = self.neo4j_graph_client.run(query, parameters={"author_name_list": author_name_list})

        authors = [Author(**record["author"]) for record in result]

        return authors