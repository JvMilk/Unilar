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

- `mysite/`: configuração Django.
- `unilar/templates/`: HTMLs.
- `unilar/front/style.css`: estilos do projeto.
- `unilar/front/imagens/`: imagens.
- `unilar/front/js/`: JavaScript.
- `unilar/models.py`, `forms.py`, `views.py`: backend.

## Funcionalidades

Catálogo com filtros por cidade, tipo e preço; favoritos por sessão; detalhes de uma kitnet; contatos e solicitações de visita gravados no banco local e disponíveis no admin.

O catálogo usa dados de exemplo. Os outros quatro imóveis ainda não têm páginas completas de detalhes. Autenticação da tela de login, Sobre, Suporte e envio de e-mail estão pendentes. SQLite é utilizado nesta etapa; SQL Server Express 2022 será configurado depois.

## Testar

```powershell
.\myvenv\Scripts\python.exe manage.py test unilar
```

O banco e o ambiente virtual são criados localmente e não fazem parte do repositório.
