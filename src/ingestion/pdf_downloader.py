import requests
import fitz  # PyMuPDF
import os
import sys
from pathlib import Path

# settings.py'ı import et
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.config.settings import PDF_DIR

class PDFDownloader:
    def __init__(self, save_dir=None):
        """
        PDF indirme ve işleme sınıfı
        
        Args:
            save_dir: PDF'lerin kaydedileceği dizin (belirtilmezse settings.py'daki PDF_DIR kullanılır)
        """
        self.save_dir = Path(save_dir) if save_dir else PDF_DIR
        os.makedirs(self.save_dir, exist_ok=True)

    def download_pdf(self, pdf_url, filename=None):
        """
        URL'den PDF indir
        
        Args:
            pdf_url: PDF'nin URL'si veya dosya yolu
            filename: Kaydedilecek dosya adı (belirtilmezse URL'den çıkarılır)
            
        Returns:
            Path: Kaydedilen PDF'nin tam yolu
        """
        # Eğer pdf_url bir dosya yolu ise (zaten indirilmişse) doğrudan dön
        pdf_path = Path(pdf_url)
        if pdf_path.exists() and pdf_path.suffix.lower() == '.pdf':
            print(f"📁 PDF zaten mevcut: {pdf_path}")
            return pdf_path
            
        # PDF'nin URL'den indirilmesi gerekiyorsa
        if pdf_url.startswith(('http://', 'https://')):
            if filename is None:
                # URL'den dosya adını çıkar
                filename = pdf_url.split("/")[-1]
                if not filename.lower().endswith(".pdf"):
                    filename += ".pdf"
                    
            save_path = self.save_dir / filename
            
            if save_path.exists():
                print(f"📋 PDF zaten indirilmiş: {save_path}")
                return save_path
                
            response = requests.get(pdf_url)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            return save_path
        else:
            # URL değilse, PDF_DIR içinde bu isimde bir dosya var mı kontrol et
            save_path = self.save_dir / filename
            if save_path.exists():
                return save_path
            else:
                raise FileNotFoundError(f"❌ PDF bulunamadı: {pdf_url}")

    def extract_text(self, pdf_path):
        """
        PDF'den metin çıkar
        
        Args:
            pdf_path: PDF dosyasının yolu (string veya Path nesnesi)
            
        Returns:
            tuple: (metin, sayfa_sayısı)
        """
        pdf_path = Path(pdf_path)
        print(f"📖 PDF okunuyor: {pdf_path}")
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        page_count = len(doc)
        doc.close()
        return text, page_count
