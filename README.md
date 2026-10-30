# TrainerDex

Aplicacao web em Django para uma plataforma de perfil de treinador inspirada no universo Pokemon.

## Arquitetura inicial

- `core`: configuracoes globais, URLs principais e bootstrap do Django.
- `accounts`: cadastro, login e logout usando o sistema de autenticacao do Django.
- `trainers`: perfil do treinador e dashboard protegido.
- `templates`: layouts e paginas HTML server-rendered.
- `static`: CSS e assets compartilhados.

## Etapa 1

Implementado:

- Tela de login personalizada.
- Cadastro de usuario com e-mail opcional e validacao de e-mail unico quando informado.
- Login automatico apos cadastro com criacao do primeiro personagem da conta.
- Redirecionamento para criacao do perfil quando o usuario ainda nao possui treinador.
- Criacao de perfil com cidade selecionavel entre locais de Kanto.
- Genero restrito a Masculino e Feminino.
- Clas atualizados para Orebound, Seavel, Naturia, Windgeon, Psycraft, Malefic, Volcanic, Ironheart, Raibolt e GardeStrike.
- Dashboard protegido para usuarios autenticados com perfil.
- Modal de Pokedex no dashboard com busca por nome, numero ou tipo nos 649 primeiros Pokemon.
- Registros de Pokedex por personagem, com imagens escurecidas ate o Pokemon ser registrado.
- Acao para registrar Pokemon digitando o nome e filtro para mostrar apenas registrados.
- Dashboard principal com visual de menu de jogo, fundo ilustrado e painel central de modulos.
- Uma conta pode ter varios personagens de treinador e alternar o personagem ativo no dashboard.
- Topo com Suporte, Jogar e Amigos.
- Modal de suporte com meios de contato.
- Pagina de amigos com base CRUD: GET lista, POST cria amigo, POST atualiza convite de amigo existente e DELETE exclui.
- Cache local de Pokedex gerado a partir da PokeAPI, com `pokebase` preparado como dependencia Python.
- Progressao de XP por tabela cumulativa dos niveis 1 ao 300.
- Modal de Missoes com imagens, recompensas de XP e conclusao por personagem.
- Modal de Mochila com inventario em grade de 40 slots por personagem.
- Modelo inicial `TrainerProfile` com nivel, XP e HP prontos para as proximas etapas.

## Requisitos para instalar em outra maquina

Instale antes:

- Python 3.11 ou superior.
- Git.

Depois clone o projeto:

```powershell
git clone https://gitlab.com/vlemosr/treiner-dex.git
cd treiner-dex
```

Crie e ative um ambiente virtual:

```powershell
python -m venv servidor
.\servidor\Scripts\activate
```

Instale as dependencias:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Prepare o banco de dados:

```powershell
python manage.py migrate
```

Rode o servidor:

```powershell
python manage.py runserver
```

Depois acesse:

```text
http://127.0.0.1:8000/
```

O acesso administrativo do TrainerDex ja esta pronto, sem precisar criar usuario no banco:

```text
Login: admin
Senha: admin
```

Depois de entrar, o painel de usuarios fica disponivel em:

```text
http://127.0.0.1:8000/conta/admin/usuarios/
```

Nesse painel, o administrador pode visualizar todos os usuarios criados no sistema e apagar contas cadastradas quando necessario.

## Endpoints principais

### Paginas de conta

- `GET /conta/entrar/`: exibe a tela de login.
- `POST /conta/entrar/`: autentica usuario comum por usuario/e-mail e senha. Tambem aceita o acesso fixo `admin` / `admin` para abrir o painel administrativo do TrainerDex.
- `POST /conta/sair/`: encerra a sessao atual.
- `GET /conta/cadastro/`: exibe a tela de cadastro.
- `POST /conta/cadastro/`: cria uma conta comum e redireciona para a criacao do primeiro personagem.

### Painel administrativo do TrainerDex

- `GET /conta/admin/usuarios/`: lista todos os usuarios criados no banco. Requer login pelo acesso fixo `admin` / `admin`.
- `POST /conta/admin/usuarios/<user_id>/excluir/`: exclui o usuario informado e seus dados relacionados, como personagens, inventario, amigos, Pokedex e missoes.

O painel administrativo permite ao admin acompanhar as contas cadastradas e remover usuarios diretamente pela interface.

### Dashboard e personagens

- `GET /`: exibe o dashboard principal do treinador autenticado. Se a conta ainda nao tiver personagem, redireciona para a criacao de perfil.
- `GET /treinador/criar/`: exibe o formulario para criar personagem.
- `POST /treinador/criar/`: cria um novo personagem para a conta logada.
- `POST /treinador/<profile_id>/selecionar/`: define o personagem ativo da sessao.
- `POST /treinador/<profile_id>/excluir/`: exclui um personagem da conta, exceto o primeiro personagem criado.
- `POST /treinador/editar/`: atualiza os dados do personagem ativo.
- `POST /treinador/senha/`: troca a senha da conta logada.

### Mochila e equipe

- `POST /treinador/equipe/atualizar/`: adiciona ou remove Pokemon da equipe ativa via requisicao AJAX.
- `POST /inventario/item/<item_id>/excluir/`: remove um item da mochila do personagem ativo.

### Amigos

- `GET /amigos/`: lista amigos do personagem ativo e permite filtrar por cla.
- `POST /amigos/`: cadastra um novo amigo para o personagem ativo.
- `POST /amigos/<friend_id>/convidar/`: marca o convite do amigo como enviado.
- `DELETE /amigos/<friend_id>/excluir/`: exclui um amigo via AJAX.
- `POST /amigos/<friend_id>/excluir/`: exclui um amigo via formulario comum.

### Missoes

- `POST /missoes/<mission_key>/concluir/`: marca uma missao como concluida para o personagem ativo e aplica a recompensa de XP.

### Pokedex

- `GET /pokedex/buscar/`: busca Pokemon por nome, numero ou tipo. Aceita `q` como termo de busca e `registered=1` para mostrar apenas registrados.
- `POST /pokedex/registrar/`: registra um Pokemon na Pokedex do personagem ativo pelo nome informado.
- `POST /pokedex_register/`: alias de compatibilidade para registrar Pokemon.

## Como executar

Se o projeto ja estiver instalado na maquina:

```powershell
.\servidor\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Depois acesse `http://127.0.0.1:8000/`.

## Testes

```powershell
python manage.py test
```
