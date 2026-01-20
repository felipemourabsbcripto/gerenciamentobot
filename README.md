# Crypto Portfolio Telegram Bot

Um bot Telegram para gerenciamento de carteira de criptomoedas com integração CoinGecko.

## 🚀 Funcionalidades

- 📊 **Gerenciamento de Carteira**: Adicione, visualize e gerencie seus ativos de criptomoedas
- 🔔 **Alertas Automáticos**:
  - 🔴 Alerta quando um ativo cai **30%+** (oportunidade de preço médio)
  - 🟢 Alerta quando um ativo sobe **100%+** (recomendação de venda parcial de 50%)
- 📈 **Integração CoinGecko**: Dados de preços em tempo real
- 💹 **Cálculo de Preço Médio**: Registre novas compras e calcule automaticamente o preço médio
- 📤 **Registro de Vendas**: Acompanhe vendas parciais e lucros realizados
- ⌨️ **Interface Inline**: Toda interação através de botões inline para melhor usabilidade

## 📁 Estrutura do Projeto

```
gerenciamentobot/
├── main.py                     # Ponto de entrada principal
├── requirements.txt            # Dependências do projeto
├── .env.example               # Exemplo de variáveis de ambiente
├── data/                      # Banco de dados SQLite
├── logs/                      # Arquivos de log
└── src/
    ├── bot/
    │   ├── bot.py             # Classe principal do bot
    │   └── handlers/
    │       ├── commands.py    # Handlers de comandos
    │       ├── callbacks.py   # Handlers de callbacks (botões)
    │       └── messages.py    # Handlers de mensagens
    ├── config/
    │   └── settings.py        # Configurações da aplicação
    ├── database/
    │   ├── database.py        # Gerenciador de conexão
    │   └── repositories/      # Repositórios de dados
    ├── models/
    │   └── models.py          # Modelos SQLAlchemy
    ├── services/
    │   ├── coingecko_service.py  # Serviço de API CoinGecko
    │   └── price_monitor.py      # Monitor de preços
    └── utils/
        ├── keyboards.py       # Teclados inline
        ├── formatters.py      # Formatadores de mensagens
        └── logger.py          # Configuração de logging
```

## ⚙️ Configuração

### 1. Criar ambiente virtual e instalar dependências

```bash
cd /Users/felipemoura/Desktop/gerenciamentobot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

Copie o arquivo de exemplo e configure suas credenciais:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas credenciais:

```env
# Token do seu bot Telegram (obtenha com @BotFather)
TELEGRAM_BOT_TOKEN=seu_token_aqui

# API Key do CoinGecko (opcional, mas recomendado)
COINGECKO_API_KEY=sua_api_key_aqui

# Intervalo de verificação de preços (em minutos)
PRICE_CHECK_INTERVAL_MINUTES=5

# Limiares de alerta
DROP_THRESHOLD_PERCENT=30
PROFIT_THRESHOLD_PERCENT=100
SELL_RECOMMENDATION_PERCENT=50
```

### 3. Criar o bot no Telegram

1. Abra o Telegram e busque por `@BotFather`
2. Envie o comando `/newbot`
3. Siga as instruções para criar seu bot
4. Copie o token fornecido para o arquivo `.env`

### 4. Obter API Key do CoinGecko (Opcional)

1. Acesse [CoinGecko API](https://www.coingecko.com/api)
2. Crie uma conta ou faça login
3. Gere uma API Key
4. Copie para o arquivo `.env`

## 🚀 Executando o Bot

```bash
# Ativar ambiente virtual (se ainda não estiver ativo)
source venv/bin/activate

# Executar o bot
python main.py
```

## 📱 Comandos do Bot

| Comando | Descrição |
|---------|-----------|
| `/start` | Iniciar o bot e ver mensagem de boas-vindas |
| `/menu` | Abrir menu principal |
| `/portfolio` | Ver sua carteira de ativos |
| `/help` | Ver ajuda e instruções |

## 🎮 Funcionalidades do Menu

- **📊 Minha Carteira**: Visualize todos os seus ativos com valores atualizados
- **➕ Adicionar Ativo**: Busque e adicione novas criptomoedas à sua carteira
- **🔍 Buscar Moeda**: Pesquise informações sobre qualquer criptomoeda
- **📈 Top Moedas**: Veja as 10 principais moedas por capitalização
- **⚙️ Configurações**: Configure API Key, Portfolio ID e notificações
- **🔔 Alertas**: Veja seus alertas recentes

## 🔔 Sistema de Alertas

### Alerta de Queda (30%+)
Quando um ativo desvaloriza mais de 30% em relação ao preço de compra:
- Você recebe uma notificação
- Recomendação de fazer preço médio
- Opção de registrar nova compra diretamente

### Alerta de Lucro (100%+)
Quando um ativo valoriza 100% ou mais:
- Você recebe uma notificação
- Recomendação de venda parcial de 50%
- O alerta se repete a cada nova alta de 100%
- Opção de registrar venda diretamente

## 📊 Gerenciamento de Ativos

### Adicionar Ativo
1. Clique em "➕ Adicionar Ativo"
2. Digite o nome ou símbolo da moeda
3. Selecione a moeda na lista
4. Informe a quantidade
5. Informe o preço de compra

### Fazer Preço Médio
1. Acesse os detalhes do ativo
2. Clique em "➕ Preço Médio"
3. Informe a quantidade adicional comprada
4. Informe o preço da nova compra
5. O sistema calcula automaticamente o novo preço médio

### Registrar Venda
1. Acesse os detalhes do ativo
2. Clique em "📤 Registrar Venda"
3. Informe a quantidade vendida
4. Informe o preço de venda
5. O sistema calcula e mostra o lucro/prejuízo

## 🛠️ Tecnologias Utilizadas

- **Python 3.10+**
- **python-telegram-bot**: Framework para bots Telegram
- **SQLAlchemy**: ORM para banco de dados
- **aiohttp**: Cliente HTTP assíncrono
- **APScheduler**: Agendamento de tarefas
- **Pydantic**: Validação de dados

## 📝 Licença

MIT License
