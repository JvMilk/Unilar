# Integração da tela de imóvel

Origem: https://github.com/pedroro-byte/loja (branch `main`, consultada em 28/10/2026).

O projeto principal continua sendo `mysite`, com o app `unilar`. A tela recebida foi convertida em template Django e usa o mesmo cabeçalho, Bootstrap e logo da página de login existente. O CSS do imóvel fica restrito à página para preservar o estilo do login.

## Endereços

- `/login/`: tela original de login.
- `/` e `/inicio/`: página inicial integrada do Kauan.
- `/imoveis/`: catálogo com filtros de cidade, tipo e preço executados no Django.
- `/imoveis/kitnet-no-centro/`: detalhes, galeria, contato e visita.
- `/favoritos/`: imóveis favoritos da sessão deste navegador.
- `/admin/`: contatos e pedidos de visita, acessíveis com uma conta administrativa.

## Organização

- Templates: `unilar/templates/unilar/`.
- Cabeçalho compartilhado: `unilar/templates/cabecalho.html`.
- CSS: `unilar/front/css/style.css`.
- JavaScript da galeria e formulários: `unilar/front/js/imovel.js`.
- Imagens importadas: `unilar/front/imagens/`.
- Backend: `unilar/models.py`, `forms.py`, `views.py`, `urls.py` e `admin.py`.
- Migração: `unilar/migrations/0001_initial.py`.

## Comportamento

Os contatos e pedidos de visita são gravados no banco local existente (SQLite). Os formulários têm validação no servidor e proteção CSRF. Visitas exigem data e horário futuros, no fuso de São Paulo, dentro dos horários exibidos no formulário. Os pedidos são solicitações, sem reserva automática de horário. Os favoritos são armazenados na sessão Django, sem exigir login, e duram enquanto a sessão estiver válida.

O envio de e-mail ao proprietário ainda não está configurado. Os dados do imóvel e do proprietário são os exemplos fixos recebidos no repositório; o cadastro e a listagem de imóveis ainda serão integrados. As outras páginas do menu (`/inicio/`, `/sobre/`, `/suporte/`) e os fluxos de autenticação da tela de login já eram pendentes e dependem das próximas partes do projeto.

SQL Server Express 2022 ficou para uma etapa posterior, conforme solicitado. Nenhuma configuração de SQL Server foi adicionada.

## Executar no PowerShell

```powershell
cd C:\Users\joaol\OneDrive\Documentos\Unilar\Projeto
.\myvenv\Scripts\python.exe manage.py migrate
.\myvenv\Scripts\python.exe manage.py runserver 127.0.0.1:8001
```

Para consultar solicitações pelo painel administrativo, use uma conta administrativa existente ou crie uma com `manage.py createsuperuser`. Nenhuma senha ou conta foi criada pela integração.

## Verificação

```powershell
.\myvenv\Scripts\python.exe manage.py check
.\myvenv\Scripts\python.exe manage.py test unilar
.\myvenv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Cinco testes cobrem páginas, gravação e validação de contatos e visitas, favoritos isolados por sessão, métodos HTTP e CSRF. Também foram conferidos no navegador a galeria, o envio de contato e a persistência do favorito após recarregar. A captura `docs/imagens/integracao-imovel.png` registra a aparência da página.

Os arquivos modificados do projeto original foram copiados antes da integração para a pasta `backups/antes-integracao-pedro-*`, ao lado de `Projeto/`.

## Integração do Kauan

Origem: https://github.com/kauanldb/unilar, branch main, consultada em 28/10/2026. Página inicial, banner, quatro imóveis e seção de benefícios adaptados ao cabeçalho principal. Arquivos: `catalogo.py`, `templates/inicio.html`, `front/css/style.css` e `front/imagens/`.

O catálogo agora tem cinco imóveis de exemplo e favoritos unificados na sessão Django. A kitnet de Patos de Minas recebida do Kauan é distinta da kitnet de Rio Paranaíba recebida do Pedro. Apenas esta última possui a página completa de detalhes; os outros cartões indicam que os detalhes ainda serão adicionados. O catálogo fica definido em Python nesta etapa, sem novo cadastro no banco. A referência anterior à listagem pendente foi resolvida nesta integração; autenticação, Sobre e Suporte continuam pendentes.

Sete testes passaram após a integração, incluindo filtros e favoritos compartilhados entre catálogo e detalhes. A página inicial também foi aberta e conferida no navegador em largura de celular. Backup anterior às alterações: `backups/antes-integracao-kauan/`.


## Estrutura de arquivos

- `unilar/front/css/style.css`: todos os estilos próprios, separados por comentários (geral/login, detalhes do imóvel, início/catálogo).
- `unilar/front/js/imovel.js`: JavaScript da galeria e dos formulários.
- `unilar/front/imagens/`: imagens usadas pelo site, sem subpastas.
- `unilar/templates/`: todos os HTMLs, incluindo o cabeçalho, sem subpastas.
- `docs/imagens/`: capturas de tela de conferência (não são servidas pelo site).

O Bootstrap continua sendo carregado pelo CDN.
