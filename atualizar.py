import datetime as dt, email.utils, html, json, pathlib, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parents[1]
TERMS={
 'Amazonas':'Amazonas Manaus notícias',
 'Tapauá':'Tapauá Amazonas',
 'Notícias urgentes':'últimas notícias Brasil',
 'Política':'política Brasil',
 'Tecnologia':'tecnologia inovação Brasil',
 'Esportes':'esportes futebol Brasil',
 'Economia':'economia Brasil mercado',
}
HEADERS={'User-Agent':'Mozilla/5.0 (compatible; NewsBrasilPWA/1.0; RSS reader)'}
items=[]; errors=[]
for category, term in TERMS.items():
    url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':term,'hl':'pt-BR','gl':'BR','ceid':'BR:pt-419'})
    try:
        req=urllib.request.Request(url,headers=HEADERS)
        with urllib.request.urlopen(req,timeout=22) as response: content=response.read(2_500_000)
        root=ET.fromstring(content)
        for entry in root.findall('./channel/item')[:25]:
            def get(name):
                e=entry.find(name);return (e.text or '').strip() if e is not None else ''
            title=html.unescape(re.sub('<[^>]+>','',get('title')))
            source=entry.find('source'); source=(source.text or '').strip() if source is not None else ''
            link=get('link')
            if not title or not link.startswith('https://'):continue
            try:
                pub=email.utils.parsedate_to_datetime(get('pubDate')).astimezone(dt.timezone.utc).isoformat()
            except Exception: pub=''
            items.append({'title':title,'url':link,'source':source or 'Google Notícias','category':category,'date':pub})
    except Exception as exc: errors.append(f'{category}: {str(exc)[:120]}')
# unique within each category, sorted by date
unique={(i['category'],i['title'].lower()):i for i in items}
news=sorted(unique.values(),key=lambda x:x['date'],reverse=True)
output={'updatedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'items':news[:170],'errors':errors}
if not news:
    previous=ROOT/'noticias.json'
    if previous.exists():
        try:
            old=json.loads(previous.read_text(encoding='utf-8'))
            if old.get('items'):print('Feeds indisponíveis, mantendo últimas notícias.');raise SystemExit(0)
        except (ValueError, OSError):pass
if not news:
    raise SystemExit('ERRO: nenhum feed retornou notícias. ' + '; '.join(errors))
(ROOT/'noticias.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
print('Notícias:',len(news),'Erros:',errors)
