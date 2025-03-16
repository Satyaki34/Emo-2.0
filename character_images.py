# character_images.py

# Dictionary mapping race_class combos to Discord CDN URLs
CHARACTER_IMAGES = {
    # Human
    "Human_Artificer": "https://media.discordapp.net/attachments/1350829867221913650/1350843809206108230/OE99ax2cA3wVm3HA-generated_image.png",  # Latest real link
    "Human_Barbarian": "https://media.discordapp.net/attachments/1350829867221913650/1350837326955282523/12IS2ERq7SnjUOKT-generated_image.png",  # Real link
    "Human_Bard": "https://media.discordapp.net/attachments/1350829867221913650/1350839888500625529/A9QI0dPcbm6SkyX5-generated_image.png",       # Real link
    "Human_Cleric": "https://media.discordapp.net/attachments/1350829867221913650/1350841133214728253/fniu7mpAeIKbO7rC-generated_image.png",     # Real link
    "Human_Druid": "https://media.discordapp.net/attachments/1350829867221913650/135090001/human_druid.png",
    "Human_Fighter": "https://media.discordapp.net/attachments/1350829867221913650/135090002/human_fighter.png",
    "Human_Monk": "https://media.discordapp.net/attachments/1195744344989249646/1350818129600839690/1efecb88-48a8-62d2-8d01-5727dce98c82.png",  # Real link
    "Human_Paladin": "https://media.discordapp.net/attachments/1350829867221913650/135090003/human_paladin.png",
    "Human_Ranger": "https://media.discordapp.net/attachments/1350829867221913650/135090004/human_ranger.png",
    "Human_Rogue": "https://media.discordapp.net/attachments/1350829867221913650/135090005/human_rogue.png",
    "Human_Sorcerer": "https://media.discordapp.net/attachments/1350829867221913650/135090006/human_sorcerer.png",
    "Human_Warlock": "https://media.discordapp.net/attachments/1350829867221913650/135090007/human_warlock.png",
    "Human_Wizard": "https://media.discordapp.net/attachments/1350829867221913650/135090008/human_wizard.png",

    # Elf
    "Elf_Artificer": "https://media.discordapp.net/attachments/1195744344989249646/135090009/elf_artificer.png",
    "Elf_Barbarian": "https://media.discordapp.net/attachments/1195744344989249646/135090010/elf_barbarian.png",
    "Elf_Bard": "https://media.discordapp.net/attachments/1195744344989249646/135090011/elf_bard.png",
    "Elf_Cleric": "https://media.discordapp.net/attachments/1195744344989249646/135090012/elf_cleric.png",
    "Elf_Druid": "https://media.discordapp.net/attachments/1195744344989249646/135090013/elf_druid.png",
    "Elf_Fighter": "https://media.discordapp.net/attachments/1195744344989249646/135090014/elf_fighter.png",
    "Elf_Monk": "https://media.discordapp.net/attachments/1195744344989249646/135090015/elf_monk.png",
    "Elf_Paladin": "https://media.discordapp.net/attachments/1195744344989249646/135090016/elf_paladin.png",
    "Elf_Ranger": "https://media.discordapp.net/attachments/1195744344989249646/135090017/elf_ranger.png",
    "Elf_Rogue": "https://media.discordapp.net/attachments/1195744344989249646/135090018/elf_rogue.png",
    "Elf_Sorcerer": "https://media.discordapp.net/attachments/1195744344989249646/135090019/elf_sorcerer.png",
    "Elf_Warlock": "https://media.discordapp.net/attachments/1195744344989249646/135090020/elf_warlock.png",
    "Elf_Wizard": "https://media.discordapp.net/attachments/1195744344989249646/135090021/elf_wizard.png",

    # Dwarf
    "Dwarf_Artificer": "https://media.discordapp.net/attachments/1350829867221913650/135090022/dwarf_artificer.png",
    "Dwarf_Barbarian": "https://media.discordapp.net/attachments/1350829867221913650/135090023/dwarf_barbarian.png",
    "Dwarf_Bard": "https://media.discordapp.net/attachments/1350829867221913650/135090024/dwarf_bard.png",
    "Dwarf_Cleric": "https://media.discordapp.net/attachments/1350829867221913650/135090025/dwarf_cleric.png",
    "Dwarf_Druid": "https://media.discordapp.net/attachments/1350829867221913650/135090026/dwarf_druid.png",
    "Dwarf_Fighter": "https://media.discordapp.net/attachments/1350829867221913650/135090027/dwarf_fighter.png",
    "Dwarf_Monk": "https://media.discordapp.net/attachments/1350829867221913650/135090028/dwarf_monk.png",
    "Dwarf_Paladin": "https://media.discordapp.net/attachments/1350829867221913650/135090029/dwarf_paladin.png",
    "Dwarf_Ranger": "https://media.discordapp.net/attachments/1350829867221913650/135090030/dwarf_ranger.png",
    "Dwarf_Rogue": "https://media.discordapp.net/attachments/1350829867221913650/135090031/dwarf_rogue.png",
    "Dwarf_Sorcerer": "https://media.discordapp.net/attachments/1350829867221913650/135090032/dwarf_sorcerer.png",
    "Dwarf_Warlock": "https://media.discordapp.net/attachments/1350829867221913650/135090033/dwarf_warlock.png",
    "Dwarf_Wizard": "https://media.discordapp.net/attachments/1350829867221913650/135090034/dwarf_wizard.png",

    # Halfling
    "Halfling_Artificer": "https://media.discordapp.net/attachments/1195744344989249646/135090035/halfling_artificer.png",
    "Halfling_Barbarian": "https://media.discordapp.net/attachments/1195744344989249646/135090036/halfling_barbarian.png",
    "Halfling_Bard": "https://media.discordapp.net/attachments/1195744344989249646/135090037/halfling_bard.png",
    "Halfling_Cleric": "https://media.discordapp.net/attachments/1195744344989249646/135090038/halfling_cleric.png",
    "Halfling_Druid": "https://media.discordapp.net/attachments/1195744344989249646/135090039/halfling_druid.png",
    "Halfling_Fighter": "https://media.discordapp.net/attachments/1195744344989249646/135090040/halfling_fighter.png",
    "Halfling_Monk": "https://media.discordapp.net/attachments/1195744344989249646/135090041/halfling_monk.png",
    "Halfling_Paladin": "https://media.discordapp.net/attachments/1195744344989249646/135090042/halfling_paladin.png",
    "Halfling_Ranger": "https://media.discordapp.net/attachments/1195744344989249646/135090043/halfling_ranger.png",
    "Halfling_Rogue": "https://media.discordapp.net/attachments/1195744344989249646/135090044/halfling_rogue.png",
    "Halfling_Sorcerer": "https://media.discordapp.net/attachments/1195744344989249646/135090045/halfling_sorcerer.png",
    "Halfling_Warlock": "https://media.discordapp.net/attachments/1195744344989249646/135090046/halfling_warlock.png",
    "Halfling_Wizard": "https://media.discordapp.net/attachments/1195744344989249646/135090047/halfling_wizard.png",

    # Gnome
    "Gnome_Artificer": "https://media.discordapp.net/attachments/1350829867221913650/135090048/gnome_artificer.png",
    "Gnome_Barbarian": "https://media.discordapp.net/attachments/1350829867221913650/135090049/gnome_barbarian.png",
    "Gnome_Bard": "https://media.discordapp.net/attachments/1350829867221913650/135090050/gnome_bard.png",
    "Gnome_Cleric": "https://media.discordapp.net/attachments/1350829867221913650/135090051/gnome_cleric.png",
    "Gnome_Druid": "https://media.discordapp.net/attachments/1350829867221913650/135090052/gnome_druid.png",
    "Gnome_Fighter": "https://media.discordapp.net/attachments/1350829867221913650/135090053/gnome_fighter.png",
    "Gnome_Monk": "https://media.discordapp.net/attachments/1350829867221913650/135090054/gnome_monk.png",
    "Gnome_Paladin": "https://media.discordapp.net/attachments/1350829867221913650/135090055/gnome_paladin.png",
    "Gnome_Ranger": "https://media.discordapp.net/attachments/1350829867221913650/135090056/gnome_ranger.png",
    "Gnome_Rogue": "https://media.discordapp.net/attachments/1350829867221913650/135090057/gnome_rogue.png",
    "Gnome_Sorcerer": "https://media.discordapp.net/attachments/1350829867221913650/135090058/gnome_sorcerer.png",
    "Gnome_Warlock": "https://media.discordapp.net/attachments/1350829867221913650/135090059/gnome_warlock.png",
    "Gnome_Wizard": "https://media.discordapp.net/attachments/1350829867221913650/135090060/gnome_wizard.png",

    # Dragonborn
    "Dragonborn_Artificer": "https://media.discordapp.net/attachments/1195744344989249646/135090061/dragonborn_artificer.png",
    "Dragonborn_Barbarian": "https://media.discordapp.net/attachments/1195744344989249646/135090062/dragonborn_barbarian.png",
    "Dragonborn_Bard": "https://media.discordapp.net/attachments/1195744344989249646/135090063/dragonborn_bard.png",
    "Dragonborn_Cleric": "https://media.discordapp.net/attachments/1195744344989249646/135090064/dragonborn_cleric.png",
    "Dragonborn_Druid": "https://media.discordapp.net/attachments/1195744344989249646/135090065/dragonborn_druid.png",
    "Dragonborn_Fighter": "https://media.discordapp.net/attachments/1195744344989249646/135090066/dragonborn_fighter.png",
    "Dragonborn_Monk": "https://media.discordapp.net/attachments/1195744344989249646/135090067/dragonborn_monk.png",
    "Dragonborn_Paladin": "https://media.discordapp.net/attachments/1195744344989249646/135090068/dragonborn_paladin.png",
    "Dragonborn_Ranger": "https://media.discordapp.net/attachments/1195744344989249646/135090069/dragonborn_ranger.png",
    "Dragonborn_Rogue": "https://media.discordapp.net/attachments/1195744344989249646/135090070/dragonborn_rogue.png",
    "Dragonborn_Sorcerer": "https://media.discordapp.net/attachments/1195744344989249646/135090071/dragonborn_sorcerer.png",
    "Dragonborn_Warlock": "https://media.discordapp.net/attachments/1195744344989249646/135090072/dragonborn_warlock.png",
    "Dragonborn_Wizard": "https://media.discordapp.net/attachments/1195744344989249646/135090073/dragonborn_wizard.png",

    # Tiefling
    "Tiefling_Artificer": "https://media.discordapp.net/attachments/1350829867221913650/135090074/tiefling_artificer.png",
    "Tiefling_Barbarian": "https://media.discordapp.net/attachments/1350829867221913650/135090075/tiefling_barbarian.png",
    "Tiefling_Bard": "https://media.discordapp.net/attachments/1350829867221913650/135090076/tiefling_bard.png",
    "Tiefling_Cleric": "https://media.discordapp.net/attachments/1350829867221913650/135090077/tiefling_cleric.png",
    "Tiefling_Druid": "https://media.discordapp.net/attachments/1350829867221913650/135090078/tiefling_druid.png",
    "Tiefling_Fighter": "https://media.discordapp.net/attachments/1350829867221913650/135090079/tiefling_fighter.png",
    "Tiefling_Monk": "https://media.discordapp.net/attachments/1350829867221913650/135090080/tiefling_monk.png",
    "Tiefling_Paladin": "https://media.discordapp.net/attachments/1350829867221913650/135090081/tiefling_paladin.png",
    "Tiefling_Ranger": "https://media.discordapp.net/attachments/1350829867221913650/135090082/tiefling_ranger.png",
    "Tiefling_Rogue": "https://media.discordapp.net/attachments/1350829867221913650/135090083/tiefling_rogue.png",
    "Tiefling_Sorcerer": "https://media.discordapp.net/attachments/1350829867221913650/135090084/tiefling_sorcerer.png",
    "Tiefling_Warlock": "https://media.discordapp.net/attachments/1350829867221913650/135090085/tiefling_warlock.png",
    "Tiefling_Wizard": "https://media.discordapp.net/attachments/1350829867221913650/135090086/tiefling_wizard.png",

    # Half-Elf
    "Half-Elf_Artificer": "https://media.discordapp.net/attachments/1195744344989249646/135090087/half-elf_artificer.png",
    "Half-Elf_Barbarian": "https://media.discordapp.net/attachments/1195744344989249646/135090088/half-elf_barbarian.png",
    "Half-Elf_Bard": "https://media.discordapp.net/attachments/1195744344989249646/135090089/half-elf_bard.png",
    "Half-Elf_Cleric": "https://media.discordapp.net/attachments/1195744344989249646/135090090/half-elf_cleric.png",
    "Half-Elf_Druid": "https://media.discordapp.net/attachments/1195744344989249646/135090091/half-elf_druid.png",
    "Half-Elf_Fighter": "https://media.discordapp.net/attachments/1195744344989249646/135090092/half-elf_fighter.png",
    "Half-Elf_Monk": "https://media.discordapp.net/attachments/1195744344989249646/135090093/half-elf_monk.png",
    "Half-Elf_Paladin": "https://media.discordapp.net/attachments/1195744344989249646/135090094/half-elf_paladin.png",
    "Half-Elf_Ranger": "https://media.discordapp.net/attachments/1195744344989249646/135090095/half-elf_ranger.png",
    "Half-Elf_Rogue": "https://media.discordapp.net/attachments/1195744344989249646/135090096/half-elf_rogue.png",
    "Half-Elf_Sorcerer": "https://media.discordapp.net/attachments/1195744344989249646/135090097/half-elf_sorcerer.png",
    "Half-Elf_Warlock": "https://media.discordapp.net/attachments/1195744344989249646/135090098/half-elf_warlock.png",
    "Half-Elf_Wizard": "https://media.discordapp.net/attachments/1195744344989249646/135090099/half-elf_wizard.png",

    # Half-Orc
    "Half-Orc_Artificer": "https://media.discordapp.net/attachments/1350829867221913650/135090100/half-orc_artificer.png",
    "Half-Orc_Barbarian": "https://media.discordapp.net/attachments/1350829867221913650/135090101/half-orc_barbarian.png",
    "Half-Orc_Bard": "https://media.discordapp.net/attachments/1350829867221913650/135090102/half-orc_bard.png",
    "Half-Orc_Cleric": "https://media.discordapp.net/attachments/1350829867221913650/135090103/half-orc_cleric.png",
    "Half-Orc_Druid": "https://media.discordapp.net/attachments/1350829867221913650/135090104/half-orc_druid.png",
    "Half-Orc_Fighter": "https://media.discordapp.net/attachments/1350829867221913650/135090105/half-orc_fighter.png",
    "Half-Orc_Monk": "https://media.discordapp.net/attachments/1350829867221913650/135090106/half-orc_monk.png",
    "Half-Orc_Paladin": "https://media.discordapp.net/attachments/1350829867221913650/135090107/half-orc_paladin.png",
    "Half-Orc_Ranger": "https://media.discordapp.net/attachments/1350829867221913650/135090108/half-orc_ranger.png",
    "Half-Orc_Rogue": "https://media.discordapp.net/attachments/1350829867221913650/135090109/half-orc_rogue.png",
    "Half-Orc_Sorcerer": "https://media.discordapp.net/attachments/1350829867221913650/135090110/half-orc_sorcerer.png",
    "Half-Orc_Warlock": "https://media.discordapp.net/attachments/1350829867221913650/135090111/half-orc_warlock.png",
    "Half-Orc_Wizard": "https://media.discordapp.net/attachments/1350829867221913650/135090112/half-orc_wizard.png",
}

# Default image for missing combos
DEFAULT_IMAGE = "https://media.discordapp.net/attachments/1350829867221913650/135090113/default_character.png"