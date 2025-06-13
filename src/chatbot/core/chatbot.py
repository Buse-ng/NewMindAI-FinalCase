import os
import torch
from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph

from src.config.prompts import cypher_prompt, qa_prompt, vector_response_prompt, condense_prompt
from src.config.logger import logger, ChainLoggerCallbacks
from chatbot.core.reasoning_chain import ReasoningCypherChain
from chatbot.core.vector_chain import VectorSearchChain
from chatbot.utils.cleaning import clean_query, clean_response

from dotenv import load_dotenv

load_dotenv()


class AIMLChatbot:
    def __init__(self, llm_provider="OpenAI", model_name="gpt-4.1-nano-2025-04-14", temperature=0.1, search_type="Normal"):
        self.graph = None
        self.chain = None
        self.schema = None
        self.llm = None
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.temperature = temperature
        self.search_type = search_type

        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.groq_api_key = os.getenv('GROQ_API_KEY')

        if llm_provider == "OpenAI" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY bulunamadı. Lütfen .env dosyasını kontrol edin.")
        elif llm_provider == "Groq" and not self.groq_api_key:
            raise ValueError("GROQ_API_KEY bulunamadı. Lütfen .env dosyasını kontrol edin.")

        self.initialize_connections()

    def initialize_connections(self):
        try:
            self.graph = Neo4jGraph(
                url=os.getenv('NEO4J_URI'),
                username=os.getenv('NEO4J_USERNAME'),
                password=os.getenv('NEO4J_PASSWORD'),
                database=os.getenv('NEO4J_DATABASE', 'neo4j')
            )

            self.graph.refresh_schema()
            self.schema = self.graph.schema

            if self.llm_provider == "Groq" and self.groq_api_key:
                self.llm = ChatGroq(
                    api_key=self.groq_api_key,
                    model=self.model_name,
                    temperature=self.temperature,
                    max_tokens=4000
                )
            elif self.llm_provider == "OpenAI" and self.openai_api_key:
                self.llm = ChatOpenAI(
                    api_key=self.openai_api_key,
                    model=self.model_name,
                    temperature=self.temperature,
                    max_tokens=3000
                )
            else:
                raise ValueError("Geçerli API anahtarı bulunamadı.")

            self.memory = ConversationBufferMemory(
                return_messages=True,
                memory_key="chat_history",
                output_key="answer",
                input_key="question"
            )

            if self.search_type == "Reasoning":
                self.chain = ReasoningCypherChain(
                    llm=self.llm,
                    graph=self.graph,
                    cypher_prompt=cypher_prompt,
                    qa_prompt=qa_prompt,
                    verbose=True,
                    callbacks=ChainLoggerCallbacks()
                )
            elif self.search_type == "Vector Search":
                device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

                embeddings_model = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    model_kwargs={'device': device}
                )

                self.chain = VectorSearchChain(
                    llm=self.llm,
                    graph=self.graph,
                    response_prompt=vector_response_prompt,
                    embeddings_model=embeddings_model,
                    verbose=True,
                    callbacks=ChainLoggerCallbacks()
                )
            else:
                self.chain = GraphCypherQAChain.from_llm(
                    llm=self.llm,
                    graph=self.graph,
                    cypher_prompt=cypher_prompt,
                    qa_prompt=qa_prompt,
                    verbose=True,
                    callbacks=[ChainLoggerCallbacks()],
                    allow_dangerous_requests=True,
                    return_intermediate_steps=True,
                    return_direct=False,
                    chat_history=self.memory.load_memory_variables({}).get("chat_history", [])
                )

            self.question_rewriter_chain = condense_prompt | self.llm

        except Exception as e:
            logger.error(f"Initialization error: {str(e)}")

    def get_response(self, user_question):
        try:
            current_history = self.memory.load_memory_variables({})
            preprocessed_question = self._preprocess_query(user_question, current_history)

            chain_input = {
                "query": preprocessed_question,
                "chat_history": current_history.get("chat_history", [])
            }

            result = self.chain.invoke(chain_input)
            answer = result.get('result', 'Yanıt verilemedi.')
            intermediate_steps = result.get('intermediate_steps', [])
            cypher_query = intermediate_steps[0].get('query', '') if intermediate_steps else ''

            cypher_query = clean_query(cypher_query)

            self.memory.save_context({"question": user_question}, {"answer": answer})

            return {
                'answer': answer,
                'cypher_query': cypher_query,
                'success': True
            }
        except Exception as e:
            logger.error(f"Query error: {str(e)}")
            return {
                'answer': f'Hata: {str(e)}',
                'cypher_query': None,
                'success': False
            }

    def _preprocess_query(self, query, history_data):
        current_history = history_data.get("chat_history", [])
        
        chat_history_str = ""
        
        for msg in current_history:
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
            else:
                role = getattr(msg, "role", "user")
                content = getattr(msg, "content", "")
            chat_history_str += f"{role}: {content}\n"
        
        result = self.question_rewriter_chain.invoke({
            "chat_history": chat_history_str,
            "question": query
        })

        if hasattr(result, 'content'):
            standalone_question = result.content
        elif isinstance(result, dict):
            standalone_question = result.get("text", query)
        elif isinstance(result, str):
            standalone_question = result
        else:
            standalone_question = str(result)


        standalone_question = clean_response(standalone_question)
        return standalone_question.strip()
