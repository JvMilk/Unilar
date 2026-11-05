# UniLar

Projeto acadêmico em Python, Django, HTML, CSS e Bootstrap para busca de imóveis universitários.

Integra a página inicial e catálogo de Kauan (https://github.com/kauanldb/unilar) e os detalhes de imóvel de Pedro (https://github.com/pedroro-byte/loja), seguindo a estrutura do projeto principal.

## Executar no Windows

```powershell
python -m venv myvenv
.\myvenv\Scripts\python.exe -m pip install -r requirements.txt
.\myvenv\Scripts\python.exe manage.py migrate
.\myvenv\Scripts\python.exe manage.py runserver
```

Abra http://127.0.0.1:8000/inicio/.

Para manter uma chave estável entre reinicializações, defina a variável de ambiente `DJANGO_SECRET_KEY` com uma chave privada antes de executar. Na ausência dela, uma chave temporária é gerada; sessões podem ser invalidadas ao reiniciar. A configuração atual é de desenvolvimento.

## Estrutura

```
manage.py
requirements.txt
mysite/                 configuração do projeto Django (settings, urls, wsgi, asgi)
unilar/                 aplicativo principal
├── models.py, forms.py, views.py, urls.py, admin.py, catalogo.py, tests.py
├── migrations/
├── templates/          HTMLs (páginas e cabecalho.html)
└── front/              arquivos estáticos (STATICFILES_DIRS)
    ├── css/style.css   estilos
    ├── js/imovel.js    JavaScript
    └── imagens/        imagens do site
docs/                   documentação (INTEGRACAO.md) e capturas de tela
```

## Funcionalidades

Catálogo com filtros por cidade, tipo e preço; favoritos por sessão; detalhes de imóveis; contatos e solicitações de visita gravados no banco. Os imóveis iniciais do catálogo são carregados para o banco pela migração e passam a ser administráveis.

## Painel administrativo

1. Instale as dependências e aplique as migrações:

   ```bash
   python -m pip install -r requirements.txt
   python manage.py migrate
   ```

2. Crie uma conta autorizada pelo sistema de autenticação do Django:

   ```bash
   python manage.py createsuperuser
   ```

   Use o mesmo endereço de e-mail como nome de usuário; o login existente recebe o e-mail nesse campo. A conta de superusuário pode acessar `/administracao/`. Não compartilhe credenciais nem as grave no código.

O painel permite administrar anúncios, imóveis e fotos, dúvidas, contas e permissões, além das informações do site. Apenas contas administrativas (`is_staff`) acessam as rotas; a criação e concessão de acesso administrativo são feitas por superusuários. Novas fotos são armazenadas em `MEDIA_ROOT` (por padrão, `media/`); em produção, configure um servidor de mídia persistente e um backend de e-mail SMTP.

As respostas às dúvidas ficam registradas no banco. O envio por e-mail só é tentado quando `EMAIL_HOST` e `DEFAULT_FROM_EMAIL` estão configurados. Use variáveis de ambiente para `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` e `DEFAULT_FROM_EMAIL`; não coloque senhas no repositório.

Para validar a aplicação:

```bash
python manage.py check
python manage.py test unilar
```

SQLite é utilizado nesta etapa; SQL Server Express 2022 será configurado depois.

## Testar

```powershell
.\myvenv\Scripts\python.exe manage.py test unilar
```

O banco e o ambiente virtual são criados localmente e não fazem parte do repositório.
