from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import numpy as np
import torch
import fitz  # PyMuPDF
import os

class LocalChunker:
    """
    Metin parçalama (chunking) sınıfı.
    Hem token-bazlı hem de semantik-bazlı parçalama yapabilir.
    """
    
    def __init__(self, embeddings, chunk_size=500):
        """
        Chunker sınıfı başlatma
        
        Args:
            embeddings: Embedding modeli (HuggingFaceEmbeddings gibi)
            chunk_size: Her chunk'ın maksimum boyutu
        """
        self.embeddings = embeddings
        self.chunk_size = chunk_size
        
        # Token bazlı bölme için
        self.token_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        # Semantic bölme için
        self.semantic_splitter = SemanticChunker(
            embeddings=embeddings
        )

    def split_text_by_tokens(self, text):
        """
        Metni token-bazlı parçalara böl
        
        Args:
            text: Parçalanacak metin
            
        Returns:
            list: Metin parçaları listesi
        """
        print(f"🧩 Token-bazlı bölme yöntemi seçildi")
        return self.token_splitter.split_text(text)

    def split_text_by_semantic(self, text):
        """
        Metni semantik-bazlı parçalara böl
        
        Args:
            text: Parçalanacak metin
            
        Returns:
            list: Metin parçaları listesi
        """
        print(f"🧠 Semantik-bazlı bölme yöntemi seçildi")
        return self.semantic_splitter.split_text(text)
    
    def split_text(self, text, page_count=None):
        """
        Metni parçalara böl. Sayfa sayısına veya metin uzunluğuna göre
        token-bazlı veya semantik-bazlı parçalama yöntemini otomatik seçer.
        
        Args:
            text: Parçalanacak metin
            page_count: Sayfa sayısı (biliniyorsa)
            
        Returns:
            list: Metin parçaları listesi
        """
        if page_count is None:
            print(f"ℹ️ Sayfa sayısı bilinmiyor")
            if len(text.split()) > 2000:  # Yaklaşık 10 sayfa
                return self.split_text_by_tokens(text)
            else:
                return self.split_text_by_semantic(text)
        else:
            print(f"📊 Sayfa sayısı: {page_count}")
            if page_count <= 50:
                return self.split_text_by_semantic(text)
            else:
                return self.split_text_by_tokens(text)
