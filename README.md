# UniLar

Projeto acadêmico em Python, Django, HTML, CSS e Bootstrap para busca de imóveis universitários.

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

O projeto também aceita `DB_ENGINE=mssql` para SQL Server, com `DB_NAME`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` e `DB_DRIVER`.

## Fotos dos imóveis no Supabase Storage

O painel aceita várias fotos por imóvel, com até 10 MB por arquivo. O formulário corrige a rotação e converte as imagens para JPEG com até 1.600 px no lado maior.

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

## Estrutura

```
manage.py
requirements.txt
mysite/                 configuração do projeto Django (settings, urls, wsgi, asgi)
unilar/                 aplicativo principal
├── models.py, forms.py, views.py, urls.py, admin.py, catalogo.py, tests.py
├── management/         comandos Django, incluindo enviar_fotos_supabase
├── migrations/
├── templates/          HTMLs (páginas e cabecalho.html)
└── front/              arquivos estáticos (STATICFILES_DIRS)
    ├── css/style.css   estilos
    ├── js/imovel.js    JavaScript
    └── imagens/        imagens do site
docs/                   documentação (INTEGRACAO.md) e capturas de tela
```

## Funcionalidades

- Catálogo com filtros por cidade, tipo e preço, e detalhes de imóveis com galeria. Uma migração carrega os imóveis iniciais no banco.
- Cadastro, login e painel do usuário. Os favoritos do visitante ficam na sessão e são associados à conta ao entrar.
- Contatos, solicitações de visita e dúvidas registrados no banco.
- Página `/sobre/` com números do catálogo e imóveis em destaque.

## Painel administrativo

Depois de instalar as dependências, configurar o banco e aplicar as migrações, crie uma conta administrativa.

```powershell
.\myvenv\Scripts\python.exe manage.py createsuperuser
```

Use o endereço de e-mail também como nome de usuário para entrar pelo login do UniLar. Em `/administracao/`, contas com `is_staff` podem administrar anúncios, imóveis, fotos, dúvidas e informações do site. Superusuários podem conceder acesso administrativo.

As respostas às dúvidas ficam registradas no banco. O envio por e-mail só é tentado quando `EMAIL_HOST` e `DEFAULT_FROM_EMAIL` estão configurados. Use variáveis de ambiente para `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` e `DEFAULT_FROM_EMAIL`; não coloque senhas no repositório.

## Testar

Use um terminal configurado para SQLite, conforme os passos da seção [Executar no Windows com SQLite](#executar-no-windows-com-sqlite).

```powershell
.\myvenv\Scripts\python.exe manage.py check
.\myvenv\Scripts\python.exe manage.py test unilar
```

O comando `test` usa um banco de testes e mantém os uploads no armazenamento local.
