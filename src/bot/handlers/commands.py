"""
Telegram bot command handlers.
"""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from src.database import get_async_session, UserRepository, AssetRepository, AlertRepository
from src.database.repositories import AdminRepository
from src.utils import KeyboardBuilder, MessageFormatter
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - with mandatory registration."""
    user = update.effective_user
    
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        admin_repo = AdminRepository(session)
        
        # Get or create user
        db_user = await user_repo.get_or_create(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        await session.commit()
        
        # Check if user is banned
        if db_user.is_banned:
            await update.message.reply_text(
                "🚫 **Acesso Negado**\n\n"
                "Sua conta foi suspensa. Entre em contato com um administrador.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Check if user is fully registered
        if not db_user.is_registered:
            # Start registration flow
            context.user_data.clear()
            context.user_data['registration_step'] = 'name'
            
            await update.message.reply_text(
                "👋 **Bem-vindo ao Gerenciador de risco da comunidade!**\n\n"
                "⚠️ **ATENÇÃO: Cadastros incompletos serão banidos!**\n\n"
                "Para usar o bot, você precisa completar seu cadastro.\n\n"
                "**Dados necessários:**\n"
                "1️⃣ Nome completo\n"
                "2️⃣ Telefone (com DDD)\n"
                "3️⃣ Data de nascimento\n"
                "4️⃣ Capital para Futuros\n"
                "5️⃣ Quem te indicou\n\n"
                "📝 **Etapa 1/5 - Nome Completo**\n\n"
                "Digite seu **nome completo**:",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Check if user accepted terms
        if not db_user.accepted_terms:
            context.user_data['registration_step'] = 'terms'
            await show_terms(update, context, db_user.full_name)
            return
        
        # User is fully registered - show main menu
        # Check if user is admin
        is_admin = await admin_repo.is_admin(user.id)
    
    welcome_msg = MessageFormatter.welcome_message(db_user.full_name or user.first_name)
    
    await update.message.reply_text(
        welcome_msg,
        reply_markup=KeyboardBuilder.main_menu(),
        parse_mode=ParseMode.MARKDOWN
    )
    
    logger.info(f"User {user.id} ({db_user.full_name}) accessed the bot")


async def show_terms(update: Update, context: ContextTypes.DEFAULT_TYPE, user_name: str):
    """Show terms of use to user."""
    terms_message = f"""⚠️ **Aviso Importante**

Eu **{user_name}** estou ciente que o bot é um terminal de consulta e registro livre. Ao utilizá-lo, você está ciente de que:

**📋 Não há Verificação Real dos valores informados:** O sistema não exige prova de fundos nem valida a veracidade dos dados. O cadastro de um ativo aqui não serve como prova de posse ou existência real; aceitamos dados fictícios ou de teste.

**⚠️ Risco de Falhas:** Como qualquer software, o sistema está sujeito a bugs, erros de design e instabilidades do Telegram.

**📊 Uso Informativo:** Todas as sugestões e registros são apenas para organização pessoal e não constituem recomendação de investimento.

**Ao continuar, você assume total responsabilidade pelo uso das informações aqui inseridas e consultadas.**"""

    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(
            terms_message,
            reply_markup=KeyboardBuilder.accept_terms(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.callback_query.edit_message_text(
            terms_message,
            reply_markup=KeyboardBuilder.accept_terms(),
            parse_mode=ParseMode.MARKDOWN
        )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /menu command."""
    user = update.effective_user
    
    # Check if user is registered
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        db_user = await user_repo.get_by_telegram_id(user.id)
        
        if not db_user or not db_user.is_registered or not db_user.accepted_terms:
            await update.message.reply_text(
                "❌ Você precisa completar seu cadastro primeiro.\n\n"
                "Use /start para iniciar.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        if db_user.is_banned:
            await update.message.reply_text(
                "🚫 Sua conta foi suspensa.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
    
    await update.message.reply_text(
        "📱 **Menu Principal**\n\nSelecione uma opção:",
        reply_markup=KeyboardBuilder.main_menu(),
        parse_mode=ParseMode.MARKDOWN
    )


async def portfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /portfolio command."""
    user = update.effective_user
    
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        asset_repo = AssetRepository(session)
        
        db_user = await user_repo.get_by_telegram_id(user.id)
        if not db_user:
            await update.message.reply_text(
                "❌ Usuário não encontrado. Use /start primeiro.",
                reply_markup=KeyboardBuilder.back_to_menu()
            )
            return
        
        assets = await asset_repo.get_user_assets(db_user.id)
    
    message = MessageFormatter.portfolio_summary(assets)
    
    await update.message.reply_text(
        message,
        reply_markup=KeyboardBuilder.portfolio_actions(),
        parse_mode=ParseMode.MARKDOWN
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_msg = MessageFormatter.help_message()
    
    await update.message.reply_text(
        help_msg,
        reply_markup=KeyboardBuilder.back_to_menu(),
        parse_mode=ParseMode.MARKDOWN
    )
