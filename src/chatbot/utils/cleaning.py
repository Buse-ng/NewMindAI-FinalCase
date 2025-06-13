def clean_text(text, is_cypher=False):
    """
        Metni temizler, <think> etiketlerini ve gereksiz açıklamaları kaldırır.
        
        Args:
            text (str): Temizlenecek metin
            is_cypher (bool): Metin bir Cypher sorgusu ise True, normal metin ise False
            
        Returns:
            str: Temizlenmiş met
    """
    if "<think>" in text and "</think>" in text:
        start_index = text.find("<think>")
        end_index = text.find("</think>") + len("</think>")
        text = text[:start_index] + text[end_index:]
        if not is_cypher and "<think>" in text:
            return clean_text(text, is_cypher)
    
    if is_cypher:
            lines = text.strip().split('\n')
            clean_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("//") and not line.startswith("<"):
                    clean_lines.append(line)
            text = ' '.join(clean_lines)
        
    return text.strip()

def clean_query(text):
    return clean_text(text, is_cypher=True)

def clean_response(text):
    return clean_text(text, is_cypher=False)