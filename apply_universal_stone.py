#!/usr/bin/env python3
"""Añade la Piedra Universal al proyecto (alternativa robusta a universal_stone.patch).
Uso, desde la carpeta del proyecto:  python3 apply_universal_stone.py
Se puede ejecutar varias veces: si un archivo ya tiene el cambio, lo salta."""
import re, sys
from pathlib import Path

ROOT = Path(".")
MARK = "UniversalStone"
ok = True

def edit(rel, fn, already):
    global ok
    p = ROOT / rel
    if not p.exists():
        print(f"  ERROR: no existe {rel} (¿estás en la carpeta del proyecto?)"); ok = False; return
    t = p.read_text(encoding="utf-8")
    if already in t:
        print(f"  ya estaba: {rel}"); return
    new = fn(t)
    if new is None:
        print(f"  ERROR: no encuentro dónde meterlo en {rel}"); ok = False; return
    p.write_text(new, encoding="utf-8")
    print(f"  hecho: {rel}")

def before_last(t, needle, add):
    i = t.rfind(needle)
    return None if i < 0 else t[:i] + add + t[i:]

# 1) Constante del objeto (justo antes de ITEMS_COUNT)
edit("include/constants/items.h",
     lambda t: (lambda m: None if not m else t[:m.start()] + "    // Emerald Nuzlocke\n    ITEM_UNIVERSAL_STONE,\n\n" + t[m.start():])(
         re.search(r"^[ \t]*ITEMS_COUNT\s*,", t, re.M)),
     "ITEM_UNIVERSAL_STONE")

# 2) Datos del objeto (al final de gItemsInfo)
ITEM_BLOCK = '\n    // Emerald Nuzlocke: se convierte en la megapiedra del Pokémon elegido\n    [ITEM_UNIVERSAL_STONE] =\n    {\n        .name = ITEM_NAME("Universal Stone"),\n        .price = 0,\n        .importance = 1,\n        .description = COMPOUND_STRING(\n            "Becomes the Mega\\n"\n            "Stone of the Pokémon\\n"\n            "you choose. 1 use."),\n        .pocket = POCKET_KEY_ITEMS,\n        .type = ITEM_USE_PARTY_MENU,\n        .fieldUseFunc = ItemUseOutOfBattle_UniversalStone,\n        .iconPic = gItemIcon_ShinyStone,\n        .iconPalette = gItemIconPalette_ShinyStone,\n    },\n'
edit("src/data/items.h",
     lambda t: (lambda m: None if not m else t[:m.start()] + ITEM_BLOCK + t[m.start():])(
         re.search(r"^};\s*\n\s*#undef ITEM_NAME", t, re.M)),
     "ITEM_UNIVERSAL_STONE")

# 3) Declaraciones
edit("include/item_use.h", lambda t: before_last(t, "#endif", "void ItemUseOutOfBattle_UniversalStone(u8 taskId);\n\n"),
     "ItemUseOutOfBattle_UniversalStone")
edit("include/party_menu.h", lambda t: before_last(t, "#endif", "void ItemUseCB_UniversalStone(u8 taskId, TaskFunc task);\n\n"),
     "ItemUseCB_UniversalStone")

# 4) Uso desde la mochila
edit("src/item_use.c", lambda t: t.rstrip("\n") + """

// Emerald Nuzlocke
void ItemUseOutOfBattle_UniversalStone(u8 taskId)
{
    gItemUseCB = ItemUseCB_UniversalStone;
    SetUpItemUseCallback(taskId);
}
""", "ItemUseOutOfBattle_UniversalStone")

# 5) Lógica en el menú del equipo
PARTY_CODE = '// --------------------------------------------------------------------------\n// Emerald Nuzlocke: Piedra Universal\n// Elige un Pokémon del equipo y se convierte en su megapiedra (un solo uso).\n// Si no tiene mega, o ya tienes su piedra, avisa y la conservas.\n// --------------------------------------------------------------------------\n#undef tState\n#undef tMonId\n#undef tStone1\n#undef tStone2\n#undef tOldFunc\n#undef tCount\n#undef tAsking\n#define tState      data[0]\n#define tMonId      data[1]\n#define tStone1     data[2]\n#define tStone2     data[3]\n#define tOldFunc    4\n#define tCount      data[6]\n#define tAsking     data[7]\n\nstatic bool32 UniversalStone_PlayerHasItem(u16 item)\n{\n    u32 i, box, pos;\n\n    if (CheckBagHasItem(item, 1))\n        return TRUE;\n    for (i = 0; i < PARTY_SIZE; i++)\n    {\n        if (GetMonData(&gParties[B_TRAINER_PLAYER][i], MON_DATA_HELD_ITEM) == item)\n            return TRUE;\n    }\n    for (box = 0; box < TOTAL_BOXES_COUNT; box++)\n    {\n        for (pos = 0; pos < IN_BOX_COUNT; pos++)\n        {\n            if (GetBoxMonDataAt(box, pos, MON_DATA_HELD_ITEM) == item)\n                return TRUE;\n        }\n    }\n    return FALSE;\n}\n\nstatic void Task_UniversalStone(u8 taskId)\n{\n    static const u8 sText_NoReact[] = _("The {STR_VAR_2} doesn\'t\\nreact to {STR_VAR_1}…{PAUSE_UNTIL_PRESS}");\n    static const u8 sText_AlreadyHave[] = _("You already have the\\n{STR_VAR_2}!{PAUSE_UNTIL_PRESS}");\n    static const u8 sText_Ask[] = _("Turn it into the\\n{STR_VAR_2}?");\n    static const u8 sText_BagFull[] = _("There\'s no room in the BAG\\nfor the {STR_VAR_2}!{PAUSE_UNTIL_PRESS}");\n    static const u8 sText_Done[] = _("It became the\\n{STR_VAR_2}!{PAUSE_UNTIL_PRESS}");\n    s16 *data = gTasks[taskId].data;\n\n    switch (tState)\n    {\n    case 0:\n    {\n        u32 species = GetMonData(&gParties[B_TRAINER_PLAYER][tMonId], MON_DATA_SPECIES_OR_EGG);\n        const struct FormChange *fc = GetSpeciesFormChanges(species);\n        u16 owned = ITEM_NONE;\n        u32 i;\n\n        tCount = 0;\n        for (i = 0; fc != NULL && fc[i].method != FORM_CHANGE_TERMINATOR; i++)\n        {\n            if (fc[i].method != FORM_CHANGE_BATTLE_MEGA_EVOLUTION_ITEM)\n                continue;\n            if (UniversalStone_PlayerHasItem(fc[i].param1))\n                owned = fc[i].param1;\n            else if (tCount == 0)\n                tStone1 = fc[i].param1, tCount = 1;\n            else if (tCount == 1 && fc[i].param1 != tStone1)\n                tStone2 = fc[i].param1, tCount = 2;\n        }\n        PlaySE(SE_SELECT);\n        if (tCount == 0)\n        {\n            gPartyMenuUseExitCallback = FALSE;\n            if (owned != ITEM_NONE)\n            {\n                CopyItemName(owned, gStringVar2);\n                StringExpandPlaceholders(gStringVar4, sText_AlreadyHave);\n            }\n            else\n            {\n                GetMonNickname(&gParties[B_TRAINER_PLAYER][tMonId], gStringVar1);\n                CopyItemName(gSpecialVar_ItemId, gStringVar2);\n                StringExpandPlaceholders(gStringVar4, sText_NoReact);\n            }\n            DisplayPartyMenuMessage(gStringVar4, TRUE);\n            ScheduleBgCopyTilemapToVram(2);\n            gTasks[taskId].func = Task_ReturnToChooseMonAfterText;\n            return;\n        }\n        gPartyMenuUseExitCallback = TRUE;\n        tAsking = 0;\n        tState = 1;\n        break;\n    }\n    case 1:\n        CopyItemName(tAsking == 0 ? tStone1 : tStone2, gStringVar2);\n        StringExpandPlaceholders(gStringVar4, sText_Ask);\n        DisplayPartyMenuMessage(gStringVar4, TRUE);\n        ScheduleBgCopyTilemapToVram(2);\n        tState++;\n        break;\n    case 2:\n        if (!IsPartyMenuTextPrinterActive())\n        {\n            PartyMenuDisplayYesNoMenu();\n            tState++;\n        }\n        break;\n    case 3:\n        switch (Menu_ProcessInputNoWrapClearOnChoose())\n        {\n        case 0:\n            tState = 4;\n            break;\n        case 1:\n        case MENU_B_PRESSED:\n            PlaySE(SE_SELECT);\n            if (tAsking == 0 && tCount == 2)\n            {\n                // Megas X / Y: ofrece la otra\n                tAsking = 1;\n                tState = 1;\n                break;\n            }\n            gPartyMenuUseExitCallback = FALSE;\n            ScheduleBgCopyTilemapToVram(2);\n            ClearStdWindowAndFrameToTransparent(6, 0);\n            ClearWindowTilemap(6);\n            DisplayPartyMenuStdMessage(5);\n            gTasks[taskId].func = (void *)GetWordTaskArg(taskId, tOldFunc);\n            return;\n        }\n        break;\n    case 4:\n    {\n        u16 stone = (tAsking == 0) ? tStone1 : tStone2;\n\n        CopyItemName(stone, gStringVar2);\n        if (!CheckBagHasSpace(stone, 1))\n        {\n            gPartyMenuUseExitCallback = FALSE;\n            PlaySE(SE_SELECT);\n            StringExpandPlaceholders(gStringVar4, sText_BagFull);\n            DisplayPartyMenuMessage(gStringVar4, TRUE);\n            ScheduleBgCopyTilemapToVram(2);\n            gTasks[taskId].func = Task_ReturnToChooseMonAfterText;\n            return;\n        }\n        PlaySE(SE_USE_ITEM);\n        RemoveBagItem(gSpecialVar_ItemId, 1);\n        AddBagItem(stone, 1);\n        StringExpandPlaceholders(gStringVar4, sText_Done);\n        DisplayPartyMenuMessage(gStringVar4, TRUE);\n        ScheduleBgCopyTilemapToVram(2);\n        tState++;\n        break;\n    }\n    case 5:\n        if (!IsPartyMenuTextPrinterActive())\n            gTasks[taskId].func = Task_ClosePartyMenu;\n        break;\n    }\n}\n\nvoid ItemUseCB_UniversalStone(u8 taskId, TaskFunc task)\n{\n    s16 *data = gTasks[taskId].data;\n\n    tState = 0;\n    tMonId = gPartyMenu.slotId;\n    SetWordTaskArg(taskId, tOldFunc, (uintptr_t)(gTasks[taskId].func));\n    gTasks[taskId].func = Task_UniversalStone;\n}\n\n#undef tState\n#undef tMonId\n#undef tStone1\n#undef tStone2\n#undef tOldFunc\n#undef tCount\n#undef tAsking'
edit("src/party_menu.c", lambda t: t.rstrip("\n") + "\n\n" + PARTY_CODE + "\n", "Task_UniversalStone")

print("Piedra Universal añadida." if ok else "Ha habido errores: pásaselos a Claude.")
sys.exit(0 if ok else 1)
