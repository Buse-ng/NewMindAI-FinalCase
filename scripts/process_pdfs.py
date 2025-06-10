import json
import sys
import os
from pathlib import Path

# Projenin kök dizinini sys.path'e ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Gerekli modüllerin importu 
from src.config.settings import PAPERS_JSON, PDF_DIR, PROCESSED_DATA_DIR
from src.chatbot.ingestion.chunker import LocalChunker
from src.chatbot.ingestion.pdf_downloader import PDFDownloader
from langchain_community.embeddings import HuggingFaceEmbeddings
import torch

def process_pdfs():
    # PDF dizini
    print(f"📂 PDF dizini: {PDF_DIR}")
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    
    # Mevcut JSON verisi
    if not PAPERS_JSON.exists():
        print(f"❌ JSON dosyası bulunamadı: {PAPERS_JSON}")
        return
        
    print(f"📄 JSON dosyası okunuyor: {PAPERS_JSON}")
    with open(PAPERS_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"🖥️ Kullanılan cihaz: {device}")

    # Embeddings modelini yükle
    print(f"🔄 Embedding modeli yükleniyor...")
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={'device': device}
    )
    print(f"✅ Embedding modeli yüklendi: {model_name}")

    # PDF downloader ve chunkerı oluştur
    pdf_downloader = PDFDownloader(PDF_DIR)
    chunker = LocalChunker(embeddings)

    # 'chunks' node'u yoksa oluştur
    if 'chunks' not in data['nodes']:
        data['nodes']['chunks'] = []

    # Papers.json içindeki makaleleri işle
    total_processed = 0
    total_errors = 0
    total_chunks_added = 0
    
    print(f"\n🚀 İşlem başlatılıyor: {len(data['nodes']['papers'])} makale işlenecek")
    print("=" * 60)
    
    for paper in data['nodes']['papers']:
        paper_id = paper.get('id')
        arxiv_link = paper.get('arxiv_link')
        arxiv_id = paper.get('arxiv_id')
        
        if not arxiv_link or not paper_id:
            print(f"⚠️ Geçersiz makale bilgisi: ID veya arxiv link eksik")
            continue
            
        print(f"\n🔍 İşleniyor: {paper['name'][:50]}... (ID: {paper_id})")
        
        try:
            # Arxiv ID'yi kullanarak PDF adını oluştur
            pdf_filename = f"{arxiv_id}.pdf" if arxiv_id else f"{paper_id}.pdf"
            
            # PDF'yi indir
            print(f"📥 PDF indiriliyor: {arxiv_link}")
            pdf_path = pdf_downloader.download_pdf(arxiv_link, pdf_filename)
            print(f"📁 PDF kaydedildi: {pdf_path}")
            
            # PDF'den metin çıkar
            print(f"📄 Metin çıkarılıyor...")
            text, page_count = pdf_downloader.extract_text(pdf_path)
            print(f"📊 Metin çıkarıldı: {page_count} sayfa, {len(text)} karakter")
            
            # Metni chunk'lara böl
            print(f"✂️ Metin parçalanıyor...")
            chunks = chunker.split_text(text, page_count)
            print(f"✅ Metin {len(chunks)} parçaya bölündü")
            
            # Her chunk için embedding oluştur
            print(f"🧠 Embedding'ler oluşturuluyor...")
            chunk_data_list = []
            for i, chunk in enumerate(chunks):
                chunk_text = chunk
                embedding = embeddings.embed_documents([chunk_text])[0]
                chunk_id = f"chunk_{paper_id}_{i}"
                chunk_data = {'id': chunk_id, 'text': chunk_text, 'embedding': embedding, 'order': i}
                chunk_data_list.append(chunk_data)
            
            # Chunk'ları data'ya ekle
            data['nodes']['chunks'].extend(chunk_data_list)
            
            # İlişkileri ekle
            for chunk_data in chunk_data_list:
                data['relationships'].append({
                    'from': paper_id,
                    'to': chunk_data['id'],
                    'type': 'HAS_CHUNK'
                })
            
            total_processed += 1
            total_chunks_added += len(chunk_data_list)
            print(f"🎉 Makale başarıyla işlendi! {len(chunk_data_list)} chunk oluşturuldu.")
                
        except Exception as e:
            print(f"❌ PDF işlenirken hata: {e}")
            total_errors += 1
        
        print("-" * 60)

    # Metadatayı güncelle
    data['metadata']['total_chunks'] = len(data['nodes']['chunks'])
    data['metadata']['total_relationships'] = len(data['relationships'])

    # Güncellenmiş veriyi kaydet
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # İşlenmiş veriyi processed klasörüne kaydet
    processed_file = PROCESSED_DATA_DIR / 'processed_papers.json'
    with open(processed_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✨ İşlem tamamlandı!")
    print(f"📚 Toplam işlenen makale: {total_processed}")
    print(f"❌ Toplam hata: {total_errors}")
    print(f"🧩 Toplam chunk sayısı: {len(data['nodes']['chunks'])}")
    print(f"🔗 Toplam ilişki sayısı: {len(data['relationships'])}")
    print(f"💾 İşlenmiş veriler kaydedildi: {PAPERS_JSON}")
    print(f"💾 İşlenmiş veriler processed klasörüne de kaydedildi: {processed_file}")
    print("=" * 60)

if __name__ == "__main__":
    process_pdfs()
