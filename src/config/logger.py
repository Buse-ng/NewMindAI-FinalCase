import logging
from langchain.callbacks.base import BaseCallbackHandler

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class ChainLoggerCallbacks(BaseCallbackHandler):
    def on_chain_start(self, serialized, inputs, **kwargs):
        logger.info(f"CHAIN BAŞLADI: {serialized}")
        logger.info(f"CHAIN GİRDİLERİ: {inputs}")

    def on_chain_end(self, outputs, **kwargs):
        logger.info(f"CHAIN BİTTİ: {outputs}")


