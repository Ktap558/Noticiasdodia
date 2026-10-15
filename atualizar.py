
import datetime as dt
import email.utils
import html
import json
import pathlib
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

# Pasta principal do projeto
ROOT = pathlib.Path(__file__).resolve().parent

# Categorias de notícias
TERMS = {
    'Amazonas': 'Amazonas Manaus notícias',
    'Tapauá': 'Tapauá Amazonas',
    'Notícias urgentes': 'últimas notícias Brasil',
    'Política': 'política Brasil',
    'Tecnologia': 'tecnologia inovação Brasil',
    'Esportes': 'esportes futebol Brasil',
    'Economia': 'economia Brasil mercado',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; NewsBrasilPWA/1.0; RSS reader)'
}

items = []
errors = []

print('Iniciando atualização das notícias...')

for category, term in TERMS.items():

    print(f'Buscando notícias: {category}')

    url = (
        'https://news.google.com/rss/search?'
        + urllib.parse.urlencode({
            'q': term,
            'hl': 'pt-BR',
            'gl': 'BR',
            'ceid': 'BR:pt-419'
        })
    )

    try:
        req = urllib.request.Request(url, headers=HEADERS)

        with urllib.request.urlopen(req, timeout=22) as response:
            content = response.read(2_500_000)

        root = ET.fromstring(content)

        encontrados = 0

        for entry in root.findall('./channel/item')[:25]:

            def get(name):
                element = entry.find(name)
                return (element.text or '').strip() if element is not None else ''

            title = html.unescape(
                re.sub(r'<[^>]+>', '', get('title'))
            )

            source_element = entry.find('source')

            source = (
                (source_element.text or '').strip()
                if source_element is not None
                else ''
            )

            link = get('link')

            if not title or not link.startswith('https://'):
                continue

            try:
                pub = (
                    email.utils.parsedate_to_datetime(get('pubDate'))
                    .astimezone(dt.timezone.utc)
                    .isoformat()
                )
            except Exception:
                pub = ''

            items.append({
                'title': title,
                'url': link,
                'source': source or 'Google Notícias',
                'category': category,
                'date': pub
            })

            encontrados += 1

        print(f'{category}: {encontrados} notícias encontradas')

    except Exception as exc:
        mensagem = f'{category}: {str(exc)[:200]}'
        errors.append(mensagem)
        print(f'ERRO: {mensagem}')

# Remover notícias duplicadas
unique = {
    (item['category'], item['title'].lower()): item
    for item in items
}

# Ordenar pelas mais recentes
news = sorted(
    unique.values(),
    key=lambda x: x['date'],
    reverse=True
)

# Limitar a 170 notícias
news = news[:170]

output = {
    'updatedAt': dt.datetime.now(dt.timezone.utc).isoformat(),
    'items': news,
    'errors': errors
}

# Caminho correto do JSON
arquivo_json = ROOT / 'noticias.json'

# Se os feeds falharem, manter notícias anteriores
if not news:

    if arquivo_json.exists():
        try:
            old = json.loads(
                arquivo_json.read_text(encoding='utf-8')
            )

            if old.get('items'):
                print('Feeds indisponíveis. Mantendo notícias anteriores.')
                raise SystemExit(0)

        except (ValueError, OSError):
            pass

    raise SystemExit(
        'ERRO: nenhum feed retornou notícias. '
        + '; '.join(errors)
    )

# Salvar notícias no diretório principal
arquivo_json.write_text(
    json.dumps(
        output,
        ensure_ascii=False,
        indent=2
    ),
    encoding='utf-8'
)

print('--------------------------------')
print('Atualização concluída!')
print(f'Total de notícias: {len(news)}')
print(f'Arquivo salvo em: {arquivo_json}')
print(f'Erros encontrados: {len(errors)}')
print('--------------------------------')
