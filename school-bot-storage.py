import os
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("DBMOD1.school-bot-storage.Storage")

DEVELOPER  = "DBMOD1 Development\nAuthor: TheQarden"
SCHOOL     = ""
BOT_NAME   = "school-bot-storage"
ABSOLUTE   = "Алматы"
VERSION    = "1.9"

ALLOWED_IDS: list[int] = [
  8763819613,
]

TOKEN = ""

STORAGE_DIR = f"school_{SCHOOL}_docs"
DATA_FILE   = f"school_{SCHOOL}_index.json"
os.makedirs(STORAGE_DIR, exist_ok=True)

IC = {
    "folder":   "📁",
    "star":     "⭐",
    "category": "📂",
    "search":   "🔍",
    "help":     "ℹ️",
    "delete":   "🗑",
    "back":     "◀️",
    "next":     "▶️",
    "check":    "✅",
    "warning":  "⚠️",
    "error":    "❌",
    "doc":      "📄",
    "house":    "🏫",
    "gear":     "⚙️",
    "pin":      "📌",
    "time":     "⏰",
    "tag":      "#️⃣",
    "stats":    "📊",
    "id_card":  "🆔",
    "lock":     "🔒",
    "rocket":   "👑",
    "crown":    "📍",
}

_EMPTY_DB: dict = {
    "docs":       {},
    "favorites":  [],
    "categories": {},
    "stats":      {"total": 0, "last_added": None},
}


def _load_db() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return json.loads(json.dumps(_EMPTY_DB))


def _dump_db(db: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as fh:
        json.dump(db, fh, ensure_ascii=False, indent=2)


_db         = _load_db()
docs        = _db["docs"]
favorites   = _db["favorites"]
categories  = _db["categories"]
db_stats    = _db["stats"]


def _persist() -> None:
    db_stats["total"]   = len(docs)
    _db["docs"]         = docs
    _db["favorites"]    = favorites
    _db["categories"]   = categories
    _db["stats"]        = db_stats
    _dump_db(_db)


def _allowed(user_id: int) -> bool:
    return user_id in ALLOWED_IDS


def _denied_msg(user_id: int) -> str:
    return (
        f"⛔ *Доступ запрещён*\n\n"
        f"{IC['id_card']} Ваш аккаунт ID: `{user_id}`\n\n"
        f"Бот доступен только сотрудникам School {SCHOOL}.\n"
        f"Для получения доступа обратитесь к {DEVELOPER}."
    )


def kb_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Все документы", callback_data="menu_list_all")],
        [
            InlineKeyboardButton("Избранное", callback_data="menu_list_fav"),
            InlineKeyboardButton("Категории", callback_data="menu_categories"),
        ],
        [
            InlineKeyboardButton("Поиск", callback_data="menu_search"),
            InlineKeyboardButton("Статистика", callback_data="menu_stats"),
        ],
        [
            InlineKeyboardButton("Помощь", callback_data="menu_help"),
            InlineKeyboardButton("О боте", callback_data="menu_about"),
        ],
    ])


def kb_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{IC['back']} Главное меню", callback_data="menu_main")],
    ])


def kb_doc(doc_name: str) -> InlineKeyboardMarkup:
    fav_btn = (
        InlineKeyboardButton(f"{IC['error']} Убрать из избранного", callback_data=f"doc_unfav_{doc_name}")
        if doc_name in favorites
        else InlineKeyboardButton(f"{IC['star']} В избранное", callback_data=f"doc_fav_{doc_name}")
    )
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{IC['doc']} Получить файл", callback_data=f"doc_get_{doc_name}")],
        [fav_btn, InlineKeyboardButton(f"{IC['delete']} Удалить", callback_data=f"doc_del_{doc_name}")],
        [InlineKeyboardButton(f"{IC['back']} Главное меню", callback_data="menu_main")],
    ])


def kb_doc_list(names: list[str], page: int = 0, prefix: str = "list") -> InlineKeyboardMarkup:
    per_page = 10
    total    = len(names)
    start    = page * per_page
    end      = min(start + per_page, total)
    rows     = []

    for name in names[start:end]:
        label = (f"{IC['star']} " if name in favorites else "") + (name[:37] + "…" if len(name) > 40 else name)
        rows.append([InlineKeyboardButton(label, callback_data=f"select_{name}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(f"{IC['back']} Назад",    callback_data=f"page_{prefix}_{page - 1}"))
    if end < total:
        nav.append(InlineKeyboardButton(f"Вперёд {IC['next']}", callback_data=f"page_{prefix}_{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton(f"{IC['house']} Главное меню", callback_data="menu_main")])
    return InlineKeyboardMarkup(rows)


def kb_categories() -> InlineKeyboardMarkup | None:
    active = {k: v for k, v in categories.items() if v}
    if not active:
        return None
    rows = [
        [InlineKeyboardButton(f"{IC['category']} {cat} ({len(docs_)})", callback_data=f"cat_view_{cat}")]
        for cat, docs_ in active.items()
    ]
    rows.append([InlineKeyboardButton(f"{IC['back']} Главное меню", callback_data="menu_main")])
    return InlineKeyboardMarkup(rows)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not _allowed(user_id):
        await update.message.reply_text(_denied_msg(user_id), parse_mode="Markdown")
        return

    context.user_data.clear()
    await update.message.reply_text(
                   f"{IC['house']} *Главное меню*\n\n{IC['id_card']} Ваш ID: `{user_id}`",
        reply_markup=kb_main(),
        parse_mode="Markdown",
    )


async def on_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not _allowed(user_id):
        await update.message.reply_text(_denied_msg(user_id), parse_mode="Markdown")
        return

    tg_file      = await update.message.document.get_file()
    orig_name    = update.message.document.file_name
    file_id      = update.message.document.file_id
    local_path   = os.path.join(STORAGE_DIR, f"{file_id}_{orig_name}")
    await tg_file.download_to_drive(local_path)

    context.user_data["pending_file"] = {"path": local_path, "original_name": orig_name}

    await update.message.reply_text(
        f"{IC['check']} *Файл получен!*\n\n"
        f"{IC['doc']} `{orig_name}`\n\n"
        f"{IC['tag']} *Введите название для архива:*\n"
        f"Можно добавить #категорию в конце\n\n"
        f"{IC['pin']} Пример: `Приказ {SCHOOL} #приказы`",
        parse_mode="Markdown",
    )


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not _allowed(user_id):
        await update.message.reply_text(_denied_msg(user_id), parse_mode="Markdown")
        return

    raw = update.message.text.strip()

    if context.user_data.get("search_mode"):
        context.user_data.pop("search_mode", None)
        matches = [n for n in docs if raw.lower() in n.lower()]
        if matches:
            rows = [
                [InlineKeyboardButton(
                    (f"{IC['star']} " if n in favorites else "") + n[:40],
                    callback_data=f"select_{n}",
                )]
                for n in matches[:15]
            ]
            rows.append([InlineKeyboardButton(f"{IC['back']} Главное меню", callback_data="menu_main")])
            await update.message.reply_text(
                f"{IC['search']} *Найдено {len(matches)}:*",
                reply_markup=InlineKeyboardMarkup(rows),
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                f"{IC['error']} *Ничего не найдено*",
                reply_markup=kb_back(),
                parse_mode="Markdown",
            )
        return

    if "pending_file" not in context.user_data:
        await update.message.reply_text(
            f"{IC['error']} Сначала отправьте файл",
            reply_markup=kb_back(),
        )
        return

    category  = "без категории"
    clean     = []
    for word in raw.split():
        if word.startswith("#"):
            category = word[1:].lower()
        else:
            clean.append(word)

    name = " ".join(clean) if clean else raw

    if name in docs:
        await update.message.reply_text(
            f"{IC['warning']} *Документ с таким названием уже есть!*",
            reply_markup=kb_back(),
            parse_mode="Markdown",
        )
        return

    fi = context.user_data.pop("pending_file")
    docs[name] = {
        "path":          fi["path"],
        "original_name": fi["original_name"],
        "date":          datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "category":      category,
        "added_by":      ABSOLUTE,
    }
    categories.setdefault(category, [])
    if name not in categories[category]:
        categories[category].append(name)

    db_stats["last_added"] = name
    _persist()

    await update.message.reply_text(
        f"{IC['check']} *{name}* - сохранён!\n"
        f"{IC['category']} Категория: {category}\n\n"
        f"👇 Управление:",
        reply_markup=kb_doc(name),
        parse_mode="Markdown",
    )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    query   = update.callback_query
    await query.answer()

    if not _allowed(user_id):
        await query.message.reply_text(_denied_msg(user_id), parse_mode="Markdown")
        return

    data = query.data

    if data == "menu_main":
        await query.edit_message_text(
            f"{IC['house']} *Главное меню*\n\n{IC['id_card']} Ваш ID: `{user_id}`",
            reply_markup=kb_main(),
            parse_mode="Markdown",
        )

    elif data == "menu_myid":
        await query.edit_message_text(
            f"{IC['id_card']} *Ваш Telegram ID*\n\n"
            f"`{user_id}`\n\n"
            f"{IC['pin']} Чтобы добавить этот ID в доступ:\n"
            f"1. Скопируйте этот номер\n"
            f"2. Отправьте разработчику {DEVELOPER}\n"
            f"3. ID будет добавлен в ALLOWED\\_IDS\n\n",
            reply_markup=kb_back(),
            parse_mode="Markdown",
        )

    elif data == "menu_list_all":
        if not docs:
            await query.edit_message_text(
                f"{IC['folder']} *Архив пуст*",
                reply_markup=kb_back(),
                parse_mode="Markdown",
            )
            return
        names = list(docs.keys())
        context.user_data["current_list"] = names
        await query.edit_message_text(
            f"{IC['folder']} *Все документы* - {len(names)} шт.",
            reply_markup=kb_doc_list(names, 0, "all"),
            parse_mode="Markdown",
        )

    elif data == "menu_list_fav":
        fav_names = [n for n in favorites if n in docs]
        if not fav_names:
            await query.edit_message_text(
                f"{IC['star']} *Избранное пусто*",
                reply_markup=kb_back(),
                parse_mode="Markdown",
            )
            return
        context.user_data["current_list"] = fav_names
        await query.edit_message_text(
            f"{IC['star']} *Избранное* - {len(fav_names)} шт.",
            reply_markup=kb_doc_list(fav_names, 0, "fav"),
            parse_mode="Markdown",
        )

    elif data == "menu_categories":
        kb = kb_categories()
        if not kb:
            await query.edit_message_text(
                f"{IC['category']} *Категорий нет*\nДобавляйте #тег при сохранении файла.",
                reply_markup=kb_back(),
                parse_mode="Markdown",
            )
            return
        await query.edit_message_text(
            f"{IC['category']} *Категории*",
            reply_markup=kb,
            parse_mode="Markdown",
        )

    elif data.startswith("cat_view_"):
        cat_name  = data[9:]
        cat_docs  = categories.get(cat_name, [])
        if cat_docs:
            context.user_data["current_list"] = cat_docs
            await query.edit_message_text(
                f"{IC['category']} *{cat_name}* - {len(cat_docs)} шт.",
                reply_markup=kb_doc_list(cat_docs, 0, f"cat_{cat_name}"),
                parse_mode="Markdown",
            )

    elif data == "menu_search":
        context.user_data["search_mode"] = True
        await query.edit_message_text(
            f"{IC['search']} *Поиск*\n\nВведите название или его часть:",
            reply_markup=kb_back(),
            parse_mode="Markdown",
        )

    elif data == "menu_stats":
        total_docs = len(docs)
        total_fav  = len(favorites)
        total_cats = sum(1 for v in categories.values() if v)
        cats_lines = "\n".join(
            f"  {IC['category']} {c}: {len(v)}" for c, v in categories.items() if v
        )[:500] or "  Нет категорий"

        await query.edit_message_text(
            f"{IC['stats']} *Статистика - School {SCHOOL}*\n\n"
            f"{IC['doc']} Документов: {total_docs}\n"
            f"{IC['star']} В избранном: {total_fav}\n"
            f"{IC['category']} Категорий: {total_cats}\n"
            f"{IC['time']} Последний: {db_stats.get('last_added', '-')}\n\n"
            f"{cats_lines}\n\n"
            f"{IC['rocket']} {DEVELOPER} | School {SCHOOL}",
            reply_markup=kb_back(),
            parse_mode="Markdown",
        )

    elif data == "menu_help":
        await query.edit_message_text(
            f"{IC['help']} *Помощь*\n\n"
            f"📎 Отправь файл → введи название\n"
            f"{IC['search']} Поиск → введи название\n"
            f"{IC['star']} Избранное → нажми на документ\n"
            f"{IC['delete']} Удаление → нажми «Удалить»\n"
            f"{IC['category']} Категории → добавь #тег при сохранении\n\n"
            f"{IC['rocket']} {DEVELOPER} | School {SCHOOL}",
            reply_markup=kb_back(),
            parse_mode="Markdown",
        )

    elif data == "menu_about":
        await query.edit_message_text(
            f"{IC['gear']} *О боте*\n\n"
            f"🤖 {BOT_NAME} v{VERSION}\n"
            f"{IC['rocket']} {DEVELOPER} Development\n"
            f"{IC['house']} School {SCHOOL}\n"
            f"{IC['crown']} {ABSOLUTE}\n\n"
            f"📅 2026 | {IC['lock']} Доступ только по ID\n"
            f"📁 Хранилище: `{STORAGE_DIR}`",
            reply_markup=kb_back(),
            parse_mode="Markdown",
        )

    elif data.startswith("select_"):
        doc_name = data[7:]
        if doc_name in docs:
            d = docs[doc_name]
            await query.edit_message_text(
                f"{IC['doc']} *{doc_name}*\n\n"
                f"📅 {d['date']}\n"
                f"{IC['category']} {d['category']}\n"
                f"📎 {d['original_name']}\n\n"
                f"👇 Управление:",
                reply_markup=kb_doc(doc_name),
                parse_mode="Markdown",
            )

    elif data.startswith("doc_get_"):
        doc_name = data[8:]
        if doc_name in docs:
            with open(docs[doc_name]["path"], "rb") as fh:
                await query.message.reply_document(
                    document=fh,
                    filename=docs[doc_name]["original_name"],
                    caption=f"{IC['doc']} {doc_name}",
                )

    elif data.startswith("doc_fav_"):
        doc_name = data[8:]
        if doc_name not in favorites:
            favorites.append(doc_name)
            _persist()
        await query.edit_message_reply_markup(reply_markup=kb_doc(doc_name))

    elif data.startswith("doc_unfav_"):
        doc_name = data[10:]
        if doc_name in favorites:
            favorites.remove(doc_name)
            _persist()
        await query.edit_message_reply_markup(reply_markup=kb_doc(doc_name))

    elif data.startswith("doc_del_"):
        doc_name = data[8:]
        if doc_name in docs:
            cat = docs[doc_name]["category"]
            if cat in categories and doc_name in categories[cat]:
                categories[cat].remove(doc_name)
            if doc_name in favorites:
                favorites.remove(doc_name)
            local_path = docs[doc_name]["path"]
            if os.path.exists(local_path):
                os.remove(local_path)
            del docs[doc_name]
            _persist()
            logger.info("DBMOD1.school-bot-storage - удалён документ: %s", doc_name)

        await query.message.reply_text(
            f"{IC['delete']} *{doc_name}* удалён",
            parse_mode="Markdown",
        )
        await query.edit_message_text(
            f"{IC['house']} *Главное меню*",
            reply_markup=kb_main(),
            parse_mode="Markdown",
        )

    elif data.startswith("page_"):
        parts = data.split("_", 2)
        if len(parts) == 3:
            prefix, page = parts[1], int(parts[2])
            names = context.user_data.get("current_list", [])
            if names:
                await query.edit_message_reply_markup(reply_markup=kb_doc_list(names, page, prefix))


def main() -> None:
    banner = (
        f"\n{'=' * 52}\n"
              f"Доступные ID: {ALLOWED_IDS}\n"
        f"Хранилище: {STORAGE_DIR}\n"
        f"{'=' * 52}\n"
    )
    print(banner)

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.Document.ALL, on_document))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    logger.info("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
