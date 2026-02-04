from math import ceil
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

MRP = 4325

# ---------- КОЭФФИЦИЕНТЫ ----------
def get_width_coef(w):
    if w <= 2.55:
        return 0
    elif w <= 3:
        return 0.009
    elif w <= 3.75:
        return 0.019
    else:
        return 0.038

def get_height_coef(h):
    if h <= 4:
        return 0
    elif h <= 4.5:
        return 0.009
    elif h <= 5:
        return 0.018
    else:
        return 0.036

def get_length_coef(length, car_type):
    norm = 12 if car_type == "одиночный" else 24
    excess = length - norm
    if excess <= 0:
        return 0
    return ceil(excess) * 0.004

# ---------- КНОПКИ ТИПА ТС ----------
def vehicle_type_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🚚 Одиночный", callback_data="одиночный"),
                InlineKeyboardButton("🚛 Автопоезд", callback_data="автопоезд"),
            ]
        ]
    )

# ---------- START / RESET ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Выберите тип транспортного средства:",
        reply_markup=vehicle_type_keyboard(),
    )

# ---------- ВЫБОР ТИПА ----------
async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data.clear()
    context.user_data["car_type"] = query.data
    context.user_data["step"] = "width"

    await query.message.reply_text("📏 Введите ширину (м):")

# ---------- ОБРАБОТКА ВВОДА ----------
async def input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step")

    try:
        value = float(update.message.text)
    except:
        await update.message.reply_text("❌ Пожалуйста, введите число")
        return

    if step == "width":
        context.user_data["width"] = value
        context.user_data["step"] = "height"
        await update.message.reply_text("📐 Введите высоту (м):")

    elif step == "height":
        context.user_data["height"] = value
        context.user_data["step"] = "length"
        await update.message.reply_text("📦 Введите длину (м):")

    elif step == "length":
        context.user_data["length"] = value
        context.user_data["step"] = "km"
        await update.message.reply_text("🛣 Введите расстояние (км):")

    elif step == "km":
        context.user_data["km"] = value
        await calculate(update, context)

# ---------- РАСЧЁТ ----------
async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    car_type = context.user_data["car_type"]
    width = context.user_data["width"]
    height = context.user_data["height"]
    length = context.user_data["length"]
    km = context.user_data["km"]

    k_w = get_width_coef(width)
    k_h = get_height_coef(height)
    k_l = get_length_coef(length, car_type)

    total = (k_w + k_h + k_l) * km * MRP

    text = (
        "📊 *Результат расчёта*\n\n"
        f"🚘 Тип ТС: *{car_type}*\n"
        f"📏 Ширина: {width} м → `{k_w}`\n"
        f"📐 Высота: {height} м → `{k_h}`\n"
        f"📦 Длина: {length} м → `{k_l}`\n"
        f"🛣 Расстояние: {km} км\n"
        f"💵 МРП: {MRP} ₸\n\n"
        f"💰 *ИТОГО: {round(total, 2)} ₸*"
    )

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔄 Рассчитать ещё раз", callback_data="restart")]]
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )

# ---------- КНОПКА ПОВТОРА ----------
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data.clear()
    await query.message.reply_text(
        "Начнём заново 👇",
        reply_markup=vehicle_type_keyboard(),
    )

# ---------- ЗАПУСК ----------
app = ApplicationBuilder().token("8466450462:AAGChpolmJQdkLknax1ODU7RIFz4HjTCqyU").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(restart, pattern="^restart$"))
app.add_handler(CallbackQueryHandler(choose_type))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, input_handler))

app.run_polling()
