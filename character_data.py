# character_data.py

RACES = {
    "Human": {
        "ability_scores": ["+1 to all ability scores"],
        "size": "Medium",
        "speed": "30 ft",
        "traits": ["Versatile"],
        "languages": ["Common", "Choice"]
    },
    "Elf (High Elf)": {
        "ability_scores": ["Dexterity +2", "Intelligence +1"],
        "size": "Medium",
        "speed": "30 ft",
        "traits": ["Darkvision", "Trance", "Elven Weapon Training", "Cantrip", "Extra Language"],
        "languages": ["Common", "Elvish", "Choice"]
    },
    "Dwarf (Mountain Dwarf)": {
        "ability_scores": ["Constitution +2", "Strength +2"],
        "size": "Medium",
        "speed": "25 ft",
        "traits": ["Darkvision", "Dwarven Resilience", "Dwarven Combat Training", "Tool Proficiency", "Stonecunning"],
        "languages": ["Common", "Dwarvish"]
    },
    "Halfling (Lightfoot)": {
        "ability_scores": ["Dexterity +2", "Charisma +1"],
        "size": "Small",
        "speed": "25 ft",
        "traits": ["Lucky", "Brave", "Halfling Nimbleness", "Naturally Stealthy"],
        "languages": ["Common", "Halfling"]
    },
    "Gnome (Rock)": {
        "ability_scores": ["Intelligence +2", "Constitution +1"],
        "size": "Small",
        "speed": "25 ft",
        "traits": ["Darkvision", "Gnome Cunning", "Artificer's Lore", "Tinker"],
        "languages": ["Common", "Gnomish"]
    },
    "Dragonborn": {
        "ability_scores": ["Strength +2", "Charisma +1"],
        "size": "Medium",
        "speed": "30 ft",
        "traits": ["Draconic Ancestry", "Breath Weapon", "Damage Resistance"],
        "languages": ["Common", "Draconic"]
    },
    "Tiefling": {
        "ability_scores": ["Charisma +2", "Intelligence +1"],
        "size": "Medium",
        "speed": "30 ft",
        "traits": ["Darkvision", "Hellish Resistance", "Infernal Legacy"],
        "languages": ["Common", "Infernal"]
    },
    "Half-Elf": {
        "ability_scores": ["Charisma +2", "Two others +1 each (choice)"],
        "size": "Medium",
        "speed": "30 ft",
        "traits": ["Darkvision", "Fey Ancestry", "Skill Versatility"],
        "languages": ["Common", "Elvish", "Choice"]
    },
    "Half-Orc": {
        "ability_scores": ["Strength +2", "Constitution +1"],
        "size": "Medium",
        "speed": "30 ft",
        "traits": ["Darkvision", "Menacing", "Relentless Endurance", "Savage Attacks"],
        "languages": ["Common", "Orc"]
    }
}

CLASSES = {
    "Artificer": {
        "hit_dice": "d8",
        "proficiencies": ["Light armor", "Medium armor", "Shields", "Simple weapons", "Artisan's tools (one type)"],
        "saving_throws": ["Constitution", "Intelligence"],
        "skills": {"choose": 2, "options": ["Arcana", "History", "Investigation", "Medicine", "Nature", "Perception", "Sleight of Hand"]},
        "equipment": ["Scale mail OR leather armor", "Light crossbow and 20 bolts OR simple weapon", "Explorer's pack", "Artisan's tools"],
        "class_features": ["Magical Tinkering", "Infuse Item"]
    },
    "Barbarian": {
        "hit_dice": "d12",
        "proficiencies": ["Light armor", "Medium armor", "Shields", "Simple weapons", "Martial weapons"],
        "saving_throws": ["Strength", "Constitution"],
        "skills": {"choose": 2, "options": ["Animal Handling", "Athletics", "Intimidation", "Nature", "Perception", "Survival"]},
        "equipment": ["Greataxe OR martial weapon", "Two javelins", "Explorer's pack"],
        "class_features": ["Rage", "Unarmored Defense"]
    },
    "Bard": {
        "hit_dice": "d8",
        "proficiencies": ["Light armor", "Simple weapons", "Hand crossbows", "Longswords", "Rapiers", "Shortswords"],
        "saving_throws": ["Dexterity", "Charisma"],
        "skills": {"choose": 3, "options": ["Acrobatics", "Animal Handling", "Arcana", "Athletics", "Deception", "History", "Insight", "Intimidation", "Investigation", "Medicine", "Nature", "Perception", "Performance", "Persuasion", "Religion", "Sleight of Hand", "Stealth", "Survival"]},
        "equipment": ["Musical instrument", "Dagger", "Leather armor", "Starting clothes"],
        "class_features": ["Bardic Inspiration", "Spellcasting"],
        "spells": {
            "choose_cantrips": 2,
            "cantrips": ["Mage Hand", "Prestidigitation", "Minor Illusion", "Vicious Mockery"],
            "choose_spells": 4,
            "spells": ["Charm Person", "Cure Wounds", "Detect Magic", "Healing Word", "Thunderwave", "Disguise Self"]
        }
    },
    "Cleric": {
        "hit_dice": "d8",
        "proficiencies": ["Light armor", "Medium armor", "Shields", "Simple weapons"],
        "saving_throws": ["Wisdom", "Charisma"],
        "skills": {"choose": 2, "options": ["History", "Insight", "Medicine", "Persuasion", "Religion"]},
        "equipment": ["Mace OR warhammer", "Scale mail", "Light crossbow and 20 bolts OR simple weapon", "Explorer's pack", "Holy symbol"],
        "class_features": ["Divine Domain", "Spellcasting"],
        "spells": {
            "choose_cantrips": 3,
            "cantrips": ["Guidance", "Light", "Sacred Flame", "Thaumaturgy"],
            "choose_spells": 3,
            "spells": ["Bless", "Cure Wounds", "Detect Magic", "Guiding Bolt", "Healing Word", "Shield of Faith"]
        }
    },
    "Druid": {
        "hit_dice": "d8",
        "proficiencies": ["Light armor", "Medium armor", "Shields (no metal)", "Clubs", "Daggers", "Darts", "Javelins", "Maces", "Quarterstaffs", "Scimitars", "Sickles", "Slings", "Spears"],
        "saving_throws": ["Intelligence", "Wisdom"],
        "skills": {"choose": 2, "options": ["Arcana", "Animal Handling", "Insight", "Medicine", "Nature", "Perception", "Survival"]},
        "equipment": ["Wooden shield OR simple weapon", "Scimitar OR simple weapon", "Leather armor", "Explorer's pack", "Druidic focus"],
        "class_features": ["Druidic", "Spellcasting"],
        "spells": {
            "choose_cantrips": 2,
            "cantrips": ["Druidcraft", "Produce Flame", "Shillelagh", "Thorn Whip"],
            "choose_spells": 3,
            "spells": ["Entangle", "Faerie Fire", "Goodberry", "Healing Word", "Thunderwave", "Fog Cloud"]
        }
    },
    "Fighter": {
        "hit_dice": "d10",
        "proficiencies": ["All armor", "Shields", "Simple weapons", "Martial weapons"],
        "saving_throws": ["Strength", "Constitution"],
        "skills": {"choose": 2, "options": ["Acrobatics", "Animal Handling", "Athletics", "History", "Insight", "Intimidation", "Perception", "Survival"]},
        "equipment": ["Chain mail OR leather armor", "Longbow and 20 arrows OR martial weapon", "Shield OR simple weapon", "Two javelins OR simple weapon", "Explorer's pack OR dungeoneer's pack"],
        "class_features": ["Fighting Style", "Second Wind"]
    },
    "Monk": {
        "hit_dice": "d8",
        "proficiencies": ["Simple weapons", "Shortswords"],
        "saving_throws": ["Strength", "Dexterity"],
        "skills": {"choose": 2, "options": ["Acrobatics", "Athletics", "History", "Insight", "Religion", "Stealth"]},
        "equipment": ["Shortsword OR simple weapon", "Dungeoneer's pack", "10 darts OR ammunition for sling/shortbow"],
        "class_features": ["Unarmored Defense", "Martial Arts"]
    },
    "Paladin": {
        "hit_dice": "d10",
        "proficiencies": ["All armor", "Shields", "Simple weapons", "Martial weapons"],
        "saving_throws": ["Wisdom", "Charisma"],
        "skills": {"choose": 2, "options": ["Athletics", "Insight", "Intimidation", "Medicine", "Persuasion", "Religion"]},
        "equipment": ["Chain mail OR leather armor", "Longsword OR martial weapon", "Shield OR simple weapon", "Holy symbol"],
        "class_features": ["Divine Sense", "Lay on Hands"]
    },
    "Ranger": {
        "hit_dice": "d10",
        "proficiencies": ["Light armor", "Medium armor", "Shields", "Simple weapons", "Martial weapons"],
        "saving_throws": ["Strength", "Dexterity"],
        "skills": {"choose": 3, "options": ["Animal Handling", "Athletics", "Insight", "Investigation", "Nature", "Perception", "Stealth", "Survival"]},
        "equipment": ["Scale mail OR leather armor", "Longbow and 20 arrows OR two simple weapons", "Shortsword OR simple weapon", "Explorer's pack", "Hunting trap"],
        "class_features": ["Favored Enemy", "Natural Explorer"]
    },
    "Rogue": {
        "hit_dice": "d8",
        "proficiencies": ["Light armor", "Simple weapons", "Hand crossbows", "Longswords", "Rapiers", "Shortswords", "Thieves' tools"],
        "saving_throws": ["Dexterity", "Intelligence"],
        "skills": {"choose": 4, "options": ["Acrobatics", "Athletics", "Deception", "Insight", "Intimidation", "Investigation", "Perception", "Performance", "Persuasion", "Sleight of Hand", "Stealth"]},
        "equipment": ["Shortsword OR simple weapon", "Shortbow and 20 arrows OR hand crossbow and 20 bolts", "Burglar's pack OR dungeoneer's pack OR explorer's pack", "Leather armor", "Thieves' tools"],
        "class_features": ["Expertise", "Sneak Attack", "Thieves' Cant"]
    },
    "Sorcerer": {
        "hit_dice": "d6",
        "proficiencies": ["Daggers", "Darts", "Slings", "Quarterstaffs", "Light crossbows"],
        "saving_throws": ["Constitution", "Charisma"],
        "skills": {"choose": 2, "options": ["Arcana", "Deception", "Insight", "Intimidation", "Persuasion", "Religion"]},
        "equipment": ["Light crossbow and 20 bolts OR simple weapon", "Component pouch OR arcane focus", "Dungeoneer's pack OR explorer's pack", "Two daggers"],
        "class_features": ["Spellcasting", "Sorcerous Origin"],
        "spells": {
            "choose_cantrips": 4,
            "cantrips": ["Fire Bolt", "Prestidigitation", "Ray of Frost", "Shocking Grasp", "Acid Splash"],
            "choose_spells": 2,
            "spells": ["Burning Hands", "Charm Person", "Magic Missile", "Shield", "Sleep"]
        }
    },
    "Warlock": {
        "hit_dice": "d8",
        "proficiencies": ["Light armor", "Simple weapons"],
        "saving_throws": ["Wisdom", "Charisma"],
        "skills": {"choose": 3, "options": ["Arcana", "Deception", "History", "Intimidation", "Investigation", "Nature", "Religion"]},
        "equipment": ["Light crossbow and 20 bolts OR simple weapon", "Component pouch OR arcane focus", "Scholar's pack OR dungeoneer's pack", "Leather armor", "Simple weapon", "Two daggers"],
        "class_features": ["Otherworldly Patron", "Pact Magic"],
        "spells": {
            "choose_cantrips": 2,
            "cantrips": ["Eldritch Blast", "Chill Touch", "Mage Hand", "Poison Spray"],
            "choose_spells": 2,
            "spells": ["Armor of Agathys", "Hex", "Charm Person", "Hellish Rebuke", "Witch Bolt"]
        }
    },
    "Wizard": {
        "hit_dice": "d6",
        "proficiencies": ["Daggers", "Darts", "Slings", "Quarterstaffs", "Light crossbows"],
        "saving_throws": ["Intelligence", "Wisdom"],
        "skills": {"choose": 3, "options": ["Arcana", "History", "Insight", "Investigation", "Medicine", "Religion"]},
        "equipment": ["Quarterstaff OR dagger", "Component pouch OR arcane focus", "Scholar's pack OR explorer's pack", "Spellbook"],
        "class_features": ["Spellcasting", "Arcane Recovery"],
        "spells": {
            "choose_cantrips": 3,
            "cantrips": ["Fire Bolt", "Light", "Mage Hand", "Prestidigitation", "Ray of Frost"],
            "choose_spells": 6,
            "spells": ["Burning Hands", "Charm Person", "Detect Magic", "Magic Missile", "Shield", "Sleep", "Find Familiar", "Identify"]
        }
    }
}