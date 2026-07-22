import os
import re
import pypdf
import psycopg2
import requests
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "").strip()
DB_NAME = os.getenv("DB_NAME", "").strip()
DB_USER = os.getenv("DB_USER", "").strip()
DB_PASS = os.getenv("DB_PASS", "").strip()
DB_PORT = os.getenv("DB_PORT", "6543").strip()

PASTA_PDFS = "./cartas_pdf"

# 🚫 LISTA NEGRA EXPANDIDA: Blindagem total contra textos institucionais
TERMOS_IGNORADOS = [
    "quem pode utilizar", 
    "gestor municipal", 
    "cidades", 
    "etapas para a realização",
    "documentação necessária",
    "o que é?",
    "o cadastro ambiental",
    "o cau também conecta",
    "isso incentiva o uso",
    "qualidade e tamanho",
    "qualquer pessoa por meio",
    "etapa 1",
    "etapa 2",
    "acesse o sistema pelo site",
    "para android",
    "para ios",
    "canais de prestação",
    "aplicativo móvel",
    "e-mail:",
    "telefone:",
    "tempo de duração",
    "atendimento imediato",
    "caso seja gestor",
    "por motivo de segurança",
    "importante:",
    "este serviço é voltado",
    "para realizar o cadastro",
    "solicitante de refúgio:",
    "a primeira etapa é",
    "clique aqui se você",
    "web: inscrever-se",
    "avaliação: sem avaliação",
    "por meio do acesso externo"
]

def validar_url(url):
    """Testa se a URL existe de verdade e detecta o Soft 404 (páginas de erro disfarçadas)."""
    try:
        resposta = requests.get(url, allow_redirects=True, timeout=3)
        if resposta.status_code != 200:
            return False
        
        conteudo_html = resposta.text
        if "esta página não existe" in conteudo_html or "Desculpe, mas esta página" in conteudo_html:
            return False
            
        return True
    except Exception:
        return False

def extrair_servicos_pdf(caminho_pdf, id_orgao):
    """Extrai os serviços do PDF. Se o link direto falhar, gera o link de busca seguro."""
    servicos = []
    
    if not os.path.exists(caminho_pdf):
        return servicos

    leitor = pypdf.PdfReader(caminho_pdf)

    padrao_limpeza = re.compile(r'^[",\s]+|[",\s\d]+$')
    padrao_apenas_numeros = re.compile(r'^\d+$')
    padrao_caracteres_especiais = re.compile(r'[^a-z0-9\s-]')
    padrao_multiplos_espacos = re.compile(r'\s+')

    for numero_pagina in range(2, 5):
        if numero_pagina >= len(leitor.pages):
            break
        pagina = leitor.pages[numero_pagina]
        texto = pagina.extract_text()
        linhas = texto.split('\n')

        for linha in linhas:
            linha_limpa = linha.strip()
            linha_lower = linha_limpa.lower()

            # Filtro básico para ignorar linhas de navegação do PDF
            if (
                not linha_limpa 
                or padrao_apenas_numeros.match(linha_limpa)
                or "serviços disponíveis" in linha_lower 
                or "página" in linha_lower
                or "pagina" in linha_lower
                or ("buscar" in linha_lower and "por" in linha_lower)
                or linha_lower.startswith("sumário") 
                or linha_lower.startswith("índice")
            ):
                continue

            nome_servico = padrao_limpeza.sub('', linha_limpa).strip()

            if len(nome_servico) < 5:
                continue

            # 🎯 NOVO FILTRO DE QUALIDADE DE DADOS (Aqui entra a mágica!)
            nome_servico_lower = nome_servico.lower()
            if any(termo in nome_servico_lower for termo in TERMOS_IGNORADOS):
                print(f"⏩ Texto ignorado por segurança (Filtro de Qualidade): {nome_servico}")
                continue # Pula esta linha e vai direto para a próxima do PDF

            # Geração do slug para tentar o Link Direto
            slug = nome_servico_lower
            slug = slug.replace('é', 'e').replace('á','a').replace('ã','a').replace('ç','c').replace('ó','o').replace('õ','o').replace('í','i').replace('ú','u')
            slug = padrao_caracteres_especiais.sub('', slug)
            slug = padrao_multiplos_espacos.sub('-', slug)

            url_gerada = f"https://www.gov.br/pt-br/servicos/{slug}"
            
            print(f"🔗 Testando URL: {url_gerada}...")
            
            if validar_url(url_gerada):
                url_final = url_gerada
                print("URL Válida! (200 OK)")
            else:
                # Fallback imediato para a página de busca com o termo codificado de forma segura
                busca_slug = urllib.parse.quote_plus(nome_servico)
                url_final = f"https://www.gov.br/pt-br/search?SearchableText={busca_slug}"
                print(f"⚠️ URL Inválida. Aplicando Fallback direto para busca: {url_final}")

            servicos.append({
                "nome": nome_servico,
                "url": url_final,
                "tipo": "Web",
                "id_orgao": id_orgao
            })
    return servicos

def buscar_orgaos_no_banco(cursor):
    cursor.execute("SELECT id_orgao, sigla FROM Orgao;")
    return cursor.fetchall()

def salvar_no_banco(cursor, servicos):
    if not servicos:
        return
    query = """
        INSERT INTO Servico (nome, url, tipo, id_orgao) 
        VALUES (%s, %s, %s, %s);
    """
    for s in servicos:
        cursor.execute(query, (s["nome"], s["url"], s["tipo"], s["id_orgao"]))

def processar_todos_os_pdfs():
    if not os.path.exists(PASTA_PDFS):
        os.makedirs(PASTA_PDFS)
        print(f"Pasta '{PASTA_PDFS}' criada. Cole os PDFs dos órgãos lá dentro!")
        return

    conn = psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT
    )
    cursor = conn.cursor()

    try:
        print("🧹 Limpando tabela de Serviços para evitar duplicações...")
        cursor.execute("TRUNCATE TABLE Servico RESTART IDENTITY CASCADE;")
        conn.commit()

        orgaos = buscar_orgaos_no_banco(cursor)
        print(f"🔎 Encontrados {len(orgaos)} órgãos ativos no banco de dados.")
        
        for id_orgao, sigla in orgaos:
            nome_arquivo = f"{sigla.lower()}.pdf"
            caminho_completo = os.path.join(PASTA_PDFS, nome_arquivo)

            if os.path.exists(caminho_completo):
                print(f"📦 Processando o arquivo '{nome_arquivo}' para o órgão {sigla} (ID {id_orgao})...")
                servicos_extraidos = extrair_servicos_pdf(caminho_completo, id_orgao)
                salvar_no_banco(cursor, servicos_extraidos)
                print(f"✅ {len(servicos_extraidos)} serviços inseridos com sucesso para o {sigla}!")
            else:
                print(f"⚠️ Arquivo '{nome_arquivo}' não encontrado na pasta. Pulando órgão {sigla}.")

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"❌ Ocorreu um erro no pipeline: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    processar_todos_os_pdfs()