SootopolisCity_Mart_MapScripts::
	.byte 0

SootopolisCity_Mart_EventScript_Clerk::
	lock
	faceplayer
	message gText_HowMayIServeYou
	waitmessage
	pokemart SootopolisCity_Mart_Pokemart
	goto_if_unset FLAG_IS_CHAMPION, SootopolisCity_Mart_EventScript_NuzNoMegaShop
	msgbox SootopolisCity_Mart_Text_NuzMegaShop, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, SootopolisCity_Mart_EventScript_NuzNoMegaShop
	message gText_HowMayIServeYou
	waitmessage
	pokemart SootopolisCity_Mart_NuzMegaStones
SootopolisCity_Mart_EventScript_NuzNoMegaShop::
	msgbox gText_PleaseComeAgain, MSGBOX_DEFAULT
	release
	end

	.align 2
SootopolisCity_Mart_Pokemart:
	.2byte ITEM_ULTRA_BALL
	.2byte ITEM_HYPER_POTION
	.2byte ITEM_MAX_POTION
	.2byte ITEM_FULL_HEAL
	.2byte ITEM_MAX_REPEL
	.2byte ITEM_X_ATTACK
	.2byte ITEM_X_DEFENSE
	.2byte ITEM_SHADOW_MAIL
	pokemartlistend

SootopolisCity_Mart_EventScript_FatMan::
	lock
	faceplayer
	goto_if_ge VAR_SKY_PILLAR_STATE, 2, SootopolisCity_Mart_EventScript_FatManNoLegendaries
	goto_if_unset FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN, SootopolisCity_Mart_EventScript_FatManNoLegendaries
	msgbox SootopolisCity_Mart_Text_TooScaryOutside, MSGBOX_DEFAULT
	release
	end

SootopolisCity_Mart_EventScript_FatManNoLegendaries::
	msgbox SootopolisCity_Mart_Text_PPUpIsGreat, MSGBOX_DEFAULT
	release
	end

SootopolisCity_Mart_EventScript_Gentleman::
	lock
	faceplayer
	goto_if_ge VAR_SKY_PILLAR_STATE, 2, SootopolisCity_Mart_EventScript_GentlemanNoLegendaries
	goto_if_unset FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN, SootopolisCity_Mart_EventScript_GentlemanNoLegendaries
	msgbox SootopolisCity_Mart_Text_DidSomethingAwaken, MSGBOX_DEFAULT
	release
	end

SootopolisCity_Mart_EventScript_GentlemanNoLegendaries::
	msgbox SootopolisCity_Mart_Text_FullRestoreItemOfDreams, MSGBOX_DEFAULT
	release
	end

SootopolisCity_Mart_Text_PPUpIsGreat:
	.string "PP UP is great!\p"
	.string "It raises the POWER POINTS, the PP,\n"
	.string "of a POKéMON move.$"

SootopolisCity_Mart_Text_TooScaryOutside:
	.string "What…\n"
	.string "What is happening?\p"
	.string "I really want to know, but it's too\n"
	.string "scary to go outside.$"

SootopolisCity_Mart_Text_FullRestoreItemOfDreams:
	.string "Do you know FULL RESTORE?\p"
	.string "Full restoration of HP!\n"
	.string "Eradication of all status problems!\p"
	.string "It's truly an item of your dreams!$"

SootopolisCity_Mart_Text_DidSomethingAwaken:
	.string "This weather…\n"
	.string "Did something awaken?$"

SootopolisCity_Mart_Text_NuzMegaShop:
	.string "Oh! You're the new CHAMPION!\p"
	.string "A collector left us some very rare\n"
	.string "MEGA STONES. They aren't cheap…\p"
	.string "Would you like to see them?$"

	.align 2
SootopolisCity_Mart_NuzMegaStones:
	.2byte ITEM_ABOMASITE
	.2byte ITEM_ABSOLITE
	.2byte ITEM_ABSOLITE_Z
	.2byte ITEM_ALAKAZITE
	.2byte ITEM_AMPHAROSITE
	.2byte ITEM_AUDINITE
	.2byte ITEM_BANETTITE
	.2byte ITEM_BARBARACITE
	.2byte ITEM_BAXCALIBRITE
	.2byte ITEM_BLASTOISINITE
	.2byte ITEM_BLAZIKENITE
	.2byte ITEM_CAMERUPTITE
	.2byte ITEM_CHARIZARDITE_X
	.2byte ITEM_CHARIZARDITE_Y
	.2byte ITEM_CHIMECHITE
	.2byte ITEM_CLEFABLITE
	.2byte ITEM_DARKRANITE
	.2byte ITEM_DIANCITE
	.2byte ITEM_EELEKTROSSITE
	.2byte ITEM_EMBOARITE
	.2byte ITEM_EXCADRITE
	.2byte ITEM_FALINKSITE
	.2byte ITEM_FERALIGITE
	.2byte ITEM_FLOETTITE
	.2byte ITEM_FROSLASSITE
	.2byte ITEM_GALLADITE
	.2byte ITEM_GARCHOMPITE
	.2byte ITEM_GARCHOMPITE_Z
	.2byte ITEM_GOLURKITE
	.2byte ITEM_GRENINJITE
	.2byte ITEM_GYARADOSITE
	.2byte ITEM_HAWLUCHANITE
	.2byte ITEM_HEATRANITE
	.2byte ITEM_HERACRONITE
	.2byte ITEM_HOUNDOOMINITE
	.2byte ITEM_LATIASITE
	.2byte ITEM_LATIOSITE
	.2byte ITEM_LOPUNNITE
	.2byte ITEM_LUCARIONITE
	.2byte ITEM_LUCARIONITE_Z
	.2byte ITEM_MAGEARNITE
	.2byte ITEM_MALAMARITE
	.2byte ITEM_MAWILITE
	.2byte ITEM_MEGANIUMITE
	.2byte ITEM_MEOWSTICITE
	.2byte ITEM_MEWTWONITE_X
	.2byte ITEM_MEWTWONITE_Y
	.2byte ITEM_PIDGEOTITE
	.2byte ITEM_PYROARITE
	.2byte ITEM_RAICHUNITE_X
	.2byte ITEM_RAICHUNITE_Y
	.2byte ITEM_SABLENITE
	.2byte ITEM_SALAMENCITE
	.2byte ITEM_SCEPTILITE
	.2byte ITEM_SCIZORITE
	.2byte ITEM_SCOLIPITE
	.2byte ITEM_SCOVILLAINITE
	.2byte ITEM_SCRAFTINITE
	.2byte ITEM_SHARPEDONITE
	.2byte ITEM_SKARMORITE
	.2byte ITEM_SLOWBRONITE
	.2byte ITEM_STEELIXITE
	.2byte ITEM_TYRANITARITE
	.2byte ITEM_VENUSAURITE
	.2byte ITEM_VICTREEBELITE
	.2byte ITEM_ZERAORITE
	.2byte ITEM_ZYGARDITE
	pokemartlistend
