import json
from typing import Dict, List, Any
import os
import sys
from datetime import datetime
from pathlib import Path
from langchain_neo4j import Neo4jGraph
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import PAPERS_JSON, PROCESSED_DATA_DIR, PROCESSED_PAPERS_JSON

class Neo4jLoader:
    def __init__(self, uri: str, user: str, password: str):
        self.graph = Neo4jGraph(
            url=uri,
            username=user,
            password=password
        )

    def close(self):
        self.graph.close()

    def load_data(self, data_file: Path):
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print("🔄 Veritabanı hazırlanıyor...")
        self._create_constraints()
        
        print("📥 Node'lar yükleniyor...")
        self._load_nodes(data['nodes'])
        
        print("🔗 İlişkiler yükleniyor...")
        self._load_relationships(data['relationships'])
        
        print("✨ Yükleme tamamlandı!")

    def _create_constraints(self):
        """Gerekli constraint'leri oluştur"""
        constraints = [
            "CREATE CONSTRAINT paper_id IF NOT EXISTS FOR (p:Paper) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT code_id IF NOT EXISTS FOR (c:Code) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT dataset_id IF NOT EXISTS FOR (d:Dataset) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT task_id IF NOT EXISTS FOR (t:Task) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT method_id IF NOT EXISTS FOR (m:Method) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT author_id IF NOT EXISTS FOR (a:Author) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
            "CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS FOR (c:Chunk) ON (c.embedding) OPTIONS {indexConfig: {`vector.dimensions`: 384, `vector.similarity_function`: 'cosine'}}"
        ]
        
        for constraint in constraints:
            try:
                self.graph.query(constraint)
            except Exception as e:
                print(f"⚠️ Constraint oluşturulurken hata: {e}")

    def _load_nodes(self, nodes: Dict[str, List[Dict[str, Any]]]):
        """Tüm node tiplerini yükle"""
        
        # Papers
        for paper in nodes.get('papers', []):
            query = """
            MERGE (p:Paper {id: $id})
            SET p.name = $name,
                p.arxiv_link = $arxiv_link,
                p.abstract = $abstract,
                p.arxiv_id = $arxiv_id,
                p.pwc_link = $pwc_link,
                p.publication_date = $publication_date
            """
            self.graph.query(query, params=paper)

        # Codes
        for code in nodes.get('codes', []):
            query = """
            MERGE (c:Code {id: $id})
            SET c.name = $name,
                c.link = $link,
                c.star = $star
            """
            self.graph.query(query, params=code)

        # Datasets
        for dataset in nodes.get('datasets', []):
            query = """
            MERGE (d:Dataset {id: $id})
            SET d.name = $name,
                d.link = $link
            """
            self.graph.query(query, params=dataset)

        # Tasks
        for task in nodes.get('tasks', []):
            query = """
            MERGE (t:Task {id: $id})
            SET t.name = $name,
                t.link = $link
            """
            self.graph.query(query, params=task)

        # Methods
        for method in nodes.get('methods', []):
            query = """
            MERGE (m:Method {id: $id})
            SET m.name = $name,
                m.link = $link
            """
            self.graph.query(query, params=method)

        # Authors
        for author in nodes.get('authors', []):
            query = """
            MERGE (a:Author {id: $id})
            SET a.name = $name,
                a.link = $link
            """
            self.graph.query(query, params=author)

        # Chunks
        for chunk in nodes.get('chunks', []):
            query = """
            MERGE (c:Chunk {id: $id})
            SET c.text = $text,
                c.embedding = $embedding,
                c.order = $order
            """
            chunk_data = {
                'id': chunk['id'],
                'text': chunk['text'],
                'embedding': chunk['embedding'],  # Doğrudan numpy array olarak gönder
                'order': chunk.get('order', 0)
            }
            self.graph.query(query, params=chunk_data)

    def _load_relationships(self, relationships: List[Dict[str, str]]):
        """İlişkileri yükle"""
        for rel in relationships:
            query = """
            MATCH (from) WHERE from.id = $from
            MATCH (to) WHERE to.id = $to
            MERGE (from)-[r:`{}`]->(to)
            """.format(rel['type'])
            
            self.graph.query(query, params={'from': rel['from'], 'to': rel['to']})

def main():
    # Neo4j bağlantı bilgileri
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    
    data_path = PROCESSED_PAPERS_JSON
    
    if not data_path.exists():
        print(f"❌ Veri dosyası bulunamadı: {data_path}")
        return
    
    try:
        print(f"🚀 Neo4j'ye veri yükleme başlatılıyor...")
        loader = Neo4jLoader(uri, user, password)
        loader.load_data(data_path)
        print("✅ Veriler başarıyla yüklendi!")
    except Exception as e:
        print(f"❌ Veri yüklenirken hata oluştu: {e}")

if __name__ == "__main__":
    main()