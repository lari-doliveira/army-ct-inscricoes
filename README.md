

# Army CT — Inscrições

MVP acadêmico para cadastrar inscrições individuais ou em dupla,
confirmar pagamentos manualmente e consultar o total confirmado.

## Regra principal

Cada inscrição confirmada ocupa uma vaga.
Uma dupla possui dois integrantes, mas conta como uma inscrição.
Pagamentos pendentes não entram no total.

## Tecnologias

- Python 3.14
- Django 5.2
- PostgreSQL 17
- HTML e CSS
- GitHub Actions

As versões das dependências estão fixadas em requirements.txt.

## Execução local no macOS

Com Python, Git e PostgreSQL instalados e o banco em execução:

```bash
git clone https://github.com/lari-doliveira/army-ct-inscricoes.git
cd army-ct-inscricoes
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Crie o banco uma única vez:

```bash
createdb army_ct
```

Configure a chave nesta sessão do Terminal:

```bash
export DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"
```

Por padrão, a conexão local utiliza o banco army_ct,
o usuário do sistema e o socket /tmp.
Outros ambientes podem definir DB_NAME, DB_USER, DB_PASSWORD,
DB_HOST e DB_PORT por variáveis de ambiente.

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acesse http://127.0.0.1:8000/ e entre com a conta criada.

Ao abrir outro Terminal, ative novamente o ambiente virtual
e configure DJANGO_SECRET_KEY.

## Testes automatizados

```bash
python manage.py test inscricoes --verbosity 2
```

A execução utiliza um banco de testes separado.
O usuário PostgreSQL precisa ter permissão para criar esse banco.

Os testes verificam validação, cadastro, contagem, confirmação
repetida, transação, autenticação, permissões e proteção CSRF.

## Integração contínua

O arquivo .github/workflows/ci.yml executa verificações,
migrações, compilação Python e testes com PostgreSQL
em pushes e Pull Requests.

As credenciais presentes no workflow são fictícias
e exclusivas do ambiente temporário de testes.

## Organização

- config/: configurações e rotas principais.
- inscricoes/models.py: entidades e restrições.
- inscricoes/forms.py: validação e cadastro em transação.
- inscricoes/views.py: operações protegidas.
- inscricoes/templates/: interfaces.
- inscricoes/tests.py: testes automatizados.

## Limites desta versão

Execução local para desenvolvimento e validação com dados fictícios.
Não processa pagamentos, não integra WhatsApp e não monta baterias.
A conferência do comprovante é feita externamente pela equipe.

A implantação pública exige configuração de produção, HTTPS,
segredos, backups e revisão dos controles de segurança.
O servidor runserver e a configuração atual de desenvolvimento
não devem ser usados em produção.

A validação com representante externo e seus resultados
serão documentados após a realização das sessões.