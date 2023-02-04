from neo4j_client import Neo4jClient
from article.serializers import ArticleSerializer
from author.serializers import AuthorSerializer

class Neo4jGraphClient(Neo4jClient):

    def create_article_nodes_batch(self, article_set):

        article_list = []

        for article in article_set:
            
            article_list.append(dict(ArticleSerializer(article).data))

        with self.driver.session() as session:
            session.execute_write(Neo4jGraphClient._create_article_nodes_batch, article_list)

    def _create_article_nodes_batch(tx, article_list):

        tx.run("""
            WITH $batch AS batch
            UNWIND batch AS article
            CREATE (p:Article)
            SET p += article;
        """, batch=article_list)

    def create_author_nodes_batch(self, author_set):

        author_list = []

        for author in author_set:
            author_list.append(dict(AuthorSerializer(author).data))

        with self.driver.session() as session:
            session.execute_write(Neo4jGraphClient._create_author_nodes_batch, author_list)

    def _create_author_nodes_batch(tx, author_list):

        tx.run("""
            WITH $batch AS batch
            UNWIND batch AS author
            CREATE (p:Author)
            SET p += author;
        """, batch=author_list)

    def create_citation_edges_batch(self, citation_set, batch_size=500):

        citation_list = []

        for citation in citation_set:
            citation_list.append({"citer": citation[0], "citee": citation[1], "type": "cites"})

        batches = [citation_list[x:x+batch_size] for x in range(0, len(citation_list), batch_size)]

        with self.driver.session() as session:
            i = 0
            for batch in batches:
                i += 1
                print("Citation batch " + str(i) + " of " + str(len(batches)))
                session.execute_write(Neo4jGraphClient._create_citation_edges_batch, batch)

    def _create_citation_edges_batch(tx, citation_list):

        citation_entities = []

        for citation in citation_list:
            citation_entities.append({"citer": citation["citer"], "citee": citation["citee"], "type": "cites"})

        tx.run("""
            WITH $batch AS batch
            UNWIND batch AS citation
            MATCH (citer) WHERE citer.DOI = citation.citer
            MATCH (citee) WHERE citee.DOI = citation.citee
            CREATE (citer)-[:Cites]->(citee)
        """, batch=citation_entities)

    def create_authorship_edges_batch(self, authorship_set, batch_size=500):

        authorship_list = []

        for authorship in authorship_set:
            authorship_list.append({"author": authorship[0], "article": authorship[1], "type": "authored"})

        batches = [authorship_list[x:x+batch_size] for x in range(0, len(authorship_list), batch_size)]

        with self.driver.session() as session:
            i = 0
            for batch in batches:
                i += 1
                print("Authorship batch " + str(i) + " of " + str(len(batches)))
                session.execute_write(Neo4jGraphClient._create_authorship_edges_batch, batch)

    def _create_authorship_edges_batch(tx, authorship_list):

        authorship_entities = []

        for authorship in authorship_list:
            authorship_entities.append({"author": authorship["author"], "article": authorship["article"], "type": "author_of"})

        tx.run("""
            WITH $batch AS batch
            UNWIND batch AS authorship
            MATCH (author) WHERE author.name = authorship.author
            MATCH (article) WHERE article.DOI = authorship.article
            CREATE (author)-[:Author_of]->(article)
        """, batch=authorship_entities)

    def create_coauthorship_edges(self):
            
        with self.driver.session() as session:
            session.execute_write(Neo4jGraphClient._create_coauthorship_edges)

    def _create_coauthorship_edges(tx):

        tx.run("""
                call{
                    match (a1:Author)-->(:Article)<--(a2:Author)
                    where a1.name < a2.name and a1 <> a2 
                    return a1 as a1, a2 as a2, [(a1)-->(p:Article)<--(a2)|p.DOI] as L
                }
                merge (a1)-[c:Coauthorship]->(a2)
                set c.weight = size(L)
                set c.coauthored_paper_DOIS = L
            """)
    