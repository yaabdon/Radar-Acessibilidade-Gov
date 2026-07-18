import os
import re
import time
import requests
import psycopg2
import urllib.parse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_PORT = os.getenv("DB_PORT", "5432")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def extrair_nota_da_pagina(url_real):
    """Acessa a página real do serviço e raspa a nota de 1 a 5 estrelas."""
    try:
        time.sleep(0.5) # Respiro para o servidor
        resposta = requests.get(url_real, headers=HEADERS, timeout=5)
        if resposta.status_code != 200:
            return None
            
        soup = BeautifulSoup(resposta.text, 'html.parser')
        
        texto_pagina = soup.get_text()
        match = re.search(r'Avaliação:\s*([0-9.,]+)', texto_pagina)
        
        if match:
            nota_texto = match.group(1).replace(',', '.')
            nota_float = float(nota_texto)
            return round(nota_float) 
            
        return None
    except Exception:
        return None

def resolver_url_se_for_search(url_banco):
    """Se a URL for de busca, entra nela e pega o primeiro link real de resultado."""
    if "search?SearchableText=" not in url_banco:
        return url_banco 
        
    try:
        time.sleep(0.5)
        resposta = requests.get(url_banco, headers=HEADERS, timeout=5)
        if resposta.status_code != 200:
            return None
            
        soup = BeautifulSoup(resposta.text, 'html.parser')
        conteudo_real = soup.find(id="content-core") or soup.find(id="content") or soup
        links = conteudo_real.find_all('a', href=re.compile(r'/servicos/|/apps/'))
        
        for tag in links:
            href = tag.get('href')
            if "buscar-servicos-por" in href or "listar_orgaos" in href:
                continue
            if not href.startswith('http'):
                href = urllib.parse.urljoin("https://www.gov.br", href)
            return href 
            
        return None
    except Exception:
        return None

def rodar_pipeline_avaliacoes():
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id_serv, nome, url FROM Servico;")
        servicos = cursor.fetchall()
        
        print(f"Iniciando coleta de avaliações para {len(servicos)} serviços...")
        
        for id_serv, nome, url in servicos:
            print(f"Processando: {nome}...")
            
            url_real = resolver_url_se_for_search(url)
            
            if not url_real:
                print(f"   ⚠️ Não foi possível determinar a URL real para extrair a nota.")
                continue
                
            nota = extrair_nota_da_pagina(url_real)
            
            if nota is not None:
                # 2. SALVA NO BANCO: Repare que passamos o id_serv (Chave Estrangeira)
                query = """
                    INSERT INTO Avaliacao (nota, data, id_serv)
                    VALUES (%s, %s, %s);
                """
                # Usa a data atual para criar o histórico temporal
                data_atual = datetime.now().date()
                cursor.execute(query, (nota, data_atual, id_serv))
                print(f"   🎉 Nota {nota} salva com sucesso para o ID {id_serv}!")
            else:
                print(f"Serviço sem avaliações computadas no portal no momento.")
                
        conn.commit()
        print("Coleta de avaliações finalizada com sucesso!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro no coletor: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    rodar_pipeline_avaliacoes()