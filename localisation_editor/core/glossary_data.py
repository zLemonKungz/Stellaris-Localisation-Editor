"""
Embedded Stellaris Thai translation glossary.
Built into the program — no external file needed.
Contains 260+ authoritative term translations organized by category.
"""

BUILTIN_GLOSSARY = [
    # ── Core Game Terms ──
    {"english": "empire", "thai": "จักรวรรดิ", "category": "core"},
    {"english": "species", "thai": "สปีชีส์", "category": "core", "alt": "เผ่าพันธุ์"},
    {"english": "pop", "thai": "ประชากร", "category": "core"},
    {"english": "planet", "thai": "ดาวเคราะห์", "category": "core"},
    {"english": "star", "thai": "ดาวฤกษ์", "category": "core"},
    {"english": "system", "thai": "ระบบดาว", "category": "core"},
    {"english": "galaxy", "thai": "ดาราจักร", "category": "core"},
    {"english": "sector", "thai": "ภาค", "category": "core"},
    {"english": "colony", "thai": "อาณานิคม", "category": "core"},
    {"english": "origin", "thai": "ต้นกำเนิด", "category": "core"},
    {"english": "technology", "thai": "เทคโนโลยี", "category": "core"},
    {"english": "research", "thai": "การวิจัย", "category": "core"},
    {"english": "tradition", "thai": "จารีต", "category": "core"},
    {"english": "leader", "thai": "ผู้นำ", "category": "core"},
    {"english": "ruler", "thai": "ผู้ปกครอง", "category": "core"},
    {"english": "governor", "thai": "ผู้ว่าการ", "category": "core"},
    {"english": "scientist", "thai": "นักวิทยาศาสตร์", "category": "core"},
    {"english": "enemy", "thai": "ศัตรู", "category": "core"},
    {"english": "ethic", "thai": "จริยธรรม", "category": "core"},
    {"english": "authority", "thai": "ระบอบการปกครอง", "category": "core"},
    {"english": "unity", "thai": "เอกภาพ", "category": "core"},
    {"english": "influence", "thai": "อิทธิพล", "category": "core"},
    {"english": "resource", "thai": "ทรัพยากร", "category": "core"},

    # ── Ethics ──
    {"english": "xenophile", "thai": "มนุษย์ต่างดาวนิยม", "category": "ethics"},
    {"english": "xenophobe", "thai": "เกลียดกลัวมนุษย์ต่างดาว", "category": "ethics"},
    {"english": "militarist", "thai": "ทหารนิยม", "category": "ethics"},
    {"english": "pacifist", "thai": "สันตินิยม", "category": "ethics"},
    {"english": "materialist", "thai": "วัตถุนิยม", "category": "ethics"},
    {"english": "spiritualist", "thai": "จิตวิญญาณนิยม", "category": "ethics"},
    {"english": "egalitarian", "thai": "เสมอภาคนิยม", "category": "ethics"},
    {"english": "authoritarian", "thai": "อำนาจนิยม", "category": "ethics"},
    {"english": "gestalt consciousness", "thai": "จิตสำนึกรวมหมู่", "category": "ethics"},
    {"english": "hive mind", "thai": "จิตผึ้ง", "category": "ethics"},
    {"english": "machine intelligence", "thai": "ปัญญาประดิษฐ์เครื่องจักร", "category": "ethics"},

    # ── Authorities ──
    {"english": "democracy", "thai": "ประชาธิปไตย", "category": "authority"},
    {"english": "oligarchy", "thai": "คณาธิปไตย", "category": "authority"},
    {"english": "dictatorship", "thai": "เผด็จการ", "category": "authority"},
    {"english": "imperial", "thai": "จักรวรรดิ", "category": "authority"},
    {"english": "hive mind authority", "thai": "ระบอบจิตผึ้ง", "category": "authority"},
    {"english": "machine intelligence authority", "thai": "ระบอบปัญญาประดิษฐ์", "category": "authority"},

    # ── Military ──
    {"english": "fleet", "thai": "กองเรือ", "category": "military"},
    {"english": "starbase", "thai": "สถานีอวกาศ", "category": "military", "alt": "สเตชั่นอวกาศ"},
    {"english": "army", "thai": "กองทัพ", "category": "military"},
    {"english": "ship", "thai": "ยานอวกาศ", "category": "military", "alt": "ยาน"},
    {"english": "admiral", "thai": "พลเรือเอก", "category": "military"},
    {"english": "general", "thai": "พลเอก", "category": "military"},
    {"english": "war", "thai": "สงคราม", "category": "military"},
    {"english": "weapon", "thai": "อาวุธ", "category": "military"},
    {"english": "armor", "thai": "เกราะ", "category": "military"},
    {"english": "shield", "thai": "โล่", "category": "military"},
    {"english": "corvette", "thai": "คอร์เวท", "category": "military"},
    {"english": "destroyer", "thai": "พิฆาต", "category": "military"},
    {"english": "cruiser", "thai": "ครูเซอร์", "category": "military"},
    {"english": "battleship", "thai": "เดรดนอต", "category": "military"},
    {"english": "titan", "thai": "ไททัน", "category": "military"},
    {"english": "colossus", "thai": "คอลอสซัส", "category": "military"},
    {"english": "juggernaut", "thai": "จักรนอท", "category": "military"},
    {"english": "science ship", "thai": "ยานวิทยาศาสตร์", "category": "military"},
    {"english": "construction ship", "thai": "ยานก่อสร้าง", "category": "military"},
    {"english": "colony ship", "thai": "ยานตั้งอาณานิคม", "category": "military"},

    # ── Diplomacy ──
    {"english": "diplomacy", "thai": "การทูต", "category": "diplomacy"},
    {"english": "espionage", "thai": "การจารกรรม", "category": "diplomacy"},
    {"english": "federation", "thai": "สหพันธ์", "category": "diplomacy"},
    {"english": "galactic community", "thai": "ประชาคมดาราจักร", "category": "diplomacy"},
    {"english": "enclave", "thai": "อาณาจักรอิสระ", "category": "diplomacy"},
    {"english": "curator", "thai": "ผู้ดูแลความรู้", "category": "diplomacy"},
    {"english": "artisan troupe", "thai": "คณะศิลปิน", "category": "diplomacy"},
    {"english": "merchant enclave", "thai": "อาณาจักรพ่อค้า", "category": "diplomacy"},
    {"english": "ally", "thai": "พันธมิตร", "category": "diplomacy"},
    {"english": "peace", "thai": "สันติภาพ", "category": "diplomacy"},
    {"english": "treaty", "thai": "สนธิสัญญา", "category": "diplomacy"},
    {"english": "alliance", "thai": "พันธมิตร", "category": "diplomacy"},
    {"english": "non-aggression pact", "thai": "สนธิสัญญาไม่รุกราน", "category": "diplomacy"},
    {"english": "guarantee", "thai": "การค้ำประกัน", "category": "diplomacy"},
    {"english": "embassy", "thai": "สถานทูต", "category": "diplomacy"},

    # ── Economy ──
    {"english": "trade", "thai": "การค้า", "category": "economy"},
    {"english": "alloy", "thai": "อัลลอย", "category": "economy"},
    {"english": "consumer goods", "thai": "สินค้าอุปโภคบริโภค", "category": "economy"},
    {"english": "food", "thai": "อาหาร", "category": "economy"},
    {"english": "mineral", "thai": "แร่ธาตุ", "category": "economy"},
    {"english": "energy", "thai": "พลังงาน", "category": "economy"},
    {"english": "strategic resource", "thai": "ทรัพยากรเชิงยุทธศาสตร์", "category": "economy"},
    {"english": "trade value", "thai": "มูลค่าการค้า", "category": "economy"},
    {"english": "district", "thai": "เขต", "category": "economy"},
    {"english": "job", "thai": "อาชีพ", "category": "economy"},
    {"english": "stratum", "thai": "ชั้นทางสังคม", "category": "economy"},
    {"english": "credit", "thai": "เครดิต", "category": "economy"},
    {"english": "building", "thai": "สิ่งก่อสร้าง", "category": "economy"},
    {"english": "upkeep", "thai": "ค่าบำรุงรักษา", "category": "economy"},
    {"english": "income", "thai": "รายได้", "category": "economy"},
    {"english": "expense", "thai": "รายจ่าย", "category": "economy"},

    # ── Exploration ──
    {"english": "anomaly", "thai": "ความผิดปกติ", "category": "exploration"},
    {"english": "archaeology site", "thai": "แหล่งโบราณคดี", "category": "exploration"},
    {"english": "relic", "thai": "โบราณวัตถุ", "category": "exploration"},
    {"english": "archaeology", "thai": "โบราณคดี", "category": "exploration"},
    {"english": "excavation", "thai": "การขุดค้น", "category": "exploration"},
    {"english": "digsite", "thai": "แหล่งขุดค้น", "category": "exploration"},
    {"english": "situation", "thai": "สถานการณ์", "category": "exploration"},
    {"english": "first contact", "thai": "การพบครั้งแรก", "category": "exploration"},
    {"english": "observation", "thai": "การสังเกตการณ์", "category": "exploration"},

    # ── Gameplay ──
    {"english": "hyperlane", "thai": "ไฮเปอร์เลน", "category": "gameplay"},
    {"english": "FTL", "thai": "การเดินทางเร็วกว่าแสง", "category": "gameplay"},
    {"english": "ascension perk", "thai": "ศักยภาพการเลื่อนขั้น", "category": "gameplay"},
    {"english": "fallen empire", "thai": "จักรวรรดิที่ร่วงหล่น", "category": "gameplay"},
    {"english": "awakened empire", "thai": "จักรวรรดิที่ตื่นแล้ว", "category": "gameplay"},
    {"english": "crisis", "thai": "วิกฤตการณ์", "category": "gameplay"},
    {"english": "megastructure", "thai": "โครงสร้างขนาดยักษ์", "category": "gameplay", "alt": "เมกะสตรัคเจอร์"},
    {"english": "edict", "thai": "พระบรมราชโองการ", "category": "gameplay", "alt": "คำสั่ง"},
    {"english": "decision", "thai": "การตัดสินใจ", "category": "gameplay"},
    {"english": "habitability", "thai": "ความสามารถในการอยู่อาศัย", "category": "gameplay"},
    {"english": "stability", "thai": "เสถียรภาพ", "category": "gameplay"},
    {"english": "crime", "thai": "อาชญากรรม", "category": "gameplay"},
    {"english": "amenities", "thai": "สิ่งอำนวยความสะดวก", "category": "gameplay"},
    {"english": "shroud", "thai": "อาภรณ์", "category": "gameplay"},
    {"english": "psionics", "thai": "พลังจิต", "category": "gameplay"},
    {"english": "synthetic", "thai": "สังเคราะห์", "category": "gameplay"},
    {"english": "genetic", "thai": "พันธุกรรม", "category": "gameplay"},
    {"english": "cybernetics", "thai": "ไซเบอร์เนติกส์", "category": "gameplay"},
    {"english": "nanite", "thai": "นาไนต์", "category": "gameplay"},
    {"english": "leviathan", "thai": "ลีไวอาธาน", "category": "gameplay"},
    {"english": "guardian", "thai": "ผู้พิทักษ์", "category": "gameplay"},
    {"english": "modifier", "thai": "ตัวปรับ", "category": "gameplay"},
    {"english": "origin", "thai": "ต้นกำเนิด", "category": "gameplay"},
    {"english": "civic", "thai": "ลักษณะสังคม", "category": "gameplay"},
    {"english": "tradition", "thai": "จารีต", "category": "gameplay"},

    # ── Megastructures ──
    {"english": "ringworld", "thai": "โลกวงแหวน", "category": "megastructure"},
    {"english": "habitat", "thai": "ที่อยู่อาศัย", "category": "megastructure"},
    {"english": "dyson sphere", "thai": "ทรงกลมไดสัน", "category": "megastructure"},
    {"english": "science nexus", "thai": "ศูนย์รวมวิทยาศาสตร์", "category": "megastructure"},
    {"english": "sentry array", "thai": "ชุดเฝ้าระวัง", "category": "megastructure"},
    {"english": "strategic coordination center", "thai": "ศูนย์ประสานงานยุทธศาสตร์", "category": "megastructure"},
    {"english": "mega shipyard", "thai": "อู่ต่อเรือเมกะ", "category": "megastructure"},
    {"english": "matter decompressor", "thai": "เครื่องย่อยสลายสสาร", "category": "megastructure"},
    {"english": "ecumenopolis", "thai": "เมืองทั้งโลก", "category": "megastructure"},

    # ── Planet Types ──
    {"english": "continental", "thai": "ทวีป", "category": "planet"},
    {"english": "oceanic", "thai": "มหาสมุทร", "category": "planet"},
    {"english": "tropical", "thai": "เขตร้อน", "category": "planet"},
    {"english": "arid", "thai": "แห้งแล้ง", "category": "planet"},
    {"english": "desert", "thai": "ทะเลทราย", "category": "planet"},
    {"english": "tundra", "thai": "ทุนดรา", "category": "planet"},
    {"english": "arctic", "thai": "อาร์กติก", "category": "planet"},
    {"english": "alpine", "thai": "อัลไพน์", "category": "planet"},
    {"english": "gaia", "thai": "ไกอา", "category": "planet"},
    {"english": "machine world", "thai": "โลกจักรกล", "category": "planet"},
    {"english": "hive world", "thai": "โลกรังผึ้ง", "category": "planet"},
    {"english": "ecu", "thai": "อีคิว", "category": "planet", "notes": "Ecumenopolis abbreviation"},

    # ── DLC Content ──
    {"english": "Utopia", "thai": "ยูโทเปีย", "category": "dlc"},
    {"english": "Apocalypse", "thai": "วันสิ้นโลก", "category": "dlc"},
    {"english": "Megacorp", "thai": "เมกะคอร์ป", "category": "dlc"},
    {"english": "Synthetic Dawn", "thai": "รุ่งอรุณสังเคราะห์", "category": "dlc"},
    {"english": "Leviathans", "thai": "ลีไวอาธาน", "category": "dlc"},
    {"english": "Distant Stars", "thai": "ดวงดาวไกลโพ้น", "category": "dlc"},
    {"english": "Ancient Relics", "thai": "โบราณวัตถุ", "category": "dlc"},
    {"english": "Federations", "thai": "สหพันธ์", "category": "dlc"},
    {"english": "Nemesis", "thai": "ศัตรูคูณแค้น", "category": "dlc"},
    {"english": "Overlord", "thai": "จอมทัพ", "category": "dlc"},
    {"english": "First Contact", "thai": "การพบครั้งแรก", "category": "dlc"},
    {"english": "Galactic Paragons", "thai": "ยอดมนุษย์ดาราจักร", "category": "dlc"},
    {"english": "Astral Planes", "thai": "มิติดาว", "category": "dlc"},
    {"english": "Cosmic Storms", "thai": "พายุจักรวาล", "category": "dlc"},
    {"english": "Machine Age", "thai": "ยุคจักรกล", "category": "dlc"},
    {"english": "Grand Archive", "thai": "บันทึกใหญ่", "category": "dlc"},
    {"english": "Biogenesis", "thai": "ชีวกำเนิด", "category": "dlc"},
    {"english": "Aquatics", "thai": "ชาวน้ำ", "category": "dlc"},
    {"english": "Toxoids", "thai": "ชาวพิษ", "category": "dlc"},
    {"english": "Necroids", "thai": "ชาวเนโคร", "category": "dlc"},
    {"english": "Lithoids", "thai": "ชาวหิน", "category": "dlc"},
    {"english": "Plantoids", "thai": "ชาวพืช", "category": "dlc"},
    {"english": "Humanoids", "thai": "มนุษย์", "category": "dlc"},

    # ── Ship Components / Tech ──
    {"english": "laser", "thai": "เลเซอร์", "category": "tech"},
    {"english": "plasma", "thai": "พลาสมา", "category": "tech"},
    {"english": "kinetic", "thai": "จลนศาสตร์", "category": "tech"},
    {"english": "missile", "thai": "ขีปนาวุธ", "category": "tech"},
    {"english": "strike craft", "thai": "อากาศยานรบ", "category": "tech"},
    {"english": "point defense", "thai": "ป้องกันจุด", "category": "tech"},
    {"english": "flak", "thai": "ปืนต่อสู้อากาศ", "category": "tech"},
    {"english": "hyperdrive", "thai": "ไฮเปอร์ไดรฟ์", "category": "tech"},
    {"english": "warp drive", "thai": "วาร์ปไดรฟ์", "category": "tech"},
    {"english": "jump drive", "thai": "จั๊มป์ไดรฟ์", "category": "tech"},
    {"english": "sensor", "thai": "เซนเซอร์", "category": "tech"},
    {"english": "computer", "thai": "คอมพิวเตอร์", "category": "tech"},
    {"english": "thruster", "thai": "ทรัสเตอร์", "category": "tech"},
    {"english": "reactor", "thai": "เครื่องปฏิกรณ์", "category": "tech"},
    {"english": "FTL drive", "thai": "ไดรฟ์ FTL", "category": "tech"},

    # ── Origins ──
    {"english": "prosperous unification", "thai": "การรวมชาติที่รุ่งเรือง", "category": "origin"},
    {"english": "remnants", "thai": "เศษซาก", "category": "origin"},
    {"english": "hegemon", "thai": "เจ้าอำนาจ", "category": "origin"},
    {"english": "mechanist", "thai": "จักรกลนิยม", "category": "origin"},
    {"english": "syncretic evolution", "thai": "วิวัฒนาการผสมผสาน", "category": "origin"},
    {"english": "doomsday", "thai": "วันสิ้นโลก", "category": "origin"},
    {"english": "void dweller", "thai": "ผู้อาศัยในห้วงอวกาศ", "category": "origin"},
    {"english": "clone army", "thai": "กองทัพโคลน", "category": "origin"},
    {"english": "necrophage", "thai": "เนโครฟาจ", "category": "origin"},
    {"english": "ocean paradise", "thai": "สวรรค์มหาสมุทร", "category": "origin"},
    {"english": "subterranean", "thai": "ใต้พิภพ", "category": "origin"},
    {"english": "scion", "thai": "ทายาท", "category": "origin"},
    {"english": "terravore", "thai": "ผู้บริโภคโลก", "category": "origin"},
    {"english": "knights of the toxic god", "thai": "อัศวินแห่งเทพพิษ", "category": "origin"},
    {"english": "imperial fiefdom", "thai": "เมืองขึ้นจักรวรรดิ", "category": "origin"},

    # ── Species Types ──
    {"english": "humanoid", "thai": "มนุษย์", "category": "species"},
    {"english": "reptilian", "thai": "สัตว์เลื้อยคลาน", "category": "species"},
    {"english": "avian", "thai": "นก", "category": "species"},
    {"english": "arthropoid", "thai": "แมลง", "category": "species"},
    {"english": "molluscoid", "thai": "มอลลัสก์", "category": "species"},
    {"english": "fungoid", "thai": "เห็ดรา", "category": "species"},
    {"english": "plantoid", "thai": "พืช", "category": "species"},
    {"english": "lithoid", "thai": "หิน", "category": "species"},
    {"english": "necroid", "thai": "เนโคร", "category": "species"},
    {"english": "aquatic", "thai": "น้ำ", "category": "species"},
    {"english": "toxoid", "thai": "พิษ", "category": "species"},
    {"english": "machine species", "thai": "จักรกล", "category": "species"},

    # ── Leader Classes ──
    {"english": "commander", "thai": "ผู้บัญชาการ", "category": "leader"},
    {"english": "official", "thai": "ข้าราชการ", "category": "leader"},
    {"english": "delegate", "thai": "ผู้แทน", "category": "leader"},
    {"english": "envoys", "thai": "ทูต", "category": "leader"},
    {"english": "council", "thai": "สภา", "category": "leader"},
    {"english": "councillor", "thai": "สมาชิกสภา", "category": "leader"},
    {"english": "paragon", "thai": "ยอดมนุษย์", "category": "leader"},

    # ── UI / Meta ──
    {"english": "tooltip", "thai": "คำแนะนำ", "category": "ui"},
    {"english": "modifier", "thai": "ตัวปรับ", "category": "ui"},
    {"english": "description", "thai": "คำอธิบาย", "category": "ui"},
    {"english": "effect", "thai": "ผล", "category": "ui"},
    {"english": "trigger", "thai": "เงื่อนไข", "category": "ui"},
    {"english": "requirement", "thai": "ข้อกำหนด", "category": "ui"},
    {"english": "cost", "thai": "ค่าใช้จ่าย", "category": "ui"},
    {"english": "duration", "thai": "ระยะเวลา", "category": "ui"},
    {"english": "chance", "thai": "โอกาส", "category": "ui"},
    {"english": "cooldown", "thai": "เวลาคูลดาวน์", "category": "ui"},

    # ── Situations ──
    {"english": "situation", "thai": "สถานการณ์", "category": "situation"},
    {"english": "progress", "thai": "ความคืบหน้า", "category": "situation"},
    {"english": "stage", "thai": "ขั้น", "category": "situation"},
    {"english": "outcome", "thai": "ผลลัพธ์", "category": "situation"},
    {"english": "resolution", "thai": "มติ", "category": "situation"},

    # ── Events ──
    {"english": "event", "thai": "เหตุการณ์", "category": "event"},
    {"english": "chain", "thai": "ชุดเหตุการณ์", "category": "event"},
    {"english": "choice", "thai": "ตัวเลือก", "category": "event"},
    {"english": "consequence", "thai": "ผลที่ตามมา", "category": "event"},

    # ── Warfare ──
    {"english": "invasion", "thai": "การบุก", "category": "war"},
    {"english": "occupation", "thai": "การยึดครอง", "category": "war"},
    {"english": "bombardment", "thai": "การระดมยิง", "category": "war"},
    {"english": "colossus weapon", "thai": "อาวุธคอสซัส", "category": "war"},
    {"english": "crisis war", "thai": "สงครามวิกฤต", "category": "war"},
    {"english": "status quo", "thai": "สถานะเดิม", "category": "war"},
    {"english": "surrender", "thai": "ยอมแพ้", "category": "war"},

    # ── Misc Game Concepts ──
    {"english": "ascension", "thai": "การเลื่อนขั้น", "category": "gameplay"},
    {"english": "awakening", "thai": "การตื่น", "category": "gameplay"},
    {"english": "subspace", "thai": "ซับสเปซ", "category": "gameplay"},
    {"english": "psi", "thai": "พลังจิต", "category": "gameplay", "alt": "ไซ"},
    {"english": "gene", "thai": "ยีน", "category": "gameplay"},
    {"english": "clone", "thai": "โคลน", "category": "gameplay"},
    {"english": "cyborg", "thai": "ไซบอร์ก", "category": "gameplay"},
    {"english": "robot", "thai": "หุ่นยนต์", "category": "gameplay"},
    {"english": "droid", "thai": "ดรอยด์", "category": "gameplay"},
    {"english": "android", "thai": "แอนดรอยด์", "category": "gameplay"},
    {"english": "relic world", "thai": "โลกโบราณ", "category": "gameplay"},
]

def get_glossary():
    """Return the built-in glossary list."""
    return BUILTIN_GLOSSARY

def get_glossary_map():
    """Return {english_lower: thai} dictionary."""
    return {entry["english"].lower(): entry["thai"] for entry in BUILTIN_GLOSSARY}

def get_glossary_reverse():
    """Return {thai: english} dictionary."""
    return {entry["thai"]: entry["english"] for entry in BUILTIN_GLOSSARY}

def get_glossary_categories():
    """Return sorted list of unique categories."""
    cats = set()
    for entry in BUILTIN_GLOSSARY:
        if entry.get("category"):
            cats.add(entry["category"])
    return sorted(cats)

def update_stellaris_terms(english_words: set):
    """Add all glossary English words to a spell checker's word set."""
    for entry in BUILTIN_GLOSSARY:
        eng = entry["english"]
        alt = entry.get("alt", "")
        for text in [eng, alt]:
            if text:
                for w in text.split():
                    clean = w.strip(".,;:!?()[]{}").lower()
                    if clean and len(clean) > 1:
                        english_words.add(clean)
