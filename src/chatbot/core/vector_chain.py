import os
from langchain_neo4j import Neo4jVector
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_core.runnables import RunnablePassthrough
from langchain.schema import Document
from dotenv import load_dotenv
from src.config.logger import logger, ChainLoggerCallbacks 

load_dotenv()

class VectorSearchChain:
    def __init__(self, llm, graph, response_prompt, embeddings_model=None, verbose=True, callbacks=None):
        self.llm = llm
        self.graph = graph
        self.response_prompt = response_prompt
        self.embeddings = embeddings_model
        self.verbose = verbose
        self.callbacks = callbacks

        self.vector_store = Neo4jVector.from_existing_graph(
            embedding=self.embeddings,
            url=os.getenv('NEO4J_URI'),
            username=os.getenv('NEO4J_USERNAME'),
            password=os.getenv('NEO4J_PASSWORD'),
            database=os.getenv('NEO4J_DATABASE', 'neo4j'),
            index_name="chunk_embedding",
            node_label="Chunk",
            text_node_properties=["text"],
            embedding_node_property="embedding",
            retrieval_query="""
            RETURN node.text AS text,
                {
                    id: node.id,
                    order: node.order
                } AS metadata,
                score
            """
        )

        self.retriever = self.create_custom_retriever()

    def create_custom_retriever(self):
        class CustomRetriever:
            def __init__(self, vector_store, graph, verbose=False):
                self.vector_store = vector_store
                self.graph = graph
                self.verbose = verbose

            def get_relevant_documents(self, query, k=10):
                try:
                    similar_docs = self.vector_store.similarity_search(query, k=k)
                    enriched_docs = []

                    for doc in similar_docs:
                        chunk_id = doc.metadata.get("id")
                        cypher_query = """
                        MATCH (p:Paper)-[:HAS_CHUNK]->(c:Chunk)
                        MATCH (a:Author)-[:AUTHORED]->(p)
                        MATCH (p)-[:HAS_CODE]->(code:Code)
                        WHERE c.id = $chunk_id
                        RETURN p.name AS paper_name, 
                               p.publication_date AS publication_date,
                               p.arxiv_link AS arxiv_link,
                               p.pwc_link AS pwc_link,
                               p.abstract AS abstract,
                               COLLECT(DISTINCT code.link) AS github_links,
                               c.text AS chunk_text,
                               COLLECT(DISTINCT a.name) AS authors
                        LIMIT 1
                        """
                        try:
                            neo4j_result = self.graph.query(cypher_query, {"chunk_id": chunk_id})
                            if neo4j_result:
                                meta = neo4j_result[0]
                                doc.metadata.update({
                                    "paper_name": meta.get("paper_name", ""),
                                    "authors": meta.get("authors", []),
                                    "publication_date": meta.get("publication_date", ""),
                                    "arxiv_link": meta.get("arxiv_link", ""),
                                    "pwc_link": meta.get("pwc_link", ""),
                                    "abstract": meta.get("abstract", ""),
                                    "github_links": meta.get("github_links", [])
                                })
                        except Exception as e:
                            if self.verbose:
                                logger.warning(f"Döküman zenginleştirme hatası: {str(e)}")
                        enriched_docs.append(doc)

                    return enriched_docs
                except Exception as e:
                    logger.error(f"Retriever hatası: {str(e)}")
                    return []
            
        return CustomRetriever(self.vector_store, self.graph, self.verbose)


    def invoke(self, inputs):
        query = inputs.get("query", "")
        try:              
            relevant_docs = self.retriever.get_relevant_documents(query, k=5)
            context_parts = []
            source_docs = []
            
            for doc in relevant_docs:
                metadata = doc.metadata
                context_parts.append(f"""
                    Makale: {metadata.get('paper_name', 'Bilinmeyen')}
                    Yazarlar: {metadata.get('authors', 'Bilinmeyen')}
                    Tarih: {metadata.get('publication_date', 'Bilinmeyen')}
                    ArXiv: {metadata.get('arxiv_link', 'Yok')}
                    PWC: {metadata.get('pwc_link', 'Yok')}
                    GitHub: {metadata.get('github_links', 'Yok')}
                    İçerik: {doc.page_content}
                ---
                """)
          
                source_docs.append({
                    "paper_name": metadata.get("paper_name", ""),
                    "authors": metadata.get("authors", ""),
                    "publication_date": metadata.get("publication_date", ""),
                    "arxiv_link": metadata.get("arxiv_link", ""),
                    "pwc_link": metadata.get("pwc_link", ""),
                    "github_link": metadata.get("github_links", ""),
                    "chunk_text": doc.page_content,
                    "chunk_order": metadata.get("chunk_order", "")
                })


            full_context = "\n".join(context_parts)
            prompt_text = self.response_prompt.format(query=query, context=full_context)

            llm_response = self.llm.invoke([{"role": "user", "content": prompt_text}])
            
            answer = getattr(llm_response, 'content', str(llm_response))
     
            return {
                "result": answer,
                "intermediate_steps": [
                    {"query": query},
                    {"context": source_docs}
                ]
            }

        except Exception as e:
            logger.error(f"VectorSearchChain: Hata: {str(e)}")
            return {
                "result": f"Arama sırasında bir hata oluştu: {str(e)}",
                "intermediate_steps": [
                    {"query": query},
                    {"context": []}
                ]
            }
            