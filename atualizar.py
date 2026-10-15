
import datetime as dt
import email.utils
import html
import json
import pathlib
import re
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent
ARQUIVO = ROOT / 'noticias.json'
AGORA = dt.datetime.now(dt.timezone.utc)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml, */*',
    'Accept-Language': 'pt-BR,pt;q=0.9',
}

# Fontes de noticias
FONTES = [
    (
        'Notícias urgentes',
        'G1',
        'https://g1.globo.com/rss/g1/'
    ),
    (
        'Notícias urgentes',
        'Agência Brasil',
        'https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml'
    ),
    (
        'Política',
        'Agência Brasil',
        'https://agenciabrasil.ebc.com.br/rss/politica/feed.xml'
    ),
    (
        'Economia',
        'Agência Brasil',
        'https://agenciabrasil.ebc.com.br/rss/economia/feed.xml'
    ),
    (
        'Esportes',
        'Agência Brasil',
        'https://agenciabrasil.ebc.com.br/rss/esportes/feed.xml'
    ),
    (
        'Tecnologia',
        'Tecnoblog',
        'https://tecnoblog.net/feed/'
    ),
    (
        'Amazonas',
        'G1 Amazonas',
        'https://g1.globo.com/dynamo/am/amazonas/rss2.xml'
    ),
]

# Buscas regionais complementares
BUSCAS = {
    'Amazonas': 'Amazonas Manaus',
    'Tapauá': 'Tapauá Amazonas',
}


def normalizar(texto):
    texto = unicodedata.normalize('NFKD', texto or '')
    return ''.join(
        c for c in texto
        if not unicodedata.combining(c)
    ).lower()


def texto(elemento, nome):
    achado = elemento.find(nome)
    return (
        (achado.text or '').strip()
        if achado is not None
        else ''
    )


def data_iso(valor):
    try:
        data = email.utils.parsedate_to_datetime(valor)

        if data.tzinfo is None:
            data = data.replace(tzinfo=dt.timezone.utc)

        return data.astimezone(dt.timezone.utc).isoformat()

    except (TypeError, ValueError, OverflowError):
        return ''


def link_original(url):
    partes = urllib.parse.urlsplit(url)

    if partes.netloc.lower().endswith('bing.com'):
        parametros = urllib.parse.parse_qs(partes.query)
        destino = parametros.get('url', [''])[0]

        if destino.startswith(('https://', 'http://')):
            return destino

    return url


def baixar(url):
    req = urllib.request.Request(
        url,
        headers=HEADERS
    )

    with urllib.request.urlopen(req, timeout=18) as resposta:
        xml = resposta.read(3_000_000)

    return ET.fromstring(xml)


def extrair(feed, categoria, fonte):
    resultado = []

    for item in feed.findall('./channel/item')[:35]:

        titulo = html.unescape(
            re.sub(
                r'<[^>]*>',
                '',
                texto(item, 'title')
            )
        ).strip()

        link = link_original(
            html.unescape(texto(item, 'link'))
        )

        descricao = html.unescape(
            re.sub(
                r'<[^>]*>',
                '',
                texto(item, 'description')
            )
        )

        if not titulo or not link.startswith(
            ('https://', 'http://')
        ):
            continue

        if categoria == 'Tapauá':
            if 'tapaua' not in normalizar(
                titulo + ' ' + descricao
            ):
                continue

        if categoria == 'Amazonas' and fonte == 'Bing Notícias':

            alvo = normalizar(
                titulo + ' ' + descricao
            )

            palavras = (
                'amazonas',
                'manaus',
                'tapaua',
                'manacapuru',
                'parintins',
                'labrea',
                'humaita',
                'tefe'
            )

            if not any(
                palavra in alvo for palavra in palavras
            ):
                continue

        origem = item.find('source')

        veiculo = (
            (origem.text or '').strip()
            if origem is not None
            else ''
        )

        resultado.append({
            'title': titulo,
            'url': link,
            'source': veiculo or fonte,
            'category': categoria,
            'date': data_iso(
                texto(item, 'pubDate')
            ),
        })

    return resultado


# Iniciar busca
noticias = []
erros = []

print('Iniciando busca de notícias...', flush=True)


# Buscar feeds RSS
for categoria, fonte, url in FONTES:

    try:
        lista = extrair(
            baixar(url),
            categoria,
            fonte
        )

        noticias.extend(lista)

        print(
            f'OK {fonte} / {categoria}: '
            f'{len(lista)} notícias',
            flush=True
        )

    except Exception as e:

        erro = (
            f'{fonte} / {categoria}: '
            f'{str(e)[:120]}'
        )

        erros.append(erro)

        print(
            'Falhou:',
            erro,
            flush=True
        )


# Buscar notícias regionais
for categoria, termo in BUSCAS.items():

    url = (
        'https://www.bing.com/news/search?'
        + urllib.parse.urlencode({
            'q': termo,
            'format': 'rss',
            'setlang': 'pt-BR'
        })
    )

    try:
        lista = extrair(
            baixar(url),
            categoria,
            'Bing Notícias'
        )

        noticias.extend(lista)

        print(
            f'OK busca {categoria}: '
            f'{len(lista)} notícias',
            flush=True
        )

    except Exception as e:

        erro = (
            f'Bing / {categoria}: '
            f'{str(e)[:120]}'
        )

        erros.append(erro)

        print(
            'Falhou:',
            erro,
            flush=True
        )


# Remover notícias duplicadas
unicas = {}

for noticia in noticias:

    chave = (
        noticia['category'],
        normalizar(noticia['title'])
    )

    if chave not in unicas:
        unicas[chave] = noticia


# Ordenar pelas mais recentes
ordenadas = sorted(
    unicas.values(),
    key=lambda n: n['date'],
    reverse=True
)[:170]


# Manter notícias anteriores em caso de falha
if not ordenadas:

    if ARQUIVO.exists():

        try:
            anterior = json.loads(
                ARQUIVO.read_text(
                    encoding='utf-8'
                )
            )

            if anterior.get('items'):

                print(
                    'Fontes indisponíveis. '
                    'Mantendo notícias anteriores.',
                    flush=True
                )

                raise SystemExit(0)

        except (OSError, ValueError, TypeError):
            pass

    raise SystemExit(
        'Nenhuma fonte retornou notícias. '
        'Verifique os erros acima.'
    )


# Gerar arquivo JSON
saida = {
    'updatedAt': AGORA.isoformat(),
    'items': ordenadas,
    'errors': erros,
}


# Salvar no diretório principal do projeto
ARQUIVO.write_text(
    json.dumps(
        saida,
        ensure_ascii=False,
        indent=2
    ),
    encoding='utf-8'
)


# Exibir resultado
print('--------------------------------', flush=True)
print('Atualização concluída!', flush=True)
print(
    f'Total de notícias: {len(ordenadas)}',
    flush=True
)
print(
    f'Arquivo salvo em: {ARQUIVO}',
    flush=True
)
print(
    f'Erros encontrados: {len(erros)}',
    flush=True
)
print('--------------------------------', flush=True)


# Estatísticas por categoria
CATEGORIAS = [
    'Amazonas',
    'Tapauá',
    'Notícias urgentes',
    'Política',
    'Tecnologia',
    'Esportes',
    'Economia'
]

for categoria in CATEGORIAS:

    quantidade = sum(
        noticia['category'] == categoria
        for noticia in ordenadas
    )

    print(
        f'{categoria}: {quantidade}',
        flush=True
    )
