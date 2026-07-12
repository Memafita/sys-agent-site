#!/usr/bin/env python3
"""Radar de Mercado — agregador de inteligencia publica.

USO LEGITIMO
------------
Inteligencia competitiva, monitoramento de marca PROPRIA e geracao de
leads B2B para oferecer servicos. Cruza fontes PUBLICAS (noticias,
comunidades, registro de empresas, enciclopedias) e monta um relatorio
que pode ser visualizado pelo iPhone e recebido no Telegram.

Este programa NAO acessa dark web, credenciais ou sistemas de terceiros
sem autorizacao.

Uso:
    python radar_mercado.py --termo "Nubank"
    python radar_mercado.py --cnpj 00000000000191
    python radar_mercado.py --termo "inteligencia artificial" --html --notify
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path

import fontes
import telegram_notifier as tg

AQUI = Path(__file__).resolve().parent
PASTA_RELATORIOS = AQUI.parent / "reports"
PASTA_RELATORIOS.mkdir(exist_ok=True)


def coletar(termo: str, cnpj: str, concorrentes: list[str]) -> dict:
    """Roda todas as fontes publicas e devolve um dict normalizado."""
    relatorio: dict = {
        "alvo": {"termo": termo, "cnpj": cnpj, "gerado_em": dt.datetime.now().isoformat(timespec="seconds")},
        "noticias": [],
        "reddit": [],
        "hackernews": [],
        "wikipedia": {},
        "empresa": {},
        "concorrentes": [],
    }

    relatorio["noticias"] = fontes.noticias_google(termo or cnpj)
    relatorio["reddit"] = fontes.mencoes_reddit(termo) if termo else []
    relatorio["hackernews"] = fontes.mencoes_hackernews(termo) if termo else []
    relatorio["wikipedia"] = fontes.wikipedia(termo) if termo else {}
    if cnpj:
        relatorio["empresa"] = fontes.empresa_cnpj(cnpj)
    for c in concorrentes:
        relatorio["concorrentes"].append(fontes.site_metadata(c))
    return relatorio


def _slug(s: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in s)[:40].strip("_") or "alvo"


def salvar(relatorio: dict, saida_json: bool, saida_html: bool) -> dict:
    base = _slug(relatorio["alvo"]["termo"] or relatorio["alvo"]["cnpj"])
    data = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    caminhos: dict = {}
    if saida_json:
        p = PASTA_RELATORIOS / f"{base}_{data}.json"
        p.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")
        caminhos["json"] = str(p)
    if saida_html:
        p = PASTA_RELATORIOS / f"{base}_{data}.html"
        p.write_text(html_relatorio(relatorio), encoding="utf-8")
        caminhos["html"] = str(p)
    return caminhos


def resumo_telegram(relatorio: dict) -> str:
    a = relatorio["alvo"]
    linhas = [f"📡 *Radar de Mercado* — `{a['termo'] or a['cnpj']}`", ""]
    if relatorio["empresa"]:
        e = relatorio["empresa"]
        linhas.append(f"🏢 *{e.get('nome') or e.get('fantasia')}*")
        if e.get("situacao"):
            linhas.append(f"Situação: {e['situacao']} | {e.get('municipio','')}/{e.get('uf','')}")
        linhas.append("")
    linhas.append(f"📰 Notícias: *{len(relatorio['noticias'])}*")
    linhas.append(f"💬 Reddit: *{len(relatorio['reddit'])}* | HN: *{len(relatorio['hackernews'])}*")
    linhas.append(f"🏢 Concorrentes analisados: *{len(relatorio['concorrentes'])}*")
    if relatorio["noticias"]:
        linhas.append("")
        linhas.append("Top 3 notícias:")
        for n in relatorio["noticias"][:3]:
            linhas.append(f"• {n['titulo'][:80]}")
    linhas.append("")
    linhas.append("Relatório completo salvo em reports/.")
    return "\n".join(linhas)


def html_relatorio(relatorio: dict) -> str:
    a = relatorio["alvo"]
    titulo = a["termo"] or a["cnpj"]

    def bloco(nome: str, itens: list[dict], campos: list[tuple[str, str]], link_field: str | None = None):
        if not itens:
            return f"<h2>{nome} <span class='q'>({len(itens)})</span></h2><p class='vazio'>Nada encontrado.</p>"
        rows = []
        for it in itens:
            partes = []
            for rotulo, chave in campos:
                if it.get(chave):
                    partes.append(f"<span class='meta'><b>{rotulo}:</b> {it[chave]}</span>")
            linha = " ".join(partes)
            if link_field and it.get(link_field):
                linha = f"<a href='{it[link_field]}' target='_blank'>{(it.get('titulo') or it[link_field])[:90]}</a><br>" + linha
            else:
                linha = f"<div class='tit'>{it.get('titulo','')}</div>" + linha
            rows.append(f"<li>{linha}</li>")
        return f"<h2>{nome} <span class='q'>({len(itens)})</span></h2><ul class='lista'>{''.join(rows)}</ul>"

    empresa_html = ""
    if relatorio["empresa"]:
        e = relatorio["empresa"]
        empresa_html = "<section class='card empresa'><h2>🏢 Registro da empresa</h2><table>"
        for rotulo, chave in [("Razão social","nome"),("Fantasia","fantasia"),("Situação","situacao"),("Atividade","atividade"),("Porte","porte"),("Capital","capital_social"),("Abertura","abertura"),("Município","municipio"),("UF","uf")]:
            if e.get(chave):
                empresa_html += f"<tr><th>{rotulo}</th><td>{e[chave]}</td></tr>"
        empresa_html += "</table></section>"

    wiki_html = ""
    if relatorio["wikipedia"].get("resumo"):
        w = relatorio["wikipedia"]
        wiki_html = f"<section class='card'><h2>📖 Contexto (Wikipédia)</h2><p><b>{w.get('titulo','')}</b></p><p>{w['resumo']}</p>" + (f"<p><a href='{w['link']}'>Ver na Wikipédia →</a></p>" if w.get('link') else "") + "</section>"

    conc_html = ""
    if relatorio["concorrentes"]:
        items = "".join(f"<li><div class='tit'>{c.get('titulo') or c.get('url')}</div><span class='meta'>{c.get('url','')}</span><br><span class='meta'>{c.get('descricao','')[:160]}</span></li>" for c in relatorio["concorrentes"])
        conc_html = f"<section class='card'><h2>🏢 Concorrentes ({len(relatorio['concorrentes'])})</h2><ul class='lista'>{items}</ul></section>"

    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Radar — {titulo}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,'Segoe UI',sans-serif}}
body{{background:#0b0e14;color:#e6e9ef;padding:18px;max-width:760px;margin:0 auto}}
header{{margin-bottom:18px}}
header h1{{font-size:1.4rem}}
header .sub{{color:#8b93a7;font-size:.85rem;margin-top:4px}}
.card{{background:#151a24;border:1px solid #232a38;border-radius:12px;padding:16px;margin-bottom:14px}}
h2{{font-size:1.05rem;margin-bottom:10px}}
.q{{color:#8b93a7;font-weight:400;font-size:.85rem}}
.lista{{list-style:none}}
.lista li{{padding:10px 0;border-bottom:1px solid #1e2433}}
.lista li:last-child{{border-bottom:0}}
.lista .tit{{font-weight:600;margin-bottom:4px;line-height:1.35}}
.meta{{display:inline-block;color:#9aa3b8;font-size:.78rem;margin-right:10px}}
a{{color:#5aa9ff;text-decoration:none}}
a:hover{{text-decoration:underline}}
.vazio{{color:#8b93a7;font-size:.9rem}}
.empresa table{{width:100%;border-collapse:collapse}}
.empresa th{{text-align:left;color:#8b93a7;font-weight:500;font-size:.8rem;padding:5px 8px;width:38%;vertical-align:top}}
.empresa td{{font-size:.9rem;padding:5px 8px}}
.pill{{display:inline-block;background:#1e7a4e;color:#fff;border-radius:20px;padding:3px 10px;font-size:.72rem}}
footer{{color:#5b6478;font-size:.75rem;text-align:center;margin-top:20px}}
</style></head>
<body>
<header>
  <span class="pill">📡 Radar de Mercado</span>
  <h1 style="margin-top:10px">{titulo}</h1>
  <div class="sub">Relatório gerado em {a['gerado_em'].replace('T',' ')} · fontes públicas</div>
</header>
{empresa_html}
{wiki_html}
{bloco('📰 Notícias', relatorio['noticias'], [('Fonte','fonte'),('Data','data')], 'link')}
{bloco('💬 Reddit', relatorio['reddit'], [('r/','subreddit'),('Score','score')], 'url')}
{bloco('🟧 Hacker News', relatorio['hackernews'], [('Pontos','pontos')], 'url')}
{conc_html}
<footer>Radar de Mercado · uso legítimo: inteligência competitiva, monitoramento de marca própria e leads B2B.</footer>
</body></html>"""


def main():
    ap = argparse.ArgumentParser(description="Radar de Mercado — inteligência pública")
    ap.add_argument("--termo", help="Termo de busca / nome da empresa / marca")
    ap.add_argument("--cnpj", default="", help="CNPJ (somente números)")
    ap.add_argument("--concorrentes", nargs="*", default=[], help="URLs de sites concorrentes para comparar")
    ap.add_argument("--json", action="store_true", help="Salvar relatório em JSON")
    ap.add_argument("--html", action="store_true", help="Salvar relatório em HTML (visualizável no iPhone)")
    ap.add_argument("--notify", action="store_true", help="Enviar resumo para o Telegram")
    args = ap.parse_args()

    if not args.termo and not args.cnpj:
        ap.error("informe --termo ou --cnpj")

    print(f"Radar ligado para: {args.termo or args.cnpj}")
    relatorio = coletar(args.termo or "", args.cnpj, args.concorrentes)

    print(f"  • Notícias: {len(relatorio['noticias'])}")
    print(f"  • Reddit: {len(relatorio['reddit'])}")
    print(f"  • Hacker News: {len(relatorio['hackernews'])}")
    print(f"  • Wikipedia: {'sim' if relatorio['wikipedia'] else 'não'}")
    print(f"  • Empresa (CNPJ): {'sim' if relatorio['empresa'] else 'não'}")
    print(f"  • Concorrentes: {len(relatorio['concorrentes'])}")

    caminhos = salvar(relatorio, saida_json=args.json or True, saida_html=args.html or True)
    if caminhos.get("html"):
        print(f"  → Relatório HTML: {caminhos['html']}")
    if caminhos.get("json"):
        print(f"  → Relatório JSON: {caminhos['json']}")

    if args.notify:
        ok = tg.enviar(resumo_telegram(relatorio))
        print(f"  → Telegram: {'enviado' if ok else 'NÃO enviado (configure config.json)'}")


if __name__ == "__main__":
    main()
