# News Brasil — PWA simples para GitHub Pages

Site instalável (PWA) com categorias **Amazonas, Tapauá, Notícias urgentes, Política, Tecnologia, Esportes e Economia**. Usa feeds RSS públicos de pesquisa do Google Notícias como agregador de manchetes e links para os veículos de origem, sem reproduzir matérias completas.

## Publicar (sem Cloudflare e sem instalar dependências)

1. Crie um repositório no GitHub (ex.: `news-brasil`).
2. Envie **todos os arquivos e pastas desta pasta**, incluindo `.github/workflows/pages.yml`, para a raiz do repositório. Defina a branch como `main`.
3. Em **Settings → Pages → Build and deployment → Source**, selecione **GitHub Actions**.
4. Em **Actions**, abra **Atualizar notícias e publicar PWA** e clique em **Run workflow** (ou aguarde a execução do push).
5. Confira o endereço gerado no workflow ou em Settings → Pages. Será parecido com `https://SEU-USUARIO.github.io/news-brasil/`.
6. No celular, abra o site em HTTPS e selecione **Adicionar à Tela de Início** (iPhone: menu de compartilhamento do Safari).

## Como as notícias chegam?

A ação `pages.yml` executa `scripts/atualizar.py`, consulta RSS de pesquisa do Google Notícias e gera `noticias.json`. A rotina está agendada a cada 30 minutos, mas o GitHub pode atrasar, pausar ou não executar determinadas rotinas; a disponibilidade dos feeds também pode variar. O primeiro site só mostrará notícias após uma execução bem-sucedida.

## Notificações

**Esta versão NÃO envia notificações push com o aplicativo fechado.** GitHub Pages só hospeda arquivos estáticos; Web Push precisa de um serviço que registre assinaturas e envie mensagens. A estrutura PWA possui Service Worker para instalação/cache, mas ele não está configurado para Push. Podemos acrescentar depois um backend (ex.: Cloudflare Workers + armazenamento + VAPID) sem mudar a aparência do app.

## Notas

- Não há banco, chaves, tokens ou API paga.
- Se quiser ajustar temas, modifique o dicionário `TERMS` em `scripts/atualizar.py` e a lista `categories` em `app.js`.
- Links e manchetes são fornecidos por terceiros; sua disponibilidade e condições de uso podem mudar.
- Para testar localmente: `python -m http.server 8000` e abra `http://localhost:8000`. Para preencher o feed local, execute `python scripts/atualizar.py` antes; acesso à internet é necessário.

## Se o aplicativo abrir sem notícias

1. Abra o repositório > **Actions** > **Atualizar notícias e publicar PWA** > **Run workflow**.
2. Aguarde aparecer uma marca verde. Se mostrar uma marca vermelha, clique no job e leia a etapa que falhou.
3. Em **Settings > Pages**, selecione **GitHub Actions**, não “Deploy from a branch”.
4. Confirme que existe o arquivo `.github/workflows/pages.yml` (pasta oculta) no GitHub.
5. Reabra o app, use **Atualizar**, e no iPhone remova/reinstale o PWA se permanecer uma versão antiga.
6. Para confirmar os dados publicados, abra `https://SEU-USUARIO.github.io/SEU-REPO/noticias.json` e procure `items`. Se estiver vazio, o job ainda não publicou manchetes.

O arquivo `noticias.json` inicial está vazio por design. As notícias reais são baixadas pelo workflow, não pelo navegador. Sem execução do workflow o PWA não tem manchetes.
