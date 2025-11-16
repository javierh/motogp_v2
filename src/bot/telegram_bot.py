"""
Telegram Bot
Main bot implementation with command handlers
"""

import asyncio
from datetime import datetime
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from src.config import settings
from src.database import get_db
from src.database.models import User, Race, Category, Rider
from src.services import BettingService, ScoringService
from src.utils.logger import logger

# Conversation states
(
    SELECT_CATEGORY,
    SELECT_RACE_TYPE,
    SELECT_FIRST,
    SELECT_SECOND,
    SELECT_THIRD,
    CONFIRM_BET
) = range(6)


class NovaPorraBot:
    """NovaPorra Telegram Bot"""
    
    def __init__(self):
        self.app = Application.builder().token(settings.telegram_bot_token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup command and callback handlers"""
        
        # Basic commands
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("ayuda", self.cmd_help))
        
        # Betting commands
        bet_conv = ConversationHandler(
            entry_points=[CommandHandler("apostar", self.cmd_bet_start)],
            states={
                SELECT_CATEGORY: [CallbackQueryHandler(self.bet_select_category)],
                SELECT_RACE_TYPE: [CallbackQueryHandler(self.bet_select_race_type)],
                SELECT_FIRST: [CallbackQueryHandler(self.bet_select_first)],
                SELECT_SECOND: [CallbackQueryHandler(self.bet_select_second)],
                SELECT_THIRD: [CallbackQueryHandler(self.bet_select_third)],
                CONFIRM_BET: [CallbackQueryHandler(self.bet_confirm)],
            },
            fallbacks=[CommandHandler("cancelar", self.cmd_cancel)],
        )
        self.app.add_handler(bet_conv)
        
        # Other commands
        self.app.add_handler(CommandHandler("misapuestas", self.cmd_my_bets))
        self.app.add_handler(CommandHandler("clasificacion", self.cmd_standings))
        self.app.add_handler(CommandHandler("proximas", self.cmd_upcoming_races))
        
        logger.info("Bot handlers configured")
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # Register user in database
        with get_db() as db:
            db_user = db.query(User).filter(User.telegram_id == user.id).first()
            
            if not db_user:
                db_user = User(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name
                )
                db.add(db_user)
                db.commit()
                
                welcome_msg = (
                    f"¡Bienvenido {user.first_name}! 🏍️\n\n"
                    "Has sido registrado en NovaPorra, el sistema de apuestas de MotoGP.\n\n"
                    "Usa /ayuda para ver todos los comandos disponibles."
                )
            else:
                welcome_msg = (
                    f"¡Hola de nuevo {user.first_name}! 🏍️\n\n"
                    "Usa /ayuda para ver los comandos disponibles."
                )
        
        await update.message.reply_text(welcome_msg)
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ayuda command"""
        help_text = (
            "📋 *Comandos Disponibles*\n\n"
            "*Apuestas:*\n"
            "/apostar - Realizar una nueva apuesta\n"
            "/editar - Modificar apuesta existente\n"
            "/misapuestas - Ver tus apuestas actuales\n\n"
            "*Información:*\n"
            "/proximas - Ver próximas carreras\n"
            "/clasificacion - Ver clasificación del campeonato\n"
            "/resultados - Ver resultados de última carrera\n"
            "/tiempos - Consultar tiempos de entrenamientos\n\n"
            "*Ayuda:*\n"
            "/ayuda - Mostrar esta ayuda\n"
            "/cancelar - Cancelar operación actual\n\n"
            "🏍️ ¡Buena suerte con tus apuestas!"
        )
        
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def cmd_bet_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start betting conversation"""
        user = update.effective_user
        
        with get_db() as db:
            # Get current event races
            categories = db.query(Category).filter(Category.is_active == True).all()
            
            if not categories:
                await update.message.reply_text(
                    "No hay categorías disponibles en este momento."
                )
                return ConversationHandler.END
            
            # Create category selection keyboard
            keyboard = []
            for cat in categories:
                keyboard.append([
                    InlineKeyboardButton(
                        cat.name,
                        callback_data=f"cat_{cat.id}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "🏍️ *Nueva Apuesta*\n\n"
                "Selecciona la categoría:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
            return SELECT_CATEGORY
    
    async def bet_select_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle category selection"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel":
            await query.edit_message_text("❌ Apuesta cancelada")
            return ConversationHandler.END
        
        category_id = int(query.data.split("_")[1])
        context.user_data["bet_category_id"] = category_id
        
        with get_db() as db:
            category = db.query(Category).filter(Category.id == category_id).first()
            
            # Get available races for this category
            # TODO: Filter by current event
            races = db.query(Race).filter(
                Race.category_id == category_id,
                Race.status.in_(["upcoming", "betting_open"])
            ).all()
            
            if not races:
                await query.edit_message_text(
                    f"No hay carreras disponibles para {category.name}"
                )
                return ConversationHandler.END
            
            # Create race type selection keyboard
            keyboard = []
            for race in races:
                time_left = BettingService.get_time_until_close(race)
                keyboard.append([
                    InlineKeyboardButton(
                        f"{race.race_type.name} - {time_left}",
                        callback_data=f"race_{race.id}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("⬅️ Atrás", callback_data="back")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📅 Categoría: *{category.name}*\n\n"
                "Selecciona la carrera:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
            return SELECT_RACE_TYPE
    
    async def bet_select_race_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle race type selection"""
        query = update.callback_query
        await query.answer()
        
        race_id = int(query.data.split("_")[1])
        context.user_data["bet_race_id"] = race_id
        
        with get_db() as db:
            race = db.query(Race).filter(Race.id == race_id).first()
            
            # Get riders for this category
            # TODO: Filter by season and category
            riders = db.query(Rider).limit(20).all()
            
            if not riders:
                await query.edit_message_text("No hay pilotos disponibles")
                return ConversationHandler.END
            
            # Create rider selection keyboard
            keyboard = []
            for rider in riders:
                keyboard.append([
                    InlineKeyboardButton(
                        f"#{rider.number} {rider.first_name} {rider.last_name}",
                        callback_data=f"rider1_{rider.id}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("⬅️ Atrás", callback_data="back")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🏆 *Primera Posición*\n\n"
                f"Carrera: {race.race_type.name}\n"
                f"Categoría: {race.category.name}\n\n"
                "Selecciona el piloto:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
            return SELECT_FIRST
    
    async def bet_select_first(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle first place selection"""
        query = update.callback_query
        await query.answer()
        
        rider_id = int(query.data.split("_")[1])
        context.user_data["bet_first"] = rider_id
        
        with get_db() as db:
            race_id = context.user_data["bet_race_id"]
            race = db.query(Race).filter(Race.id == race_id).first()
            riders = db.query(Rider).filter(Rider.id != rider_id).limit(20).all()
            
            keyboard = []
            for rider in riders:
                keyboard.append([
                    InlineKeyboardButton(
                        f"#{rider.number} {rider.first_name} {rider.last_name}",
                        callback_data=f"rider2_{rider.id}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("⬅️ Atrás", callback_data="back")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🥈 *Segunda Posición*\n\n"
                f"Carrera: {race.race_type.name}\n"
                f"Categoría: {race.category.name}\n\n"
                "Selecciona el piloto:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
            return SELECT_SECOND
    
    async def bet_select_second(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle second place selection"""
        query = update.callback_query
        await query.answer()
        
        rider_id = int(query.data.split("_")[1])
        context.user_data["bet_second"] = rider_id
        
        with get_db() as db:
            race_id = context.user_data["bet_race_id"]
            race = db.query(Race).filter(Race.id == race_id).first()
            
            first_id = context.user_data["bet_first"]
            riders = db.query(Rider).filter(
                Rider.id.notin_([first_id, rider_id])
            ).limit(20).all()
            
            keyboard = []
            for rider in riders:
                keyboard.append([
                    InlineKeyboardButton(
                        f"#{rider.number} {rider.first_name} {rider.last_name}",
                        callback_data=f"rider3_{rider.id}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("⬅️ Atrás", callback_data="back")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🥉 *Tercera Posición*\n\n"
                f"Carrera: {race.race_type.name}\n"
                f"Categoría: {race.category.name}\n\n"
                "Selecciona el piloto:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
            return SELECT_THIRD
    
    async def bet_select_third(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle third place selection"""
        query = update.callback_query
        await query.answer()
        
        rider_id = int(query.data.split("_")[1])
        context.user_data["bet_third"] = rider_id
        
        with get_db() as db:
            race_id = context.user_data["bet_race_id"]
            race = db.query(Race).filter(Race.id == race_id).first()
            
            first = db.query(Rider).filter(Rider.id == context.user_data["bet_first"]).first()
            second = db.query(Rider).filter(Rider.id == context.user_data["bet_second"]).first()
            third = db.query(Rider).filter(Rider.id == rider_id).first()
            
            keyboard = [
                [InlineKeyboardButton("✅ Confirmar", callback_data="confirm")],
                [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            bet_summary = (
                f"🏍️ *Confirma tu apuesta*\n\n"
                f"📅 Carrera: {race.race_type.name}\n"
                f"🏁 Categoría: {race.category.name}\n\n"
                f"🥇 1º: #{first.number} {first.first_name} {first.last_name}\n"
                f"🥈 2º: #{second.number} {second.first_name} {second.last_name}\n"
                f"🥉 3º: #{third.number} {third.first_name} {third.last_name}\n\n"
                f"⏱️ Cierre: {BettingService.get_time_until_close(race)}"
            )
            
            await query.edit_message_text(
                bet_summary,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
            return CONFIRM_BET
    
    async def bet_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm and save bet"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel":
            await query.edit_message_text("❌ Apuesta cancelada")
            return ConversationHandler.END
        
        user = update.effective_user
        
        with get_db() as db:
            db_user = db.query(User).filter(User.telegram_id == user.id).first()
            
            bet, message = BettingService.create_bet(
                db,
                db_user.id,
                context.user_data["bet_race_id"],
                context.user_data["bet_first"],
                context.user_data["bet_second"],
                context.user_data["bet_third"]
            )
            
            if bet:
                await query.edit_message_text(f"✅ {message}")
            else:
                await query.edit_message_text(f"❌ Error: {message}")
        
        return ConversationHandler.END
    
    async def cmd_my_bets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's active bets"""
        user = update.effective_user
        
        with get_db() as db:
            db_user = db.query(User).filter(User.telegram_id == user.id).first()
            if not db_user:
                await update.message.reply_text("No estás registrado. Usa /start")
                return
            
            bets = BettingService.get_user_active_bets(db, db_user.id)
            
            if not bets:
                await update.message.reply_text("No tienes apuestas activas")
                return
            
            message = "🎯 *Tus apuestas activas:*\n\n"
            
            for bet in bets:
                race = bet.race
                message += (
                    f"📅 {race.event.name}\n"
                    f"🏁 {race.category.name} - {race.race_type.name}\n"
                    f"🥇 #{bet.first_place.number} {bet.first_place.first_name} {bet.first_place.last_name}\n"
                    f"🥈 #{bet.second_place.number} {bet.second_place.first_name} {bet.second_place.last_name}\n"
                    f"🥉 #{bet.third_place.number} {bet.third_place.first_name} {bet.third_place.last_name}\n"
                    f"⏱️ Cierre: {BettingService.get_time_until_close(race)}\n\n"
                )
            
            await update.message.reply_text(message, parse_mode="Markdown")
    
    async def cmd_standings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show championship standings"""
        with get_db() as db:
            season = settings.current_season
            
            # Get global standings
            standings = ScoringService.get_global_standings(db, season, limit=10)
            
            if not standings:
                await update.message.reply_text("Todavía no hay clasificación")
                return
            
            message = f"🏆 *Clasificación Global {season}*\n\n"
            
            for i, standing in enumerate(standings, 1):
                user = standing.user
                name = user.first_name
                if user.username:
                    name = f"@{user.username}"
                
                message += (
                    f"{i}. {name} - *{standing.total_points} pts*\n"
                    f"   MotoGP: {standing.motogp_points} | "
                    f"Moto2: {standing.moto2_points} | "
                    f"Moto3: {standing.moto3_points}\n\n"
                )
            
            await update.message.reply_text(message, parse_mode="Markdown")
    
    async def cmd_upcoming_races(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show upcoming races"""
        with get_db() as db:
            races = db.query(Race).filter(
                Race.status.in_(["upcoming", "betting_open"])
            ).order_by(Race.race_datetime).limit(10).all()
            
            if not races:
                await update.message.reply_text("No hay carreras próximas")
                return
            
            message = "📅 *Próximas Carreras:*\n\n"
            
            for race in races:
                message += (
                    f"🏍️ {race.event.name}\n"
                    f"🏁 {race.category.name} - {race.race_type.name}\n"
                    f"📍 {race.event.circuit.name}\n"
                    f"⏱️ Cierre apuestas: {BettingService.get_time_until_close(race)}\n\n"
                )
            
            await update.message.reply_text(message, parse_mode="Markdown")
    
    async def cmd_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel current operation"""
        await update.message.reply_text("❌ Operación cancelada")
        return ConversationHandler.END
    
    async def run(self):
        """Run the bot"""
        logger.info("Starting NovaPorra Bot...")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        
        # Keep the bot running
        try:
            await asyncio.Event().wait()
        finally:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
