from langchain_core.runnables import RunnablePassthrough
from chatbot.utils.cleaning import clean_query, clean_response
from src.config.logger import logger, ChainLoggerCallbacks

class ReasoningCypherChain:
    def __init__(self, llm, graph, cypher_prompt, qa_prompt, verbose=True, callbacks=None):
        self.llm = llm
        self.graph = graph
        self.cypher_prompt = cypher_prompt
        self.qa_prompt = qa_prompt
        self.verbose = verbose
        self.callbacks = callbacks
        self.create_chains()

    def create_chains(self):
        self.cypher_chain = (
            RunnablePassthrough.assign(
                formatted_prompt=lambda x: self.cypher_prompt.format(
                    schema=self.graph.schema,
                    question=x["query"]
                )
            )
            | RunnablePassthrough.assign(
                cypher_response=lambda x: self.llm.invoke([{"role": "user", "content": x["formatted_prompt"]}]).content
            )
            | RunnablePassthrough.assign(
                cleaned_cypher=lambda x: clean_query(x["cypher_response"])
            )
        )

        self.neo4j_chain = RunnablePassthrough.assign(
            neo4j_results=lambda x: self._safe_query(x["cleaned_cypher"])
        )

        self.qa_chain = (
            RunnablePassthrough.assign(
                qa_prompt=lambda x: self.qa_prompt.format(
                    question=x["query"],
                    context=x["neo4j_results"]
                )
            )
            | RunnablePassthrough.assign(
                qa_response=lambda x: self.llm.invoke([{"role": "user", "content": x["qa_prompt"]}]).content
            )
            | RunnablePassthrough.assign(
                cleaned_response=lambda x: clean_response(x["qa_response"]) 
            )
        )

    def _safe_query(self, cypher_query):
        try:
            if self.verbose:
                logger.info(f"Neo4j sorgusu: {cypher_query}")
            return self.graph.query(cypher_query)
        except Exception as e:
            logger.error(f"Cypher sorgusu hatası: {e}")
            return []

    def invoke(self, inputs):
        if self.verbose:
            logger.info(f"Girdi: {inputs}")

        cypher_result = self.cypher_chain.invoke(inputs)
        if "cypher_response" in cypher_result:
            logger.info(f"CYPHER response: {cypher_result['cypher_response']}")

        neo4j_result = self.neo4j_chain.invoke(cypher_result)
        final_result = self.qa_chain.invoke(neo4j_result)

        if "qa_response" in final_result:
            logger.info(f"QA response: {final_result['qa_response']}")

        return {
            "result": final_result["cleaned_response"],
            "intermediate_steps": [
                {"query": final_result["cleaned_cypher"]},
                {"context": final_result["neo4j_results"]}
            ]
        }
