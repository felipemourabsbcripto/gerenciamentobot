#!/bin/bash
# Script de setup para o Crypto Portfolio Bot

echo "==================================="
echo "  Crypto Portfolio Bot - Setup"
echo "==================================="

# Criar diretórios necessários
echo "[1/4] Criando diretórios..."
mkdir -p data logs

# Instalar dependências
echo "[2/4] Instalando dependências..."
pip install -r requirements.txt

# Instalar dependências adicionais
echo "[3/4] Instalando bibliotecas de dados de mercado..."
pip install ccxt pandas ta numpy

# Verificar instalação
echo "[4/4] Verificando instalação..."
python3 -c "
import sys
print(f'Python: {sys.version}')

modules = ['telegram', 'sqlalchemy', 'aiosqlite', 'apscheduler', 'pydantic', 'ccxt', 'pandas', 'ta']
for mod in modules:
    try:
        __import__(mod)
        print(f'✓ {mod}')
    except ImportError:
        print(f'✗ {mod} - NÃO INSTALADO')
"

echo ""
echo "==================================="
echo "  Setup concluído!"
echo "==================================="
echo ""
echo "Próximos passos:"
echo "1. Configure o arquivo .env com seu token do Telegram"
echo "   - Obtenha o token em @BotFather no Telegram"
echo ""
echo "2. Execute o bot:"
echo "   python main.py"
echo ""
