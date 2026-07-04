import asyncio
import sqlite3
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart

# ВСТАВЬ СВОЙ ТОКЕН СЮДА:
BOT_TOKEN = "8999022213:AAH5RznzWZUlEbdf7DpgjJBbrxewjnrEkTk"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
DB_NAME = "one_piece_full_rpg.db"

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

# Шаблоны для генерации 100 видов оружия по тирам
WEAPON_PREFIXES = ["Старый", "Ржавый", "Флотский", "Пиратский", "Острый", "Закаленный", "Тяжелый", "Кованый", "Проклятый", "Императорский"]
WEAPON_TYPES = ["Кортик", "Катана", "Сабля", "Нож", "Мушкет", "Топор", "Трезубец", "Алебарда", "Глефа", "Меч"]
WEAPON_SUFFIXES = ["Морского Дозора", "Нового Мира", "Рыболюдей", "Шанкса", "Вано", "Белоуса", "Михоука", "Небесных Волков", "Короля Пиратов", "Бездны"]

# Дьявольские фрукты
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
    """Генерирует ровно 100 уникальных кастомных оружий с разным уроном"""
    weapons = []
    random.seed(42) # Чтобы пул всегда был фиксированным из 100 пушек
    for i in range(100):
        pref = random.choice(WEAPON_PREFIXES)
        w_type = random.choice(WEAPON_TYPES)
        suff = random.choice(WEAPON_SUFFIXES)
        
        # Чем дальше по списку, тем сильнее пушка
        dmg = int(10 + (i * 7.5) + random.randint(1, 15))
        
        if i < 40: rarity = "Common"
        elif i < 70: rarity = "Rare"
        elif i < 90: rarity = "Epic"
        else: rarity = "Legendary"
            
        weapons.append({
            "id": i + 1,
            "name": f"{pref} {w_type} {suff}",
            "rarity": rarity,
            "dmg": dmg
        })
    return weapons

ALL_WEAPONS = generate_weapon_pool()

# ==========================================
# РАБОТА С БАЗОЙ ДАННЫХ (БД)
# ==========================================

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            level INTEGER DEFAULT 1,
            exp INTEGER DEFAULT 0,
            gold INTEGER DEFAULT 500,
            bounty INTEGER DEFAULT 0,
            weapon TEXT DEFAULT "Кулаки",
            weapon_dmg INTEGER DEFAULT 5,
            fruit TEXT DEFAULT "Нет",
            fruit_dmg INTEGER DEFAULT 0,
            fruit_hp INTEGER DEFAULT 0,
            haki_level INTEGER DEFAULT 0,
            inv_fruit TEXT DEFAULT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_user(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def register_user(user_id: int, username: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def update_user(user_id: int, **kwargs):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    set_query = ", ".join([f"{key} = ?" for key in kwargs.keys()])
    values = list(kwargs.values()) + [user_id]
    cursor.execute(f"UPDATE users SET {set_query} WHERE user_id = ?", values)
    conn.commit()
    conn.close()

def get_top_players():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username, bounty FROM users ORDER BY bounty DESC LIMIT 10")
    top = cursor.fetchall()
    conn.close()
    return top

# ==========================================
# ИНТЕРФЕЙС И КНОПКИ
# ==========================================

def main_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🏴‍☠️ Мой Профиль"), KeyboardButton(text="🧭 Отплыть на Остров")],
        [KeyboardButton(text="🎒 Трюм (Инвентарь)"), KeyboardButton(text="🏋️ Тренировать Хаки")],
        [KeyboardButton(text="📜 Листовки Розыска (Топ)")]
    ], resize_keyboard=True)

# ==========================================
# ХЭНДЛЕРЫ ИГРЫ
# ==========================================

@dp.message(CommandStart())
async def start_cmd(message: Message):
    register_user(message.from_user.id, message.from_user.first_name)
    await message.answer(
        f"🌊 **Добро пожаловать на Гранд Лайн, {message.from_user.first_name}!**\n\n"
        "Перед тобой открыты **8 легендарных островов**. Путешествуй, уничтожай врагов, "
        "выбивай уникальное оружие из пула в **100 клинков** и ищи спрятанные Дьявольские Фрукты!\n\n"
        "Найденные фрукты можно складывать в инвентарь, чтобы съесть ради безумной силы или продать на черном рынке! 👑",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(F.text == "🏴‍☠️ Мой Профиль")
async def profile_cmd(message: Message):
    user = get_user(message.from_user.id)
    if not user: return
    
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
    user = get_user(message.from_user.id)
    if not user: return
    
    # Подбираем самый сильный остров, доступный игроку по уровню
    available_islands = [v for k, v in ISLANDS.items() if user['level'] >= v['req_level']]
    current_island = available_islands[-1]
    
    await message.answer(f"⛵ Команда поднимает паруса. Направляемся на остров: **{current_island['name']}**...")
    await asyncio.sleep(1.2)
    
    earned_gold = random.randint(current_island['gold_min'], current_island['gold_max'])
    earned_exp = random.randint(current_island['exp_min'], current_island['exp_max'])
    earned_bounty = earned_gold * random.randint(5, 10)
    
    # Расчет уровня
    new_exp = user['exp'] + earned_exp
    new_level = user['level']
    exp_needed = new_level * 150
    lvl_up_text = ""
    while new_exp >= exp_needed:
        new_exp -= exp_needed
        new_level += 1
        exp_needed = new_level * 150
        lvl_up_text = f"\n\n⚡ **NEW LEVEL UP!** Вы достигли **{new_level} уровня**!"

    loot_text = ""
    new_weapon = user['weapon']
    new_weapon_dmg = user['weapon_dmg']
    new_inv_fruit = user['inv_fruit']
    
    roll = random.random()
    
    # 1. Шанс найти Дьявольский фрукт (8%)
    if roll < 0.08:
        if user['inv_fruit'] is None: # Если слот в инвентаре пуст
            rarity_roll = random.choices(["Common", "Rare", "Epic", "Legendary", "Mythical"], weights=[50, 30, 14, 5, 1], k=1)[0]
            found_fruit = random.choice(FRUITS_POOL[rarity_roll])
            new_inv_fruit = found_fruit['name']
            loot_text = f"\n\n🍇 **НЕВЕРОЯТНО!** На побережье острова вы нашли выброшенный волнами Дьявольский Фрукт: **{found_fruit['name']}** ({rarity_roll})! Он бережно спрятан в ваш инвентарь."
        else:
            loot_text = f"\n\n🍇 Вы заметили Дьявольский фрукт в густых зарослях, но ваш инвентарь полон! Вы не смогли забрать его."
            
    # 2. Шанс выбить оружие из 100 существующих (18%)
    elif roll < 0.26:
        # Случайно выбираем пушку из ВСЕГО пула в 100 штук
        drop = random.choice(ALL_WEAPONS)
        if drop['dmg'] > user['weapon_dmg']:
            new_weapon = f"{drop['name']} [{drop['rarity']}]"
            new_weapon_dmg = drop['dmg']
            loot_text = f"\n\n⚔️ **НОВОЕ ОРУЖИЕ!** Вы победили сильного босса и забрали его клинок: **{drop['name']}** (+{drop['dmg']} DMG)!"
        else:
            scrap_gold = drop['dmg'] * 5
            earned_gold += scrap_gold
            loot_text = f"\n\n📦 Вы нашли *{drop['name']}* (Топ-{drop['id']}/100), но ваше текущее оружие смертоноснее. Клинок сдан торговцу за +{scrap_gold} ฿."

    update_user(
        user['user_id'], 
        gold=user['gold'] + earned_gold, 
        exp=new_exp, 
        level=new_level, 
        bounty=user['bounty'] + earned_bounty,
        weapon=new_weapon,
        weapon_dmg=new_weapon_dmg,
        inv_fruit=new_inv_fruit
    )
    
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
    user = get_user(message.from_user.id)
    if not user: return
    
    if not user['inv_fruit']:
        await message.answer("🎒 **Ваш инвентарь пуст.**\n\nПутешествуйте по островам (`🧭 Отплыть на Остров`), чтобы найти спрятанные Дьявольские Фрукты!")
        return
        
    # Ищем инфу о фрукте в пуле, чтобы показать цену и статы
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
        f"💰 Цена продажи скупщику: {fruit_info['price']:,} Белли ฿\n\n"
        f"Используйте команды:\n"
        f"▶️ /eat — съесть фрукт (заменит ваш текущий фрукт)\n"
        f"▶️ /sell — продать фрукт торговцу"
    )
    await message.answer(text)

@dp.message(F.text == "/eat")
async def eat_fruit_cmd(message: Message):
    user = get_user(message.from_user.id)
    if not user or not user['inv_fruit']:
        await message.answer("❌ У вас в инвентаре нет фрукта, который можно съесть!")
        return
        
    fruit_info = None
    for rarity, list_fruits in FRUITS_POOL.items():
        for f in list_fruits:
            if f['name'] == user['inv_fruit']:
                fruit_info = f
                break

    update_user(
        user['user_id'],
        fruit=user['inv_fruit'],
        fruit_dmg=fruit_info['dmg'],
        fruit_hp=fruit_info['hp'],
        inv_fruit=None # Очищаем инвентарь
    )
    
    await message.answer(
        f"🍇👅 **💥 ХРУСЬ! Вы откусили Дьявольский Фрукт!**\n\n"
        f"Тело переполняет невероятная энергия природы! Вы полностью освоили: **{fruit_info['name']}**.\n"
        f"Ваша базовая атака выросла на **+{fruit_info['dmg']} DMG**!",
        reply_markup=main_keyboard()
    )

@dp.message(F.text == "/sell")
async def sell_fruit_cmd(message: Message):
    user = get_user(message.from_user.id)
    if not user or not user['inv_fruit']:
        await message.answer("❌ Продавать нечего. Сундук пуст!")
        return
        
    fruit_info = None
    for rarity, list_fruits in FRUITS_POOL.items():
        for f in list_fruits:
            if f['name'] == user['inv_fruit']:
                fruit_info = f
                break

    new_gold = user['gold'] + fruit_info['price']
    update_user(user['user_id'], gold=new_gold, inv_fruit=None)
    
    await message.answer(
        f"💰 **Сделка закрыта!** Вы продали {user['inv_fruit']} подпольному брокеру на черном рынке за **+{fruit_info['price']:,} Белли ฿**!",
        reply_markup=main_keyboard()
    )

@dp.message(F.text == "🏋️ Тренировать Хаки")
async def train_haki(message: Message):
    user = get_user(message.from_user.id)
    cost = (user['haki_level'] + 1) * 3000
    
    if user['gold'] < cost:
        await message.answer(f"🏋️ Тренировка продвинутой Воли требует спаррингов и сосредоточения. Нужно **{cost:,} Белли ฿**.")
        return
    
    new_haki = user['haki_level'] + 1
    update_user(user['user_id'], gold=user['gold'] - cost, haki_level=new_haki)
    
    await message.answer(
        f"🌌 **Вы провели недели на заброшенном острове, оттачивая Волю!**\n"
        f"Ваша Хаки поднялась до уровня **{new_haki}**!\n"
        f"Каждый уровень Хаки теперь дает огромный пассивный буст к атаке!"
    )

@dp.message(F.text == "📜 Листовки Розыска (Топ)")
async def show_top(message: Message):
    top_players = get_top_players()
    text = "📜 **Самые опасные преступники Гранд Лайн (ТОП Наград):**\n━━━━━━━━━━━━━━━━━━━━\n"
    for idx, player in enumerate(top_players, 1):
        text += f"{idx}. 🏴‍☠️ `{player[0]}` — Награда: **{player[1]:,} ฿**\n"
    await message.answer(text, parse_mode="Markdown")

# ==========================================
# ЗАПУСК ИГРЫ
# ==========================================
async def main():
    init_db()
    print("=== [Скрипт One Piece RPG успешно запущен. Поднимите Веселого Роджера!] ===")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
