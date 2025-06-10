from bs4 import BeautifulSoup
from urllib.parse import urljoin
import hashlib
from datetime import datetime
from typing import Dict, List, Any
import requests
import re
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config.settings import PAPERS_JSON, RAW_DATA_DIR
from src.chatbot.ingestion.scraper import PapersWithCodeScraper

def main():
    print("🚀 PapersWithCode veri toplama işlemi başlatılıyor...")
    
    scraper = PapersWithCodeScraper()
    items_to_process = []
    paper_urls_to_scrape = []

    if not paper_urls_to_scrape:
        max_pages = 1
        for page_num in range(2, max_pages + 2):
            list_url = f"https://paperswithcode.com/?page={page_num}"
            print(f"🔍 Paper listesi taranıyor: {list_url}")
            try:
                response = requests.get(list_url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
                response.raise_for_status()
                list_soup = BeautifulSoup(response.text, "html.parser")
                paper_link_elements = list_soup.select('div.paper-card div.item-content h1 a[href^="/paper/"]')
                
                if not paper_link_elements:
                    print(f"⚠️ Sayfa {page_num} için paper linki bulunamadı. Selector'leri kontrol edin.")
                    continue

                for link_elem in paper_link_elements[:10]:
                    paper_relative_url = link_elem.get('href')
                    if paper_relative_url:
                        paper_full_url = urljoin(scraper.base_url, paper_relative_url)
                        paper_urls_to_scrape.append(paper_full_url)
            except requests.exceptions.RequestException as e:
                print(f"❌ Paper listesi ({list_url}) alınırken hata: {e}")

    unique_paper_urls = sorted(list(set(paper_urls_to_scrape)))
    print(f"📊 Toplam {len(unique_paper_urls)} benzersiz paper URL'si işlenecek.\n")

    for paper_full_url in unique_paper_urls:
        print(f"📄 Paper işleniyor: {paper_full_url}")
        print(f"⬇️  Detay sayfası çekiliyor: {paper_full_url}")
        try:
            paper_response = requests.get(paper_full_url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
            paper_response.raise_for_status()
            items_to_process.append({'html_content': paper_response.text, 'pwc_url': paper_full_url})
        except requests.exceptions.RequestException as e:
            print(f"❌ Paper detay sayfası ({paper_full_url}) alınırken hata: {e}")
        print("\n")

    if not items_to_process:
        print("⚠️ İşlenecek paper bulunamadı.")
    else:
        print(f"🔄 Paper'lar işleniyor...")
        scraper.process_page_items(items_to_process)
    
    # Output dosyasını ayarla ve scraper'ı çağır
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_file = str(PAPERS_JSON)
    print(f"🔄 Veriler {output_file} dosyasına kaydediliyor...")
    scraper.save_to_json(output_file)
    print(f"✅ Veriler {output_file} dosyasına kaydedildi.")

if __name__ == "__main__":
    main()
