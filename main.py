import asyncio
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart

# ВСТАВЬ СВОЙ НОВЫЙ ТОКЕН СЮДА (после Revoke у BotFather):
BOT_TOKEN = "8794922534:AAFgZcdhtgiYvywJh_iauIV7KCc-TRMd_w4"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==========================================
# ИГРОВАЯ БАЗА ДАННЫХ В ПАМЯТИ (ОЗУ)
# ==========================================
# Данные игроков сотрутся ТОЛЬКО если ты сам перезапустишь процесс скрипта
USERS_DB = {}

# ==========================================
# ИГРОВОЙ КОНТЕНТ (8 ОСТРОВОВ И ГЕНЕРАТОРЫ)
# ==========================================
ISLANDS = {
    1: {"name": "Ист Блу (Фууша)", "req_level": 1, "exp_min": 15, "exp_max": 35, "gold_min": 20, "gold_max": 50},
    2: {"name": "Арабаста", "req_level": 10, "exp_min": 50, "exp_max": 100, "gold_min": 80, "gold_max": 180},
    3: {"name": "Скайпия", "req_level": 25, "exp_min": 150, "exp_max": 300, "gold_min": 250, "gold_max": 500},
    4: {"name": "Эниес Лобби", "req_level": 45, "exp_min": 400, "exp_max": 750, "gold_min": 600, "gold_max": 1100},
    5: {"name": "Маринфорд", "req_level": 70, "exp_min": 900, "exp_max": 1600, "gold_min": 1300, "gold_max": 2400},
    6: {"name": "Вано (Страна Самураев)", "req_level": 100, "exp_min": 2000, "exp_max": 4000, "gold_min": 3500, "gold_max": 6500},
    7: {"name": "Эггхэд (Остров Будущего)", "req_level": 140, "exp_min": 5000, "exp_max": 9500, "gold_min": 8000, "gold_max": 15000},
    8: {"name": "Лаф Тейл (Рафтель)", "req_level": 200, "exp_min": 12000, "exp_max": 25000, "gold_min": 20000, "gold_max": 45000}
}

WEAPON_PREFIXES = ["Старый", "Ржавый", "Флотский", "Пиратский", "Острый", "Закаленный", "Тяжелый", "Кованый", "Проклятый", "Императорский"]
WEAPON_TYPES = ["Кортик", "Катана", "Сабля", "Нож", "Мушкет", "Топор", "Трезубец", "Алебарда", "Глефа", "Меч"]
WEAPON_SUFFIXES = ["Морского Дозора", "Нового Мира", "Рыболюдей", "Шанкса", "Вано", "Белоуса", "Михоука", "Небесных Волков", "Короля Пиратов", "Бездны"]

FRUITS_POOL = {
    "Common": [
        {"name": "Гому Гому но Ми (Резина)", "dmg": 20, "hp": 100, "price": 1500},
        {"name": "Бара Бара но Ми (Деление)", "dmg": 15, "hp": 150, "price": 1500},
        {"name": "Субе Субе но Ми (Гладкость)", "dmg": 10, "hp": 200, "price": 1200}
    ],
    "Rare": [
        {"name": "Моку Моку но Ми (Дым)", "dmg": 50, "hp": 350, "price": 4500},
        {"name": "Суна Суна но Ми (Песок)", "dmg": 65, "hp": 400, "price": 5500},
        {"name": "Бане Бане но Ми (Пружина)", "dmg": 40, "hp": 300, "price": 3500}
    ],
    "Epic": [
        {"name": "Мера Мера но Ми (Огонь)", "dmg": 130, "hp": 800, "price": 15000},
        {"name": "Горо Горо но Ми (Молния)", "dmg": 160, "hp": 700, "price": 18000},
        {"name": "Хиэ Хиэ но Ми (Лёд)", "dmg": 140, "hp": 900, "price": 16500}
    ],
    "Legendary": [
        {"name": "Гула Гула но Ми (Трясение)", "dmg": 350, "hp": 2000, "price": 50000},
        {"name": "Ями Ями но Ми (Тьма)", "dmg": 400, "hp": 1800, "price": 55000},
        {"name": "Уо Уо но Ми: Сейрю (Дракон)", "dmg": 450, "hp": 2500, "price": 65000}
    ],
    "Mythical": [
        {"name": "Хито Хито но Ми: Модель Ника", "dmg": 750, "hp": 5000, "price": 150000}
    ]
}

def generate_weapon_pool():
    weapons = []
    random.seed(42)  # Фиксированные 100 пушек
    for i in range(100):
        pref = random.choice(WEAPON_PREFIXES)
        w_type = random.choice(WEAPON_TYPES)
        suff = random.choice(WEAPON_SUFFIXES)
        dmg = int(10 + (i * 7.5) + random.randint(1, 15))
        rarity = "Common" if i < 40 else "Rare" if i < 70 else "Epic" if i < 90 else "Legendary"
        weapons.append({"id": i + 1, "name": f"{pref} {w_type} {suff}", "rarity": rarity, "dmg": dmg})
    return weapons

ALL_WEAPONS = generate_weapon_pool()

# ==========================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С СЛОВАРЕМ
# ==========================================
def get_or_create_user(user_id: int, username: str) -> dict:
    if user_id not in USERS_DB:
        USERS_DB[user_id] = {
            "user_id": user_id,
            "username": username,
            "level": 1,
            "exp": 0,
            "gold": 500,
            "bounty": 0,
            "weapon": "Кулаки",
            "weapon_dmg": 5,
            "fruit": "Нет",
            "fruit_dmg": 0,
            "fruit_hp": 0,
            "haki_level": 0,
            "inv_fruit": None
        }
    return USERS_DB[user_id]

# ==========================================
# ИНТЕРФЕЙС
# ==========================================
def main_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🏴‍☠️ Мой Профиль"), KeyboardButton(text="🧭 Отплыть на Остров")],
        [KeyboardButton(text="🎒 Трюм (Инвентарь)"), KeyboardButton(text="🏋️ Тренировать Хаки")],
        [KeyboardButton(text="📜 Листовки Розыска (Топ)")]
    ], resize_keyboard=True)

# ==========================================
# ХЭНДЛЕРЫ
# ==========================================
@dp.message(CommandStart())
async def start_cmd(message: Message):
    get_or_create_user(message.from_user.id, message.from_user.first_name)
    await message.answer(
        f"🌊 **Добро пожаловать на Гранд Лайн, {message.from_user.first_name}!**\n\n"
        "Перед тобой открыты **8 легендарных островов**. Путешествуй, уничтожай врагов, "
        "выбивай уникальное оружие из пула в **100 клинков** и ищи спрятанные Дьявольские Фрукты!\n\n"
        "Найденные фрукты падают в инвентарь, чтобы съесть ради силы или продать! 👑",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(F.text == "🏴‍☠️ Мой Профиль")
async def profile_cmd(message: Message):
    user = get_or_create_user(message.from_user.id, message.from_user.first_name)
    total_dmg = user['weapon_dmg'] + user['fruit_dmg'] + (user['haki_level'] * 35)
    exp_needed = user['level'] * 150
    
    text = (
        f"☠️ **Карточка Капитана: {user['username']}** ☠️\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌟 **Уровень:** {user['level']} `[{user['exp']}/{exp_needed} XP]`\n"
        f"💰 **Белли:** {user['gold']:,} ฿\n"
        f"🔥 **Награда (Bounty):** {user['bounty']:,} ฿\n\n"
        f"⚔️ **Оружие:** {user['weapon']} (+{user['weapon_dmg']} DMG)\n"
        f"🍇 **Активный Фрукт:** {user['fruit']} (+{user['fruit_dmg']} DMG)\n"
        f"🌌 **Воля (Хаки):** Уровень {user['haki_level']} (🦾 Усиление)\n"
        f"💥 **Общая Сила атаки:** {total_dmg} DMG"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "🧭 Отплыть на Остров")
async def choose_island(message: Message):
    user = get_or_create_user(message.from_user.id, message.from_user.first_name)
    
    available_islands = [v for k, v in ISLANDS.items() if user['level'] >= v['req_level']]
    current_island = available_islands[-1]
    
    await message.answer(f"⛵ Команда поднимает паруса. Направляемся на остров: **{current_island['name']}**...")
    await asyncio.sleep(1)
    
    earned_gold = random.randint(current_island['gold_min'], current_island['gold_max'])
    earned_exp = random.randint(current_island['exp_min'], current_island['exp_max'])
    earned_bounty = earned_gold * random.randint(5, 10)
    
    user['exp'] += earned_exp
    exp_needed = user['level'] * 150
    lvl_up_text = ""
    while user['exp'] >= exp_needed:
        user['exp'] -= exp_needed
        user['level'] += 1
        exp_needed = user['level'] * 150
        lvl_up_text = f"\n\n⚡ **NEW LEVEL UP!** Вы достигли **{user['level']} уровня**!"

    loot_text = ""
    roll = random.random()
    
    # Шанс найти фрукт (8%)
    if roll < 0.08:
        if user['inv_fruit'] is None:
            rarity_roll = random.choices(["Common", "Rare", "Epic", "Legendary", "Mythical"], weights=[50, 30, 14, 5, 1], k=1)[0]
            found_fruit = random.choice(FRUITS_POOL[rarity_roll])
            user['inv_fruit'] = found_fruit['name']
            loot_text = f"\n\n🍇 **НЕВЕРОЯТНО!** Вы нашли Дьявольский Фрукт: **{found_fruit['name']}** ({rarity_roll})! Он добавлен в инвентарь."
        else:
            loot_text = f"\n\n🍇 Вы заметили Дьявольский фрукт, но ваш инвентарь полон!"
            
    # Шанс выбить пушку из пула 100 шт (18%)
    elif roll < 0.26:
        drop = random.choice(ALL_WEAPONS)
        if drop['dmg'] > user['weapon_dmg']:
            user['weapon'] = f"{drop['name']} [{drop['rarity']}]"
            user['weapon_dmg'] = drop['dmg']
            loot_text = f"\n\n⚔️ **НОВОЕ ОРУЖИЕ!** Вы выбили клинок: **{drop['name']}** (+{drop['dmg']} DMG)!"
        else:
            scrap_gold = drop['dmg'] * 5
            earned_gold += scrap_gold
            loot_text = f"\n\n📦 Вы нашли *{drop['name']}* (Топ-{drop['id']}/100), но ваше оружие лучше. Продано за +{scrap_gold} ฿."

    user['gold'] += earned_gold
    user['bounty'] += earned_bounty
    
    report = (
        f"⚔️ **Зачистка на острове {current_island['name']}!**\n━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Найдено белли: **+{earned_gold:,} ฿**\n"
        f"✨ Опыт: **+{earned_exp} XP**\n"
        f"📈 Награда за голову: **+{earned_bounty:,} ฿**"
        f"{loot_text}{lvl_up_text}"
    )
    await message.answer(report, parse_mode="Markdown")

@dp.message(F.text == "🎒 Трюм (Инвентарь)")
async def inventory_cmd(message: Message):
    user = get_or_create_user(message.from_user.id, message.from_user.first_name)
    
    if not user['inv_fruit']:
        await message.answer("🎒 **Ваш инвентарь пуст.**\n\nПутешествуйте по островам (`🧭 Отплыть на Остров`), чтобы найти фрукты!")
        return
        
    fruit_info = None
    for rarity, list_fruits in FRUITS_POOL.items():
        for f in list_fruits:
            if f['name'] == user['inv_fruit']:
                fruit_info = f
                break
                
    text = (
        f"🎒 **Трюм вашего корабля:**\n━━━━━━━━━━━━━━━━━━━━\n"
        f"🍇 **Содержимое сундука:** {user['inv_fruit']}\n"
        f"💥 Дает при поедании: +{fruit_info['dmg']} DMG\n"
        f"💰 Цена продажи: {fruit_info['price']:,} Белли ฿\n\n"
        f"Используйте команды:\n"
        f"▶️ /eat — съесть фрукт\n"
        f"▶️ /sell — продать фрукт"
    )
    await message.answer(text)

@dp.message(F.text == "/eat")
async def eat_fruit_cmd(message: Message):
    user = get_or_create_user(message.from_user.id, message.from_user.first_name)
    if not user['inv_fruit']:
        await message.answer("❌ В инвентаре пусто!")
        return
        
    fruit_info = None
    for rarity, list_fruits in FRUITS_POOL.items():
        for f in list_fruits:
            if f['name'] == user['inv_fruit']:
                fruit_info = f
                break

    user['fruit'] = user['inv_fruit']
    user['fruit_dmg'] = fruit_info['dmg']
    user['fruit_hp'] = fruit_info['hp']
    user['inv_fruit'] = None
    
    await message.answer(
        f"🍇👅 **💥 ХРУСЬ! Вы съели Дьявольский Фрукт!**\n\n"
        f"Вы полностью освоили силу: **{fruit_info['name']}**.\n"
        f"Ваша атака выросла на **+{fruit_info['dmg']} DMG**!",
        reply_markup=main_keyboard()
    )

@dp.message(F.text == "/sell")
async def sell_fruit_cmd(message: Message):
    user = get_or_create_user(message.from_user.id, message.from_user.first_name)
    if not user['inv_fruit']:
        await message.answer("❌ Сундук пуст!")
        return
        
    fruit_info = None
    for rarity, list_fruits in FRUITS_POOL.items():
        for f in list_fruits:
            if f['name'] == user['inv_fruit']:
                fruit_info = f
                break

    user['gold'] += fruit_info['price']
    user['inv_fruit'] = None
    
    await message.answer(
        f"💰 **Сделка закрыта!** Вы продали фрукт за **+{fruit_info['price']:,} Белли ฿**!",
        reply_markup=main_keyboard()
    )

@dp.message(F.text == "🏋️ Тренировать Хаки")
async def train_haki(message: Message):
    user = get_or_create_user(message.from_user.id, message.from_user.first_name)
    cost = (user['haki_level'] + 1) * 3000
    
    if user['gold'] < cost:
        await message.answer(f"🏋️ Для тренировки Воли нужно **{cost:,} Белли ฿**.")
        return
    
    user['gold'] -= cost
    user['haki_level'] += 1
    
    await message.answer(
        f"🌌 **Уровень Хаки повышен до {user['haki_level']}!**\n"
        f"Получен мощный пассивный буст к атаке!"
    )

@dp.message(F.text == "📜 Листовки Розыска (Топ)")
async def show_top(message: Message):
    # Сортируем игроков из ОЗУ по величине награды
    sorted_users = sorted(USERS_DB.values(), key=lambda x: x['bounty'], reverse=True)[:10]
    
    text = "📜 **Самые опасные преступники Гранд Лайн (ТОП Наград):**\n━━━━━━━━━━━━━━━━━━━━\n"
    for idx, u in enumerate(sorted_users, 1):
        text += f"{idx}. 🏴‍屑️ `{u['username']}` — Награда: **{u['bounty']:,} ฿**\n"
    
    if not sorted_users:
        text += "Пока никого нет, стань первым!"
        
    await message.answer(text, parse_mode="Markdown")

async def main():
    print("=== [Скрипт One Piece RPG успешно запущен без БД. Весь прогресс в памяти!] ===")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
