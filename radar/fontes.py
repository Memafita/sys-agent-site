"""Fontes de dados PUBLICAS para o Radar de Mercado.

Todas as fontes deste modulo usam APIS PUBLICAS E LEGITIMAS:
  - Registro de empresas (Receita Federal, via ReceitaWS)        -> dados publicos de CNPJ
  - Noticias (Google News RSS)                                   -> jornalismo publico
  - Mencoes em comunidades publicas (Reddit, Hacker News)        -> discussao publica
  - Informacao enciclopedica (Wikipedia)                         -> conhecimento publico
  - Metadados publicos de sites (title / meta description)       -> pagina inicial publica

O modulo NAO acessa dados privados, credenciais, dark web, nem sistemas
de terceiros sem autorizacao. Ele serve para inteligencia competitiva,
monitoramento de marca propria e geracao de leads B2B.
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

import requests

TIMEOUT = 15
HEADERS = {"User-Agent": "RadarMercado/1.0 (+contato@exemplo.com)"}


def _get(url: str, **kw) -> requests.Response | None:
    """GET com tratamento de erros silencioso (degrada graca a graca)."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, **kw)
        if r.status_code == 200:
            return r
    except requests.RequestException:
        pass
    return None


# ---------------------------------------------------------------- noticias
def noticias_google(termo: str, limite: int = 12) -> list[dict]:
    """Manchetes publicas sobre o termo (Google News RSS, sem auth)."""
    url = (
        "https://news.google.com/rss/search?q="
        + quote_plus(termo)
        + "&hl=pt-BR&gl=BR&ceid=BR:pt-PT"
    )
    r = _get(url)
    if not r:
        return []
    itens: list[dict] = []
    try:
        root = ET.fromstring(r.content)
        for item in root.findall(".//item")[:limite]:
            titulo = (item.findtext("title") or "").strip()
            if not titulo:
                continue
            itens.append(
                {
                    "titulo": titulo,
                    "fonte": (item.findtext("source") or "").strip(),
                    "data": (item.findtext("pubDate") or "").strip(),
                    "link": (item.findtext("link") or "").strip(),
                }
            )
    except ET.ParseError:
        pass
    return itens


# ----------------------------------------------------------- comunidades
def mencoes_reddit(termo: str, limite: int = 8) -> list[dict]:
    """Mencoes publicas em foruns do Reddit (JSON publico, sem auth)."""
    url = f"https://www.reddit.com/search.json?q={quote_plus(termo)}&sort=new&limit={limite}"
    r = _get(url)
    if not r:
        return []
    out: list[dict] = []
    for child in r.json().get("data", {}).get("children", []):
        d = child.get("data", {})
        out.append(
            {
                "titulo": d.get("title", "").strip(),
                "subreddit": d.get("subreddit", ""),
                "score": d.get("score", 0),
                "url": "https://reddit.com" + d.get("permalink", ""),
            }
        )
    return out


def mencoes_hackernews(termo: str, limite: int = 8) -> list[dict]:
    """Mencoes no Hacker News (API publica Algolia, sem auth)."""
    url = f"https://hn.algolia.com/api/v1/search?query={quote_plus(termo)}&tags=story"
    r = _get(url)
    if not r:
        return []
    out: list[dict] = []
    for hit in r.json().get("hits", [])[:limite]:
        out.append(
            {
                "titulo": (hit.get("title") or "").strip(),
                "pontos": hit.get("points", 0),
                "url": hit.get("url") or "https://news.ycombinator.com/item?id=" + str(hit.get("objectID", "")),
            }
        )
    return out


# ----------------------------------------------------------- enciclopedia
def wikipedia(termo: str) -> dict:
    """Resumo enciclopedico publico (Wikipedia REST API)."""
    search = "https://pt.wikipedia.org/w/api.php?action=query&list=search&srsearch=" + quote_plus(termo) + "&format=json&srlimit=1"
    r = _get(search)
    if not r:
        return {}
    resultados = r.json().get("query", {}).get("search", [])
    if not resultados:
        return {}
    titulo = resultados[0]["title"]
    s = _get("https://pt.wikipedia.org/api/rest_v1/page/summary/" + quote_plus(titulo))
    if not s:
        return {"titulo": titulo, "resumo": ""}
    d = s.json()
    return {
        "titulo": d.get("title", titulo),
        "resumo": d.get("extract", "").strip(),
        "link": d.get("content_urls", {}).get("desktop", {}).get("page", ""),
    }


# ------------------------------------------------------------- site meta
def site_metadata(url: str) -> dict:
    """Metadados PUBLICOS da pagina inicial de um site (titulo + descricao)."""
    if not url.startswith("http"):
        url = "https://" + url
    r = _get(url)
    if not r:
        return {}
    html = r.text
    titulo = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    if m:
        titulo = re.sub(r"\s+", " ", m.group(1)).strip()
    desc = ""
    m = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', html, re.I | re.S)
    if m:
        desc = re.sub(r"\s+", " ", m.group(1)).strip()
    return {"url": url, "titulo": titulo, "descricao": desc}


# --------------------------------------------------------- registro CNPJ
def empresa_cnpj(cnpj: str) -> dict:
    """Dados PUBLICOS de registro de empresa brasileira (ReceitaWS).

    ReceitaWS tem limite de requisicoes no plano gratuito; se falhar,
    a funcao retorna {} e o relatorio segue sem essa secao.
    """
    cnpj = re.sub(r"\D", "", cnpj)
    if len(cnpj) != 14:
        return {}
    r = _get("https://receitaws.com.br/v1/cnpj/" + cnpj)
    if not r:
        return {}
    try:
        d = r.json()
    except ValueError:
        return {}
    return {
        "nome": d.get("nome", ""),
        "fantasia": d.get("fantasia", ""),
        "situacao": d.get("situacao", ""),
        "porte": d.get("porte", ""),
        "natureza_juridica": d.get("natureza_juridica", ""),
        "atividade": d.get("atividade_principal", [{}])[0].get("text", "") if d.get("atividade_principal") else "",
        "capital_social": d.get("capital_social", ""),
        "abertura": d.get("abertura", ""),
        "municipio": d.get("municipio", ""),
        "uf": d.get("uf", ""),
    }
