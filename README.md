# UniLar

Projeto acadêmico em Python, Django, HTML, CSS e Bootstrap para busca de imóveis universitários em Rio Paranaíba (MG).

Integra a página inicial e catálogo de Kauan (https://github.com/kauanldb/unilar) e os detalhes de imóvel de Pedro (https://github.com/pedroro-byte/loja), seguindo a estrutura do projeto principal.

## Executar no Windows com SQLite

No PowerShell, na pasta que contém `manage.py`, crie o ambiente virtual, instale as dependências e configure o banco para o terminal atual.

```powershell
python -m venv myvenv
.\myvenv\Scripts\python.exe -m pip install -r requirements.txt
$env:DB_ENGINE = "sqlite"
.\myvenv\Scripts\python.exe manage.py migrate
.\myvenv\Scripts\python.exe manage.py runserver
```

Abra [http://127.0.0.1:8000/inicio/](http://127.0.0.1:8000/inicio/).

O SQLite usa o arquivo local `db.sqlite3`. As URLs de PostgreSQL têm prioridade sobre `DB_ENGINE`. Para usar SQLite, abra um terminal sem `DATABASE_URL`, `POSTGRES_URL` ou outra variável terminada em `_POSTGRES_URL` e defina `DB_ENGINE` novamente.

Defina `DJANGO_SECRET_KEY` com uma chave privada para manter as sessões válidas entre reinicializações. Na ausência dessa variável, o Django gera uma chave temporária a cada inicialização.

## Banco de dados Supabase

Para usar PostgreSQL do Supabase localmente, copie a URI do **Session pooler** para `DATABASE_URL` no PowerShell. Use esse terminal para executar os comandos do Django.

```powershell
$env:DATABASE_URL = "cole-aqui-a-uri-do-session-pooler"
.\myvenv\Scripts\python.exe manage.py migrate
.\myvenv\Scripts\python.exe manage.py runserver
```

O comando `migrate` aplica as migrações ao banco selecionado. Na Vercel, o Django também reconhece `POSTGRES_URL` e nomes com prefixo, como `SUPA_BD_POSTGRES_URL`. Sem uma URL de PostgreSQL ou um `DB_ENGINE` válido, o Django interrompe a inicialização com uma mensagem de configuração.

As migrações não rodam sozinhas na Vercel. Depois de enviar ao GitHub uma mudança que cria migração, rode `migrate` uma vez com a `DATABASE_URL` do Supabase.

O projeto também aceita `DB_ENGINE=mssql` para SQL Server, com `DB_NAME`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` e `DB_DRIVER`.

## Fotos dos imóveis no Supabase Storage

O formulário de imóvel (no painel e em "Anunciar imóvel") aceita várias fotos por imóvel. As fotos escolhidas se acumulam entre seleções, podem ser retiradas antes de salvar e são reduzidas no próprio navegador antes do envio, para caber no limite de 4,5 MB por envio da Vercel. No servidor, cada foto (até 10 MB) tem a rotação corrigida, perde os metadados e é regravada em JPEG com até 1.600 px no lado maior. A primeira foto é a capa do anúncio.

Para gravar no Supabase Storage, habilite o protocolo S3 no projeto Supabase e use um bucket público para leitura das fotos. Configure estas variáveis no ambiente que executa o Django, tanto localmente quanto na Vercel se os dois precisarem acessar as mesmas imagens.

| Variável | Valor |
| --- | --- |
| `SUPABASE_PROJECT_REF` | Referência do projeto Supabase. O código já aponta para o projeto do UniLar por padrão. |
| `SUPABASE_STORAGE_BUCKET` | Nome do bucket público. O padrão é `imoveis`. |
| `SUPABASE_S3_REGION` | Região indicada na configuração S3 do Supabase. O padrão no Django é `us-east-1`. |
| `SUPABASE_S3_ACCESS_KEY_ID` | Identificador da chave de acesso S3. |
| `SUPABASE_S3_SECRET_ACCESS_KEY` | Segredo da chave de acesso S3. |

Sem as duas credenciais S3, o Django grava as fotos em `media/`. A conexão com o PostgreSQL e o armazenamento de fotos são configurados separadamente. Mantenha a URI e as chaves nas variáveis de ambiente, fora do repositório.

### Copiar fotos existentes

Execute o comando no computador que tem os arquivos originais em `media/`, com as credenciais S3 e o banco que contém os registros dessas fotos configurados.

```powershell
.\myvenv\Scripts\python.exe manage.py enviar_fotos_supabase
```

O comando pula arquivos que já existem no bucket e lista as fotos cadastradas cujo arquivo local não foi encontrado.

## Google (opcional)

| Variável | Para que serve |
| --- | --- |
| `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` | Ativam o botão "Entrar com Google". Sem as duas, o login com Google fica escondido. |
| `GOOGLE_MAPS_API_KEY` | Chave da Maps Embed API para o mapa da página do imóvel. Sem ela, o site usa o mapa incorporado padrão do Google, que funciona sem chave. |

O mapa da página do imóvel procura "rua, número, cidade". O bairro fica fora da busca porque, quando o Google não reconhece o nome do bairro, ele deixa de achar a rua. O bairro continua aparecendo no texto do anúncio.

## Funcionalidades

### Para quem procura imóvel

- **Página inicial:** busca rápida e "Imóveis em destaque", com os 4 imóveis disponíveis mais caros.
- **Imóveis (`/imoveis/`):** catálogo com busca por texto e filtros de cidade, tipo, faixa de preço, preço máximo e ordenação. O filtro de tipo mostra só os tipos que têm imóvel disponível, com a quantidade de cada um.
- **Mapa ilustrativo:** ao lado do catálogo, um mapa desenhado de Rio Paranaíba (sem escala) com um pino por bairro e a quantidade de imóveis. Clicar num pino filtra a lista por aquele bairro. A posição de cada bairro fica em `BAIRROS_NO_MAPA`, em `unilar/views.py`. Bairros que ainda não estão no desenho aparecem como botões em "Outros bairros".
- **Página do imóvel:** galeria com 1 foto grande e até 4 menores, e "Mostrar todas as fotos", que abre um carrossel em tela cheia (setas, teclado, deslize no celular e miniaturas). A página também tem destaques montados a partir do cadastro, comodidades, mapa com pontos de referência ao redor e botão para tirar dúvida.
- **Conta:** cadastro (com estado e cidade validados pela lista do IBGE), login, login com Google e painel do usuário. Os favoritos do visitante ficam na sessão e são associados à conta ao entrar.
- **Dúvidas, contatos e solicitações de visita:** ficam registrados no banco. A resposta da equipe aparece na página Dúvidas.
- **Página `/sobre/`:** números do catálogo e imóveis em destaque.
- **Listas do site:** os campos de seleção (`<select>`) abrem uma lista no visual do site (`js/listas.js` e `css/listas.css`). O `<select>` original continua cuidando do valor e do envio do formulário. Para manter a lista nativa num campo, use `<select data-nativo>`.

### Anunciar imóvel (`/anunciar/`)

Qualquer pessoa logada pode anunciar pelo link "Anunciar imóvel" da navbar. O formulário é o mesmo do painel, sem os campos de situação e responsável. O anúncio entra como **pendente**, no nome de quem enviou, e só aparece no site depois de aprovado. A pessoa acompanha a situação de cada anúncio em "Meus anúncios": Em análise, No ar ou Não aprovado.

Enquanto o anúncio não está no ar, só a equipe e o próprio anunciante conseguem abrir a página dele, com uma faixa de "Pré-visualização". Para os demais, o endereço retorna 404.

## Painel administrativo

Depois de instalar as dependências, configurar o banco e aplicar as migrações, crie uma conta administrativa.

```powershell
.\myvenv\Scripts\python.exe manage.py createsuperuser
```

Use o endereço de e-mail também como nome de usuário para entrar pelo login do UniLar. Em `/administracao/`, contas com `is_staff` têm acesso a:

- **Visão geral:** indicadores, gráfico de atividade, imóveis recentes e últimas dúvidas.
- **Imóveis:** cadastrar, editar, excluir e gerenciar fotos.
- **Dúvidas e mensagens:** responder, marcar como pendente ou excluir.
- **Usuários:** dados de cadastro e permissões. Só superusuários concedem acesso administrativo.
- **Anúncios pendentes:** anúncios enviados pelo site que aguardam aprovação, com contador no menu. Cada um tem os botões **Ver anúncio** (pré-visualização), **Editar**, **Aprovar** (fica Disponível e vai ao ar) e **Recusar** (fica Inativo e continua em Imóveis).
- **Configurações:** nome do site, contatos e informações institucionais.

As respostas às dúvidas ficam registradas no banco. O envio por e-mail só é tentado quando `EMAIL_HOST` e `DEFAULT_FROM_EMAIL` estão configurados. Use variáveis de ambiente para `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` e `DEFAULT_FROM_EMAIL`; não coloque senhas no repositório.

## Estrutura

```
manage.py
requirements.txt
mysite/                   configuração do projeto Django (settings, urls, wsgi, asgi)
unilar/                   aplicativo principal
├── models.py             imóveis, fotos, favoritos, dúvidas, visitas, cadastro e configurações
├── forms.py              formulários (cadastro, imóvel do painel, "Anunciar imóvel")
├── views.py              páginas públicas, catálogo, mapa ilustrativo e "Anunciar imóvel"
├── admin_views.py        painel administrativo em /administracao/
├── context_processors.py dados comuns (configurações do site, avatar, contadores do painel)
├── catalogo.py, google_forms.py, urls.py, admin.py, tests.py
├── management/commands/  enviar_fotos_supabase, baixar_municipios
├── migrations/
├── templates/            páginas públicas, cabecalho.html, anunciar.html
│   ├── admin/            telas do painel
│   └── unilar_admin/     layout base do painel
└── front/                arquivos estáticos (STATICFILES_DIRS)
    ├── css/              style.css (site), admin.css (painel), listas.css (listas)
    ├── js/               anuncio.js (galeria e carrossel), fotos.js (envio de fotos),
    │                     listas.js (listas), admin.js, cadastro.js, cpf_cidade.js, duvidas.js, imovel.js
    └── imagens/          imagens do site
docs/                     documentação (INTEGRACAO.md) e capturas de tela
```

## Testar

Use um terminal configurado para SQLite, conforme os passos da seção [Executar no Windows com SQLite](#executar-no-windows-com-sqlite).

```powershell
.\myvenv\Scripts\python.exe manage.py check
.\myvenv\Scripts\python.exe manage.py test unilar
```

O comando `test` usa um banco de testes separado e mantém os uploads no armazenamento local. Se o terminal estiver configurado para o Supabase e o Django perguntar se pode apagar um banco de testes antigo, rode com `--noinput --keepdb` para reaproveitá-lo.
