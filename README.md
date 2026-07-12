# Radar de Mercado — Inteligência Pública (sys-agent-site)

Agregador de **inteligência de mercado** que cruza fontes **públicas** de dados
e monta relatórios visualizáveis pelo iPhone e recebidos no Telegram.

> ⚠️ **Uso legítimo:** inteligência competitiva, monitoramento de marca
> **própria** e geração de leads B2B. Este projeto **não** acessa dark web,
> credenciais ou sistemas de terceiros sem autorização.

## O que tem aqui

```
sys-agent-site/
├── index.html                  # Dashboard web (abrir pelo iPhone)
├── radar/                      # O agregador (Python)
│   ├── radar_mercado.py        # Orquestrador + gerador de relatório
│   ├── fontes.py               # Fontes públicas (notícias, Reddit, HN, CNPJ…)
│   ├── telegram_notifier.py    # Alertas no Telegram
│   ├── config.example.json     # Copie para config.json e preencha
│   └── requirements.txt
├── guia/
│   └── freelancing-afiliados.md # Plano de renda no iPhone
└── reports/                    # Onde os relatórios gerados caem
```

## Fontes públicas usadas (todas legítimas, sem dark web)
- **Google News RSS** — manchetes públicas
- **Reddit / Hacker News (Algolia)** — discussões públicas
- **Wikipédia** — contexto enciclopédico
- **ReceitaWS** — dados públicos de CNPJ (Receita Federal)
- **Metadados de sites** — title/description da página inicial pública

## Rodar (Replit / Google Colab / PC)

```bash
cd radar
pip install -r requirements.txt
cp config.example.json config.json   # preencha token/chat_id do Telegram

python radar_mercado.py --termo "Nubank" --html --notify
python radar_mercado.py --cnpj 00000000000191 --notify
python radar_mercado.py --termo "fintech" --concorrentes https://a.com https://b.com
```

Saídas:
- `reports/*.html` — relatório visualizável no iPhone
- `reports/*.json` — dados crus
- Resumo no **Telegram** (com `--notify`)

## Configurar o Telegram (uma vez, pelo celular)
1. Abra **@BotFather** → `/newbot` → copie o **token**.
2. Mande uma mensagem pro seu bot novo.
3. Acesse `https://api.telegram.org/bot<TOKEN>/getUpdates` e copie o `chat.id`.
4. Cole os dois em `radar/config.json`.

## Automatizar (roda sozinho e te avisa)
No **Replit** ou **GitHub Actions**, agende para rodar 1x/dia. O iPhone só
recebe o resumo no Telegram e abre o HTML quando quiser.

## Como vira dinheiro (de forma honesta)
- **Serviço de monitoramento para PMEs:** "acompanho sua marca e concorrentes,
  relatório no Telegram, R$X/mês".
- **Diferencial de freelancing:** estude o cliente antes da proposta.
- **Conteúdo de afiliados:** use ângulos em alta puxados das notícias.

Veja o passo a passo completo em [`guia/freelancing-afiliados.md`](guia/freelancing-afiliados.md).

## Por que não a versão "poderosa/deep web"
A versão que caça sistemas expostos de terceiros, credenciais vazadas e
infraestrutura alheia para "virar dinheiro" é a engenharia de invasão — não
gero isso, independentemente de nome (OSINT/CTI) ou onde rode. A versão deste
repositório usa **exatamente a mesma habilidade técnica**, apontada para o lado
que constrói renda sustentável sem risco.
