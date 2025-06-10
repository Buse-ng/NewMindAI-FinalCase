from bs4 import BeautifulSoup
from urllib.parse import urljoin
import hashlib
from datetime import datetime
from typing import Dict, List, Any
import requests
import re
import json
import os

class PapersWithCodeScraper:
    def __init__(self):
        self.nodes = {
            'papers': {}, 'codes': {}, 'datasets': {},
            'tasks': {}, 'methods': {}, 'authors': {}, 'chunks': {}
        }
        self.relationships = []
        self.base_url = "https://paperswithcode.com"

    def generate_id(self, text: str, prefix: str = "") -> str:
        if not text:
            timestamp_hash = hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:8]
            return f"{prefix}_empty_{timestamp_hash}"
        clean_text = re.sub(r'[^\w\s-]', '', text.lower().strip())
        hash_obj = hashlib.md5(clean_text.encode())
        return f"{prefix}_{hash_obj.hexdigest()[:8]}"

    def extract_stars(self, text: Any) -> int:
        if text is None:
            return 0
        try:
            match = re.search(r'\d[\d,]*', str(text))
            if match:
                return int(match.group(0).replace(',', ''))
            return 0
        except Exception:
            return 0
         
    def extract_arxiv_id(self, url: str) -> str:
        if not url: return ""
        match = re.search(r'(\d{4}\.\d{4,5}(v\d+)?)', url)
        return match.group(1) if match else ""

    def parse_paper_html(self, html_content: str, pwc_url: str = "") -> Dict[str, Any]:
        soup = BeautifulSoup(html_content, 'html.parser')
        paper_data = self.extract_paper_info(soup, pwc_url)

        if not paper_data.get('id'):
            return {}

        return {
            'paper': paper_data,
            'codes': self.extract_codes(soup),
            'datasets': self.extract_datasets(soup),
            'tasks': self.extract_tasks(soup),
            'methods': self.extract_methods(soup),
            'authors': self.extract_authors(soup),
            'chunks': []  
        }

    def extract_paper_info(self, soup: BeautifulSoup, pwc_url: str) -> Dict[str, Any]:
        title_elem = soup.select_one('div.paper-title h1')
        title = title_elem.get_text(separator=" ", strip=True) if title_elem else ""

        paper_id_source = title if title else pwc_url
        if not paper_id_source:
            return {}
        paper_id = self.generate_id(paper_id_source, "paper")

        abstract_elem = soup.find('div', class_='paper-abstract')
        abstract = ""
        if abstract_elem:
            p_tags = abstract_elem.find_all('p')
            abstract = "\n".join(p.get_text(separator=" ", strip=True) for p in p_tags) if p_tags \
                else abstract_elem.get_text(separator=" ", strip=True)

        arxiv_link = None
        arxiv_id = ""
        for a in soup.find_all('a', href=True):
            if 'arxiv.org/pdf' in a['href']:
                arxiv_link = a['href']
                arxiv_id = self.extract_arxiv_id(arxiv_link)
                break

        publication_date_str = soup.find('span', class_="author-span").get_text(strip=True)

        paper_data = {
            'id': paper_id, 'name': title, 'arxiv_link': arxiv_link, 'abstract': abstract,
            'arxiv_id': arxiv_id, 'pwc_link': pwc_url,
            'publication_date': publication_date_str
        }
        if paper_id not in self.nodes['papers']:
            self.nodes['papers'][paper_id] = paper_data
        return paper_data

    def extract_datasets(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        datasets = []
        dataset_section = soup.find('div', id='datasets')
        
        if dataset_section:
            links = dataset_section.select('div.paper-datasets a[href^="/dataset/"]')
            
            for link in links:
                name = link.get_text(strip=True)
                href = link.get("href")

                if name and href:
                    full_url = self.base_url + href
                    dataset_id = self.generate_id(name, "dataset")
                    dataset_data = {'id': dataset_id, 'name': name, 'link': full_url}

                    if dataset_id not in self.nodes['datasets']:
                        self.nodes['datasets'][dataset_id] = dataset_data
                    datasets.append(dataset_data)

        return datasets

    def extract_tasks(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        tasks = []
        tasks_section = soup.find('div', id='tasks')
        if tasks_section:
            task_links = tasks_section.select('.paper-tasks a .badge-primary span:last-child')
            
            for span in task_links:
                name = span.get_text(strip=True)
                parent_link = span.find_parent('a')
                
                if name and parent_link and 'href' in parent_link.attrs:
                    href = parent_link['href']
                    full_url = self.base_url +  href
                    task_id = self.generate_id(name, "task")
                    task_data = {'id': task_id, 'name': name, 'link': full_url}
                    
                    if task_id not in self.nodes['tasks']:
                        self.nodes['tasks'][task_id] = task_data
                    tasks.append(task_data)
        return tasks

    def extract_methods(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        methods = []
        methods_tag = soup.select('div.method-section a')

        for method_tag in methods_tag:
            href = method_tag.get("href")
            name = method_tag.text.strip()
            
            if not href or not href.startswith("/method/"):
                continue
            if name.lower() == "relevant methods here":
                continue
            
            method_link = self.base_url + href
            method_id = self.generate_id(name, "method")
            method_data = {'id': method_id, 'name': name, "link": method_link}
            
            if method_id not in self.nodes['methods']:
                self.nodes['methods'][method_id] = method_data
            methods.append(method_data)

        return methods

    def extract_codes(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        codes = []

        code_section = soup.find('div', id='code')
        if not code_section:
            return codes

        implementations = code_section.find('div', class_='paper-implementations')
        if not implementations:
            return codes

        #! full list ile alınca 2 kere yazıyor
        code_rows = implementations.select('#implementations-short-list .row')

        for row in code_rows:
            # GitHub bağlantısı
            # link_elem = row.select_one('.col-sm-7 .paper-impl-cell a.code-table-link') 
            link_elem = row.select_one('.paper-impl-cell a.code-table-link')
            if not link_elem or 'href' not in link_elem.attrs:
                continue

            href = link_elem['href']
            if 'github.com' not in href:
                continue

            # Repo adı
            # repo_name = link_elem.get_text(strip=True) #!o divdeki tum metinleri aldi sil
            repo_name = ''.join([t for t in link_elem.contents if isinstance(t, str)]).strip()

            star_icon = row.select_one('.col-3 .paper-impl-cell span[data-name="star"]')
            star_count = 0
            if star_icon:
                for sibling in star_icon.next_siblings:
                    if isinstance(sibling, str):
                        star_text = sibling.strip()
                        if star_text:
                            star_count = self.extract_stars(star_text)
                            break
            
            code_id = self.generate_id(href, "code")
            code_data = {
                'id': code_id,
                'name': repo_name,
                'link': href,
                'star': star_count
            }

            if code_id not in self.nodes['codes']:
                self.nodes['codes'][code_id] = code_data
            codes.append(code_data)

        return codes

    def extract_authors(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        authors = []
        authors_spans = soup.find_all('span', class_='author-span')[1:]

        if authors_spans:
            for author in authors_spans:
                link = self.base_url + author.find("a")["href"]
                name = author.get_text(strip=True)
                author_id = self.generate_id(name, "author")
                author_data = {'id': author_id, 'name': name, "link": link}
                if author_id not in self.nodes['authors']:
                    self.nodes['authors'][author_id] = author_data
                authors.append(author_data)
        return authors

    def create_relationships(self, paper_data: Dict[str, Any], extracted_data: Dict[str, Any]):
        paper_id = paper_data.get('id')
        if not paper_id: return

        relationship_map = {
            'codes': 'HAS_CODE', 'datasets': 'USES_DATASET',
            'tasks': 'ADDRESSES_TASK', 'methods': 'USES_METHOD',
            'chunks': 'HAS_CHUNK'
        }
        for node_type, rel_type in relationship_map.items():
            for item in extracted_data.get(node_type, []):
                if item.get('id'):
                    self.relationships.append({'from': paper_id, 'to': item['id'], 'type': rel_type})
        
        for author in extracted_data.get('authors', []):
            if author.get('id'):
                self.relationships.append({'from': author['id'], 'to': paper_id, 'type': 'AUTHORED'})

    def process_page_items(self, items_to_process: List[Dict[str, str]]):
        for item_data in items_to_process:
            html_content = item_data.get('html_content')
            pwc_url = item_data.get('pwc_url')
            if not html_content or not pwc_url: 
                print(f"❌ Geçersiz makale bilgisi: ID veya pwc_url eksik")
                continue
            
            try:
                extracted_data = self.parse_paper_html(html_content, pwc_url)
                if extracted_data and 'paper' in extracted_data and extracted_data['paper'].get('id'):
                    self.create_relationships(extracted_data['paper'], extracted_data)
            except Exception as e:
                print(f"'{pwc_url}' işlenirken bir hata oluştu: {type(e).__name__} - {str(e)}")

    def save_to_json(self, output_file: str):
        final_nodes_as_lists = {k: list(v.values()) for k, v in self.nodes.items()}
        output_data = {
            'nodes': final_nodes_as_lists,
            'relationships': self.relationships,
            'metadata': {
                'total_papers': len(self.nodes['papers']),
                'total_codes': len(self.nodes['codes']),
                'total_datasets': len(self.nodes['datasets']),
                'total_tasks': len(self.nodes['tasks']),
                'total_methods': len(self.nodes['methods']),
                'total_authors': len(self.nodes['authors']),
                'total_chunks': len(self.nodes['chunks']),
                'total_relationships': len(self.relationships),
                'extracted_at': datetime.now().isoformat()
            }
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"Veri {output_file} dosyasına kaydedildi.")
        print(f"Toplam: {len(self.nodes['papers'])} paper, {len(self.relationships)} ilişki.")