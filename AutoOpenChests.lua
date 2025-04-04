---@diagnostic disable: lowercase-global, undefined-global, need-check-nil, param-type-mismatch
require 'lib.moonloader'
local se = require 'lib.samp.events'
local imgui = require 'imgui'
local inicfg = require 'inicfg'
local encoding = require 'encoding'
encoding.default = 'CP1251'
u8 = encoding.UTF8

local cfg = inicfg.load({
	chests = {
		starter = false,
		donate = false,
		platinum = false,
		elon_musk1 = false,
		elon_musk2 = false,
		los_santos = false,
		vice_city = false,
		vice_city2 = false,
		vice_city3 = false,
		sobiratel1 = false,
		sobiratel2 = false,
		sobiratel3 = false,
		sobiratel4 = false,
		sobiratel5 = false,
		sobiratel6 = false,
		sobiratel7 = false,
		sobiratel8 = false,
		sobiratel9 = false,
		sobiratel10 = false,
		sobiratel11 = false,
		sobiratel12 = false,
		sobiratel13 = false,
		sobiratel14 = false,
		sobiratel15 = false,
		sobiratel16 = false,
		sobiratel17 = false,
		sobiratel18 = false,
		sobiratel19 = false,
		sobiratel20 = false,
		sobiratel21 = false,
		sobiratel22 = false,
		sobiratel23 = false,
		sobiratel24 = false,
		sobiratel25 = false,
		sobiratel26 = false,
		sobiratel27 = false,
		sobiratel28 = false,
		sobiratel29 = false,
		sobiratel30 = false
	},
	settings = {
		delay_time = 60,
		random_delay = false,
		add_vip = false,
		open_inventory = false,
		connected = false,
	},
	prices = {
		platinum_roulette = 0,
		gold_roulette = 0,
		silver_roulette = 0,
		bronze_roulette = 0, --рулетки
		premium_box = 0,
		super_car_box = 0,
		concept_car_luxury_box = 0,
		products_carrier_box = 0,
		fisher_box = 0,
		treasure_hunter_box = 0,
		crafter_box = 0,
		custom_accessories_box = 0,
		mortal_combat_box = 0,
		fortnite_box = 0,
		random_box = 0,
		oligarch_box = 0,
		organization_box = 0,
		nostalgic_box = 0,
		rare_yellow_box = 0,
		rare_red_box = 0,
		rare_blue_box = 0,
		super_auto_box = 0,
		super_moto_box = 0,
		marvel_box = 0,
		gentleman_box = 0,
		minecraft_box = 0,
		second_hand_box = 0,
	}
}, 'auto_opening_chests')

if not doesFileExist('auto_opening_chests.ini') then
    inicfg.save(cfg, 'auto_opening_chests.ini')
end

function json(filePath)
	local filePath = getWorkingDirectory()..'\\config\\'..(filePath:find('(.+).json') and filePath or filePath..'.json')
	local class = {}
	if not doesDirectoryExist(getWorkingDirectory()..'\\config') then
		createDirectory(getWorkingDirectory()..'\\config')
	end
	function class:Save(tbl)
		if tbl then
			local F = io.open(filePath, 'w')
			F:write(encodeJson(tbl) or {})
			F:close()
			return true, 'ok'
		end
		return false, 'table = nil'
	end
	function class:Load(defaultTable)
		if not doesFileExist(filePath) then
			class:Save(defaultTable or {})
		end
		local F = io.open(filePath, 'r+')
		local TABLE = decodeJson(F:read() or {})
		F:close()
		for def_k, def_v in next, defaultTable do
			if TABLE[def_k] == nil then
				TABLE[def_k] = def_v
			end
		end
		return TABLE
	end
	return class
end

local sw, sh = getScreenResolution()
local main_window = imgui.ImBool(false)
local stats_window = imgui.ImBool(false)
local imgui_page = 1
local work = false
local inventory_fix = false
local inventory_id = nil
local first_start = true
local block_donate = false
local block_platinum = false
local block_elon_musk1 = false
local block_elon_musk2 = false
local temp_date = os.date('%d.%m.%Y')
local last_date = os.date('%d.%m.%Y')
local log = json('chests_opening_stats.json'):Load({})
local profit = 0
local delay = imgui.ImBool(true)
local delay_time = imgui.ImBuffer(tostring(cfg.settings.delay_time), 4)
local random_delay = imgui.ImBool(cfg.settings.random_delay)
local add_vip = imgui.ImBool(cfg.settings.add_vip)
local open_inventory = imgui.ImBool(cfg.settings.open_inventory)
local timer = imgui.ImBool(false)
local timer_time = imgui.ImBuffer(tostring(''), 4)

local chest = {
	[1] = {'Сундук рулетки', 'starter', imgui.ImBool(cfg.chests.starter), _, _, false},
	[2] = {'Сундук рулетки (донат)', 'donate', imgui.ImBool(cfg.chests.donate), _, _, false},
	[3] = {'Сундук платиновой рулетки', 'platinum', imgui.ImBool(cfg.chests.platinum), _, _, false},
	[4] = {'Тайник Илона Маска 1', 'elon_musk1', imgui.ImBool(cfg.chests.elon_musk1), _, _, false},
	[5] = {'Тайник Илона Маска 2', 'elon_musk2', imgui.ImBool(cfg.chests.elon_musk2), _, _, false},
	[6] = {'Тайник Лос Сантоса', 'los_santos', imgui.ImBool(cfg.chests.los_santos), _, _, false},
	[7] = {'Тайник Vice City 1', 'vice_city', imgui.ImBool(cfg.chests.vice_city), _, _, false},
	[8] = {'Тайник Vice City 2', 'vice_city2', imgui.ImBool(cfg.chests.vice_city2), _, _, false},
	[9] = {'Тайник Vice City 3', 'vice_city3', imgui.ImBool(cfg.chests.vice_city3), _, _, false},
	[10] = {'Тайник Собирателя 1', 'sobiratel1', imgui.ImBool(cfg.chests.sobiratel1), _, _, false},
	[11] = {'Тайник Собирателя 2', 'sobiratel2', imgui.ImBool(cfg.chests.sobiratel2), _, _, false},
	[12] = {'Тайник Собирателя 3', 'sobiratel3', imgui.ImBool(cfg.chests.sobiratel3), _, _, false},
	[13] = {'Тайник Собирателя 4', 'sobiratel4', imgui.ImBool(cfg.chests.sobiratel4), _, _, false},
	[14] = {'Тайник Собирателя 5', 'sobiratel5', imgui.ImBool(cfg.chests.sobiratel5), _, _, false},
	[15] = {'Тайник Собирателя 6', 'sobiratel6', imgui.ImBool(cfg.chests.sobiratel6), _, _, false},
	[16] = {'Тайник Собирателя 7', 'sobiratel7', imgui.ImBool(cfg.chests.sobiratel7), _, _, false},
	[17] = {'Тайник Собирателя 8', 'sobiratel8', imgui.ImBool(cfg.chests.sobiratel8), _, _, false},
	[18] = {'Тайник Собирателя 9', 'sobiratel9', imgui.ImBool(cfg.chests.sobiratel9), _, _, false},
	[19] = {'Тайник Собирателя 10', 'sobiratel10', imgui.ImBool(cfg.chests.sobiratel10), _, _, false},
	[20] = {'Тайник Собирателя 11', 'sobiratel11', imgui.ImBool(cfg.chests.sobiratel11), _, _, false},
	[21] = {'Тайник Собирателя 12', 'sobiratel12', imgui.ImBool(cfg.chests.sobiratel12), _, _, false},
	[22] = {'Тайник Собирателя 13', 'sobiratel13', imgui.ImBool(cfg.chests.sobiratel13), _, _, false},
	[23] = {'Тайник Собирателя 14', 'sobiratel14', imgui.ImBool(cfg.chests.sobiratel14), _, _, false},
	[24] = {'Тайник Собирателя 15', 'sobiratel15', imgui.ImBool(cfg.chests.sobiratel15), _, _, false},
	[25] = {'Тайник Собирателя 16', 'sobiratel16', imgui.ImBool(cfg.chests.sobiratel16), _, _, false},
	[26] = {'Тайник Собирателя 17', 'sobiratel17', imgui.ImBool(cfg.chests.sobiratel17), _, _, false},
	[27] = {'Тайник Собирателя 18', 'sobiratel18', imgui.ImBool(cfg.chests.sobiratel18), _, _, false},
	[28] = {'Тайник Собирателя 19', 'sobiratel19', imgui.ImBool(cfg.chests.sobiratel19), _, _, false},
	[29] = {'Тайник Собирателя 20', 'sobiratel20', imgui.ImBool(cfg.chests.sobiratel20), _, _, false},
	[30] = {'Тайник Собирателя 21', 'sobiratel21', imgui.ImBool(cfg.chests.sobiratel21), _, _, false},
	[31] = {'Тайник Собирателя 22', 'sobiratel22', imgui.ImBool(cfg.chests.sobiratel22), _, _, false},
	[32] = {'Тайник Собирателя 23', 'sobiratel23', imgui.ImBool(cfg.chests.sobiratel23), _, _, false},
	[33] = {'Тайник Собирателя 24', 'sobiratel24', imgui.ImBool(cfg.chests.sobiratel24), _, _, false},
	[34] = {'Тайник Собирателя 25', 'sobiratel25', imgui.ImBool(cfg.chests.sobiratel25), _, _, false},
	[35] = {'Тайник Собирателя 26', 'sobiratel26', imgui.ImBool(cfg.chests.sobiratel26), _, _, false},
	[36] = {'Тайник Собирателя 27', 'sobiratel27', imgui.ImBool(cfg.chests.sobiratel27), _, _, false},
	[37] = {'Тайник Собирателя 28', 'sobiratel28', imgui.ImBool(cfg.chests.sobiratel28), _, _, false},
	[38] = {'Тайник Собирателя 29', 'sobiratel29', imgui.ImBool(cfg.chests.sobiratel29), _, _, false},
	[39] = {'Тайник Собирателя 30', 'sobiratel30', imgui.ImBool(cfg.chests.sobiratel30), _, _, false}
}

local item = {
	[1] = {'Платиновая рулетка', 'платиновую рулетку', 'platinum_roulette', imgui.ImInt(cfg.prices.platinum_roulette), _, _},
	[2] = {'Золотая рулетка', 'золотую рулетку', 'gold_roulette', imgui.ImInt(cfg.prices.gold_roulette), _, _},
	[3] = {'Серебряная рулетка', 'серебряную рулетку', 'silver_roulette', imgui.ImInt(cfg.prices.silver_roulette), _, _},
	[4] = {'Бронзовая рулетка', 'бронзовую рулетку', 'bronze_roulette', imgui.ImInt(cfg.prices.bronze_roulette), _, _},
	[5] = {'Ларец с премией', 'Ларец с премией', 'premium_box', imgui.ImInt(cfg.prices.premium_box), _, _},
	[6] = {'Super Car Box', 'Super Car Box', 'super_car_box', imgui.ImInt(cfg.prices.super_car_box), _, _},
	[7] = {'Concept Car Luxury', 'Concept Car Luxury', 'concept_car_luxury_box', imgui.ImInt(cfg.prices.concept_car_luxury_box), _, _},
	[8] = {'Ларец развозчика продуктов', 'Ларец развозчика продуктов', 'products_carrier_box', imgui.ImInt(cfg.prices.products_carrier_box), _, _},
	[9] = {'Ларец рыболова', 'Ларец рыболова', 'fisher_box', imgui.ImInt(cfg.prices.fisher_box), _, _},
	[10] = {'Ларец кладоискателя', 'Ларец кладоискателя', 'treasure_hunter_box', imgui.ImInt(cfg.prices.treasure_hunter_box), _, _},
	[11] = {'Ларец крафтера', 'Ларец крафтера', 'crafter_box', imgui.ImInt(cfg.prices.crafter_box), _, _},
	[12] = {'Ларец кастомных аксессуаров', 'Ларец кастомных аксессуаров', 'custom_accessories_box', imgui.ImInt(cfg.prices.custom_accessories_box), _, _},
	[13] = {'Ларец Mortal Combat', 'Ларец Mortal Combat', 'mortal_combat_box', imgui.ImInt(cfg.prices.mortal_combat_box), _, _},
	[14] = {'Рандомный ларец', 'Рандомный Ларец', 'random_box', imgui.ImInt(cfg.prices.random_box), _, _},
	[15] = {'Ларец олигарха', 'Ларец Олигарха', 'oligarch_box', imgui.ImInt(cfg.prices.oligarch_box), _, _},
	[16] = {'Ларец организации', 'Ларец организации', 'organization_box', imgui.ImInt(cfg.prices.organization_box), _, _},
	[17] = {'Ларец Fortnite', 'Ларец Fortnite', 'fortnite_box', imgui.ImInt(cfg.prices.fortnite_box), _, _},
	[18] = {'Ностальгический ящик', 'Ностальгический ящик', 'nostalgic_box', imgui.ImInt(cfg.prices.nostalgic_box), _, _},
	[19] = {'Rare Box Yellow', 'Rare Box Yellow', 'rare_yellow_box', imgui.ImInt(cfg.prices.rare_yellow_box), _, _},
	[20] = {'Rare Box Red', 'Rare Box Red', 'rare_red_box', imgui.ImInt(cfg.prices.rare_red_box), _, _},
	[21] = {'Rare Box Blue', 'Rare Box Blue', 'rare_blue_box', imgui.ImInt(cfg.prices.rare_blue_box), _, _},
	[22] = {'Супер авто-ящик', 'Супер авто-ящик', 'super_auto_box', imgui.ImInt(cfg.prices.super_auto_box), _, _},
	[23] = {'Супер мото-ящик', 'Супер мото-ящик', 'super_moto_box', imgui.ImInt(cfg.prices.super_moto_box), _, _},
	[24] = {'Ящик Marvel', 'Ящик Marvel', 'marvel_box', imgui.ImInt(cfg.prices.marvel_box), _, _},
	[25] = {'Ящик Джентельменов', 'Ящик Джентельменов', 'gentleman_box', imgui.ImInt(cfg.prices.gentleman_box), _, _},
	[26] = {'Ящик Minecraft', 'Ящик Minecraft', 'minecraft_box', imgui.ImInt(cfg.prices.minecraft_box), _, _},
	[27] = {'Одежда из секонд-хенда', 'Одежда из секонд-хенда', 'second_hand_box', imgui.ImInt(cfg.prices.second_hand_box), _, _},
}

function main()
	if not isSampLoaded() or not isSampfuncsLoaded() then return end
	while not isSampAvailable() do wait(100) end
	
	if log == nil then
		json('chests_opening_stats.json'):Save({})
		log = json('chests_opening_stats.json'):Load({})
	end

	sampRegisterChatCommand('chest', 
	function()
		main_window.v = not main_window.v 
		imgui.Process = main_window.v
	end)

	sampRegisterChatCommand('aoc', 
	function(arg)
		local timer_arg = tonumber(arg)
		if not work then
			if chest[1][3].v == false and chest[2][3].v == false and chest[3][3].v == false and chest[4][3].v == false and chest[5][3].v == false and chest[6][3].v == false and chest[7][3].v == false and chest[8][3].v == false and chest[9][3].v == false and chest[10][3].v == false and chest[11][3].v == false and chest[12][3].v == false and chest[13][3].v == false and chest[14][3].v == false and chest[15][3].v == false and chest[16][3].v == false and chest[17][3].v == false and chest[18][3].v == false and chest[19][3].v == false and chest[20][3].v == false and chest[21][3].v == false and chest[22][3].v == false and chest[23][3].v == false and chest[24][3].v == false and chest[25][3].v == false and chest[26][3].v == false and chest[27][3].v == false and chest[28][3].v == false and chest[29][3].v == false and chest[30][3].v == false and chest[31][3].v == false and chest[32][3].v == false and chest[33][3].v == false and chest[34][3].v == false and chest[35][3].v == false and chest[36][3].v == false and chest[37][3].v == false and chest[38][3].v == false and chest[39][3].v == false and delay_time.v == '' then
				sampAddChatMessage('[Информация] {FFFFFF}Вы не выбрали сундук и не указали задержку.', 0xFFFF00)
			elseif chest[1][3].v == false and chest[2][3].v == false and chest[3][3].v == false and chest[4][3].v == false and chest[5][3].v == false and chest[6][3].v == false and chest[7][3].v == false and chest[8][3].v == false and chest[9][3].v == false and chest[10][3].v == false and chest[11][3].v == false and chest[12][3].v == false and chest[13][3].v == false and chest[14][3].v == false and chest[15][3].v == false and chest[16][3].v == false and chest[17][3].v == false and chest[18][3].v == false and chest[19][3].v == false and chest[20][3].v == false and chest[21][3].v == false and chest[22][3].v == false and chest[23][3].v == false and chest[24][3].v == false and chest[25][3].v == false and chest[26][3].v == false and chest[27][3].v == false and chest[28][3].v == false and chest[29][3].v == false and chest[30][3].v == false and chest[31][3].v == false and chest[32][3].v == false and chest[33][3].v == false and chest[34][3].v == false and chest[35][3].v == false and chest[36][3].v == false and chest[37][3].v == false and chest[38][3].v == false and chest[39][3].v == false then
				sampAddChatMessage('[Информация] {FFFFFF}Вы не выбрали сундук.', 0xFFFF00)
			elseif delay_time.v == '' then
				sampAddChatMessage('[Информация] {FFFFFF}Вы не указали задержку.', 0xFFFF00) 
			else
				if not timer_arg or timer_arg <= 0 then
					work = true
					showCursor(false)
					main_window.v = false
					sampAddChatMessage('[Информация] {FFFFFF}Автоматическое открытие сундуков: {00FF00}включено{FFFFFF}.', 0xFFFF00)
					else	
					timer_time.v = arg
					timer.v = true
					work = true
					showCursor(false)
					main_window.v = false
					sampAddChatMessage('[Информация] {FFFFFF}Автоматическое открытие сундуков: {00FF00}включено{FFFFFF}.', 0xFFFF00)
					sampAddChatMessage('[Информация] {FFFFFF}Запуск через {FFFF00}'..timer_time.v..' {FFFFFF}мин.', 0xFFFF00)
				end
			end
		else
			sampSendClickTextdraw(65535)
			showCursor(false)
			thisScript():reload()
			sampAddChatMessage('[Информация] {FFFFFF}Автоматическое открытие сундуков: {FF0000}выключено{FFFFFF}.', 0xFFFF00)
		end
	end)
	
	sampRegisterChatCommand('cstats', 
	function()
		stats_window.v = not stats_window.v 
		imgui.Process = stats_window.v
	end)

	while true do
		wait(0)
		if work and cfg.settings.connected then
			if first_start and timer.v then
				wait(timer_time.v*60000)
				timer_time.v = ''
			end
			if first_start then
				sampSendClickTextdraw(65535)
				sampAddChatMessage('[Информация] {FFFFFF}Сейчас откроется инвентарь.', 0xFFFF00)
			elseif not first_start and not open_inventory.v then
				sampSendClickTextdraw(65535)
				sampAddChatMessage('[Информация] {FFFFFF}Сейчас откроется инвентарь.', 0xFFFF00)
			end
			wait(500)
			inventory_fix = true
			sampSendChat('/mn')
			wait(1000)
			if first_start then
				sampSendChat('/invent')
			elseif not first_start and not open_inventory.v then
				sampSendChat('/invent')
			elseif not first_start and open_inventory.v and not sampTextdrawIsExists(inventory_id) then
				sampSendChat('/invent')
			end
			if cfg.settings.connected then
				repeat wait(1) until sampTextdrawIsExists(inventory_id)
				wait(500)
			else
				wait(2000)
			end
			if chest[1][3].v then
				if chest[1][4] ~= nil then
					chest[1][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[1][4])
						wait(500)
						sampSendClickTextdraw(chest[1][5])
						wait(500)
					until chest[1][6] == false
					--sampAddChatMessage('1 chest', -1)
				else
					chest[1][3].v = false
					cfg.chests[chest[1][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Cундук рулетки» не найден.', 0xFFFF00)
				end
			end
			if chest[2][3].v and not block_donate then
				if chest[2][4] ~= nil then
					chest[2][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[2][4])
						wait(500)
						sampSendClickTextdraw(chest[2][5])
						wait(500)
					until chest[2][6] == false
					--sampAddChatMessage('2 chest', -1)
				else
					chest[2][3].v = false
					cfg.chests[chest[2][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Cундук рулетки (донат)» не найден.', 0xFFFF00)
				end
			elseif chest[2][3].v and block_donate then
				block_donate = false
				--sampAddChatMessage('2 chest block', -1)
			end
			if chest[3][3].v and not block_platinum then
				if chest[3][4] ~= nil then
					chest[3][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[3][4])
						wait(500)
						sampSendClickTextdraw(chest[3][5])
						wait(500)
					until chest[3][6] == false
					--sampAddChatMessage('3 chest', -1)
				else
					chest[3][3].v = false
					cfg.chests[chest[2][3]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Сундук платиновой рулетки» не найден.', 0xFFFF00)
				end
			elseif chest[3][3].v and block_platinum then
				block_platinum = false
				--sampAddChatMessage('3 chest block', -1)
			end
			if chest[4][3].v and not block_elon_musk1 then
				if chest[4][4] ~= nil then
					chest[4][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[4][4])
						wait(500)
						sampSendClickTextdraw(chest[4][5])
						wait(500)
					until chest[4][6] == false
					--sampAddChatMessage('4 chest', -1)
				else
					chest[4][3].v = false
					cfg.chests[chest[4][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник Илона Маска 1» не найден.', 0xFFFF00)
				end
			elseif chest[4][3].v and block_elon_musk1 then
				block_elon_musk1 = false
				--sampAddChatMessage('4 chest block', -1)
			end
			--
			if chest[5][3].v and not block_elon_musk2 then
				if chest[5][4] ~= nil then
					chest[5][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[5][4])
						wait(500)
						sampSendClickTextdraw(chest[5][5])
						wait(500)
					until chest[5][6] == false
					--sampAddChatMessage('5 chest', -1)
				else
					chest[5][3].v = false
					cfg.chests[chest[5][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник Илона Маска 2» не найден.', 0xFFFF00)
				end
			elseif chest[5][3].v and block_elon_musk2 then
				block_elon_musk2 = false
				--sampAddChatMessage('5 chest block', -1)
			end
			---2 mask
			if chest[6][3].v then
				if chest[6][4] ~= nil then
					chest[6][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[6][4])
						wait(500)
						sampSendClickTextdraw(chest[6][5])
						wait(500)
					until chest[6][6] == false
					--sampAddChatMessage('6 chest', -1)
				else
					chest[6][3].v = false
					cfg.chests[chest[6][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник Лос Сантоса» не найден.', 0xFFFF00)
				end
			end
			if chest[7][3].v then
				if chest[7][4] ~= nil then
					chest[7][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[7][4])
						wait(500)
						sampSendClickTextdraw(chest[7][5])
						wait(500)
					until chest[7][6] == false
					--sampAddChatMessage('7 chest', -1)
				else
					chest[7][3].v = false
					cfg.chests[chest[7][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник Vice City 1» не найден.', 0xFFFF00)
				end
			end
			if chest[8][3].v then
				if chest[8][4] ~= nil then
					chest[8][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[8][4])
						wait(500)
						sampSendClickTextdraw(chest[8][5])
						wait(500)
					until chest[8][6] == false
					--sampAddChatMessage('8 chest', -1)
				else
					chest[8][3].v = false
					cfg.chests[chest[8][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник Vice City 2» не найден.', 0xFFFF00)
				end
			end
			if chest[9][3].v then
				if chest[9][4] ~= nil then
					chest[9][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[9][4])
						wait(500)
						sampSendClickTextdraw(chest[9][5])
						wait(500)
					until chest[9][6] == false
					--sampAddChatMessage('9 chest', -1)
				else
					chest[9][3].v = false
					cfg.chests[chest[9][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник Vice City 3» не найден.', 0xFFFF00)
				end
			end
			if chest[10][3].v then
				if chest[10][4] ~= nil then
					chest[10][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[10][4])
						wait(500)
						sampSendClickTextdraw(chest[10][5])
						wait(500)
					until chest[10][6] == false
				else
					chest[10][3].v = false
					cfg.chests[chest[10][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 1» не найден.', 0xFFFF00)
				end
			end
			if chest[11][3].v then
				if chest[11][4] ~= nil then
					chest[11][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[11][4])
						wait(500)
						sampSendClickTextdraw(chest[11][5])
						wait(500)
					until chest[11][6] == false
				else
					chest[11][3].v = false
					cfg.chests[chest[11][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 2» не найден.', 0xFFFF00)
				end
			end
			if chest[12][3].v then
				if chest[12][4] ~= nil then
					chest[12][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[12][4])
						wait(500)
						sampSendClickTextdraw(chest[12][5])
						wait(500)
					until chest[12][6] == false
				else
					chest[12][3].v = false
					cfg.chests[chest[12][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 3» не найден.', 0xFFFF00)
				end
			end
			if chest[13][3].v then
				if chest[13][4] ~= nil then
					chest[13][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[13][4])
						wait(500)
						sampSendClickTextdraw(chest[13][5])
						wait(500)
					until chest[13][6] == false
				else
					chest[13][3].v = false
					cfg.chests[chest[13][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 4» не найден.', 0xFFFF00)
				end
			end
			if chest[14][3].v then
				if chest[14][4] ~= nil then
					chest[14][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[14][4])
						wait(500)
						sampSendClickTextdraw(chest[14][5])
						wait(500)
					until chest[14][6] == false
				else
					chest[14][3].v = false
					cfg.chests[chest[14][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 5» не найден.', 0xFFFF00)
				end
			end
			if chest[15][3].v then
				if chest[15][4] ~= nil then
					chest[15][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[15][4])
						wait(500)
						sampSendClickTextdraw(chest[15][5])
						wait(500)
					until chest[15][6] == false
				else
					chest[15][3].v = false
					cfg.chests[chest[15][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 6» не найден.', 0xFFFF00)
				end
			end
			if chest[16][3].v then
				if chest[16][4] ~= nil then
					chest[16][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[16][4])
						wait(500)
						sampSendClickTextdraw(chest[16][5])
						wait(500)
					until chest[16][6] == false
				else
					chest[16][3].v = false
					cfg.chests[chest[16][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 7» не найден.', 0xFFFF00)
				end
			end
			if chest[17][3].v then
				if chest[17][4] ~= nil then
					chest[17][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[17][4])
						wait(500)
						sampSendClickTextdraw(chest[17][5])
						wait(500)
					until chest[17][6] == false
				else
					chest[17][3].v = false
					cfg.chests[chest[17][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 8» не найден.', 0xFFFF00)
				end
			end
			if chest[18][3].v then
				if chest[18][4] ~= nil then
					chest[18][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[18][4])
						wait(500)
						sampSendClickTextdraw(chest[18][5])
						wait(500)
					until chest[18][6] == false
				else
					chest[18][3].v = false
					cfg.chests[chest[18][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 9» не найден.', 0xFFFF00)
				end
			end
			if chest[19][3].v then
				if chest[19][4] ~= nil then
					chest[19][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[19][4])
						wait(500)
						sampSendClickTextdraw(chest[19][5])
						wait(500)
					until chest[19][6] == false
				else
					chest[19][3].v = false
					cfg.chests[chest[19][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 10» не найден.', 0xFFFF00)
				end
			end
			if chest[20][3].v then
				if chest[20][4] ~= nil then
					chest[20][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[20][4])
						wait(500)
						sampSendClickTextdraw(chest[20][5])
						wait(500)
					until chest[20][6] == false
				else
					chest[20][3].v = false
					cfg.chests[chest[20][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 11» не найден.', 0xFFFF00)
				end
			end
			if chest[21][3].v then
				if chest[21][4] ~= nil then
					chest[21][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[21][4])
						wait(500)
						sampSendClickTextdraw(chest[21][5])
						wait(500)
					until chest[21][6] == false
				else
					chest[21][3].v = false
					cfg.chests[chest[21][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 12» не найден.', 0xFFFF00)
				end
			end
			if chest[22][3].v then
				if chest[22][4] ~= nil then
					chest[22][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[22][4])
						wait(500)
						sampSendClickTextdraw(chest[22][5])
						wait(500)
					until chest[22][6] == false
				else
					chest[22][3].v = false
					cfg.chests[chest[22][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 13» не найден.', 0xFFFF00)
				end
			end
			if chest[23][3].v then
				if chest[23][4] ~= nil then
					chest[23][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[23][4])
						wait(500)
						sampSendClickTextdraw(chest[23][5])
						wait(500)
					until chest[23][6] == false
				else
					chest[23][3].v = false
					cfg.chests[chest[23][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 14» не найден.', 0xFFFF00)
				end
			end
			if chest[24][3].v then
				if chest[24][4] ~= nil then
					chest[24][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[24][4])
						wait(500)
						sampSendClickTextdraw(chest[24][5])
						wait(500)
					until chest[24][6] == false
				else
					chest[24][3].v = false
					cfg.chests[chest[24][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 15» не найден.', 0xFFFF00)
				end
			end
			if chest[25][3].v then
				if chest[25][4] ~= nil then
					chest[25][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[25][4])
						wait(500)
						sampSendClickTextdraw(chest[25][5])
						wait(500)
					until chest[25][6] == false
				else
					chest[25][3].v = false
					cfg.chests[chest[25][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 16» не найден.', 0xFFFF00)
				end
			end
			if chest[26][3].v then
				if chest[26][4] ~= nil then
					chest[26][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[26][4])
						wait(500)
						sampSendClickTextdraw(chest[26][5])
						wait(500)
					until chest[26][6] == false
				else
					chest[26][3].v = false
					cfg.chests[chest[26][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 17» не найден.', 0xFFFF00)
				end
			end
			if chest[27][3].v then
				if chest[27][4] ~= nil then
					chest[27][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[27][4])
						wait(500)
						sampSendClickTextdraw(chest[27][5])
						wait(500)
					until chest[27][6] == false
				else
					chest[27][3].v = false
					cfg.chests[chest[27][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 18» не найден.', 0xFFFF00)
				end
			end
			if chest[28][3].v then
				if chest[28][4] ~= nil then
					chest[28][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[28][4])
						wait(500)
						sampSendClickTextdraw(chest[28][5])
						wait(500)
					until chest[28][6] == false
				else
					chest[28][3].v = false
					cfg.chests[chest[28][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 19» не найден.', 0xFFFF00)
				end
			end
			if chest[29][3].v then
				if chest[29][4] ~= nil then
					chest[29][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[29][4])
						wait(500)
						sampSendClickTextdraw(chest[29][5])
						wait(500)
					until chest[29][6] == false
				else
					chest[29][3].v = false
					cfg.chests[chest[29][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 20» не найден.', 0xFFFF00)
				end
			end
			if chest[30][3].v then
				if chest[30][4] ~= nil then
					chest[30][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[30][4])
						wait(500)
						sampSendClickTextdraw(chest[30][5])
						wait(500)
					until chest[30][6] == false
				else
					chest[30][3].v = false
					cfg.chests[chest[30][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 21» не найден.', 0xFFFF00)
				end
			end
			if chest[31][3].v then
				if chest[31][4] ~= nil then
					chest[31][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[31][4])
						wait(500)
						sampSendClickTextdraw(chest[31][5])
						wait(500)
					until chest[31][6] == false
				else
					chest[31][3].v = false
					cfg.chests[chest[31][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 22» не найден.', 0xFFFF00)
				end
			end
			if chest[32][3].v then
				if chest[32][4] ~= nil then
					chest[32][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[32][4])
						wait(500)
						sampSendClickTextdraw(chest[32][5])
						wait(500)
					until chest[32][6] == false
				else
					chest[32][3].v = false
					cfg.chests[chest[32][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 23» не найден.', 0xFFFF00)
				end
			end
			if chest[33][3].v then
				if chest[33][4] ~= nil then
					chest[33][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[33][4])
						wait(500)
						sampSendClickTextdraw(chest[33][5])
						wait(500)
					until chest[33][6] == false
				else
					chest[33][3].v = false
					cfg.chests[chest[33][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 24» не найден.', 0xFFFF00)
				end
			end
			if chest[34][3].v then
				if chest[34][4] ~= nil then
					chest[34][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[34][4])
						wait(500)
						sampSendClickTextdraw(chest[34][5])
						wait(500)
					until chest[34][6] == false
				else
					chest[34][3].v = false
					cfg.chests[chest[34][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 25» не найден.', 0xFFFF00)
				end
			end
			if chest[35][3].v then
				if chest[35][4] ~= nil then
					chest[35][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[35][4])
						wait(500)
						sampSendClickTextdraw(chest[35][5])
						wait(500)
					until chest[35][6] == false
				else
					chest[35][3].v = false
					cfg.chests[chest[35][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 26» не найден.', 0xFFFF00)
				end
			end
			if chest[36][3].v then
				if chest[36][4] ~= nil then
					chest[36][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[36][4])
						wait(500)
						sampSendClickTextdraw(chest[36][5])
						wait(500)
					until chest[36][6] == false
				else
					chest[36][3].v = false
					cfg.chests[chest[36][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 27» не найден.', 0xFFFF00)
				end
			end
			if chest[37][3].v then
				if chest[37][4] ~= nil then
					chest[37][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[37][4])
						wait(500)
						sampSendClickTextdraw(chest[37][5])
						wait(500)
					until chest[37][6] == false
				else
					chest[37][3].v = false
					cfg.chests[chest[37][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 28» не найден.', 0xFFFF00)
				end
			end
			if chest[38][3].v then
				if chest[38][4] ~= nil then
					chest[38][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[38][4])
						wait(500)
						sampSendClickTextdraw(chest[38][5])
						wait(500)
					until chest[38][6] == false
				else
					chest[38][3].v = false
					cfg.chests[chest[38][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 29» не найден.', 0xFFFF00)
				end
			end
			if chest[39][3].v then
				if chest[39][4] ~= nil then
					chest[39][6] = true
					repeat
						if not sampTextdrawIsExists(inventory_id) then
							sampSendChat('/invent')
							wait(500)
						end
						sampSendClickTextdraw(chest[39][4])
						wait(500)
						sampSendClickTextdraw(chest[39][5])
						wait(500)
					until chest[39][6] == false
				else
					chest[39][3].v = false
					cfg.chests[chest[39][2]] = false
					inicfg.save(cfg, 'auto_opening_chests.ini')
					sampAddChatMessage('[Информация] {FFFFFF}«Тайник собирателя 30» не найден.', 0xFFFF00)
				end
			end
			if chest[1][3].v == false and chest[2][3].v == false and chest[3][3].v == false and chest[4][3].v == false and chest[5][3].v == false and chest[6][3].v == false and chest[7][3].v == false and chest[8][3].v == false and chest[9][3].v == false and chest[10][3].v == false and chest[11][3].v == false and chest[12][3].v == false and chest[13][3].v == false and chest[14][3].v == false and chest[15][3].v == false and chest[16][3].v == false and chest[17][3].v == false and chest[18][3].v == false and chest[19][3].v == false and chest[20][3].v == false and chest[21][3].v == false and chest[22][3].v == false and chest[23][3].v == false and chest[24][3].v == false and chest[25][3].v == false and chest[26][3].v == false and chest[27][3].v == false and chest[28][3].v == false and chest[29][3].v == false and chest[30][3].v == false and chest[31][3].v == false and chest[32][3].v == false and chest[33][3].v == false and chest[34][3].v == false and chest[35][3].v == false and chest[36][3].v == false and chest[37][3].v == false and chest[38][3].v == false and chest[39][3].v == false then
				sampSendClickTextdraw(65535)
				showCursor(false)
				thisScript():reload()
				sampAddChatMessage('[Информация] {FFFFFF}Автоматическое открытие сундуков: {FF0000}выключено{FFFFFF}.', 0xFFFF00)
			end
			wait(500)
			if not open_inventory.v then
				sampSendClickTextdraw(65535)
			end
			if not random_delay.v then
				wait(delay_time.v*60000)
			else
				wait(delay_time.v*60000+math.random(0, 900000))
			end
			first_start = false
        end
    end
end

function imgui.OnDrawFrame()
	if not main_window.v and not stats_window.v then imgui.Process = false end
	if main_window.v then
		imgui.SetNextWindowPos(imgui.ImVec2(sw/2, sh/2), imgui.Cond.FirstUseEver, imgui.ImVec2(0.5, 0.5))
		imgui.SetNextWindowSize(imgui.ImVec2(343, 260), imgui.Cond.FirstUseEver)
		imgui.Begin(u8'Автоматическое открытие сундуков', main_window, imgui.WindowFlags.NoCollapse + imgui.WindowFlags.NoResize)
		imgui.BeginChild('##menu', imgui.ImVec2(116, 172), true)
		imgui.CenterText(u8'Меню')
		imgui.Separator()
		if imgui.Button(u8'Cундуки', imgui.ImVec2(100, 28)) then imgui_page = 1 end
		if imgui.Button(u8'Настройки', imgui.ImVec2(100, 28)) then imgui_page = 2 end
		if imgui.Button(u8'Информация', imgui.ImVec2(100, 28)) then imgui_page = 3 end
		imgui.Separator()
		if work then 
			imgui.PushStyleColor(imgui.Col.Button, imgui.ImVec4(0.13, 0.13, 0.13, 1.00))
			imgui.PushStyleColor(imgui.Col.ButtonHovered, imgui.ImVec4(0.66, 0.00, 0.00, 1.00))
			imgui.PushStyleColor(imgui.Col.ButtonActive, imgui.ImVec4(0.50, 0.00, 0.00, 1.00))
		else
			imgui.PushStyleColor(imgui.Col.Button, imgui.ImVec4(0.13, 0.13, 0.13, 1.00))
			imgui.PushStyleColor(imgui.Col.ButtonHovered, imgui.ImVec4(0.00, 0.66, 0.00, 1.00))
			imgui.PushStyleColor(imgui.Col.ButtonActive, imgui.ImVec4(0.00, 0.50, 0.00, 1.00))
		end
		if imgui.Button(work and u8'Выключить' or u8'Включить', imgui.ImVec2(100, 30)) then 
			if not work then
				if chest[1][3].v == false and chest[2][3].v == false and chest[3][3].v == false and chest[4][3].v == false and chest[5][3].v == false and chest[6][3].v == false and chest[7][3].v == false and chest[8][3].v == false and chest[9][3].v == false and chest[10][3].v == false and delay_time.v == '' then
					sampAddChatMessage('[Информация] {FFFFFF}Вы не выбрали сундук и не указали задержку.', 0xFFFF00)
				elseif chest[1][3].v == false and chest[2][3].v == false and chest[3][3].v == false and chest[4][3].v == false and chest[5][3].v == false and chest[6][3].v == false and chest[7][3].v == false and chest[8][3].v == false and chest[9][3].v == false and chest[10][3].v == false then
					sampAddChatMessage('[Информация] {FFFFFF}Вы не выбрали сундук.', 0xFFFF00)
				elseif delay_time.v == '' then
					sampAddChatMessage('[Информация] {FFFFFF}Вы не указали задержку.', 0xFFFF00) 
				else
					work = true
					showCursor(false)
					main_window.v = false
					if timer.v and timer_time.v ~= '' then
						sampAddChatMessage('[Информация] {FFFFFF}Автоматическое открытие сундуков: {00FF00}включено{FFFFFF}.', 0xFFFF00)
						sampAddChatMessage('[Информация] {FFFFFF}Запуск через {FFFF00}'..timer_time.v..' {FFFFFF}мин.', 0xFFFF00)
					else
						sampAddChatMessage('[Информация] {FFFFFF}Автоматическое открытие сундуков: {00FF00}включено{FFFFFF}.', 0xFFFF00)
					end
				end
			else
				sampSendClickTextdraw(65535)
				showCursor(false)
				thisScript():reload()
				sampAddChatMessage('[Информация] {FFFFFF}Автоматическое открытие сундуков: {FF0000}выключено{FFFFFF}.', 0xFFFF00)
			end
		end
		imgui.PopStyleColor(3)
		imgui.EndChild()
		imgui.SameLine()
		if imgui_page == 1 then
			imgui.BeginChild('##chests', imgui.ImVec2(206, 266), true)
			imgui.CenterText(u8'Сундуки')
			imgui.Separator()
			for k in ipairs(chest) do
				imgui.Checkbox(u8(chest[k][1]), chest[k][3])
				if chest[k][3].v then
					if cfg.chests[chest[k][2]] ~= chest[k][3].v then
						cfg.chests[chest[k][2]] = true
						inicfg.save(cfg, 'auto_opening_chests.ini')
					end
				else
					if cfg.chests[chest[k][2]] ~= chest[k][3].v then
						cfg.chests[chest[k][2]] = false
						inicfg.save(cfg, 'auto_opening_chests.ini')
					end
				end
			end
			imgui.EndChild()
			imgui.SetWindowSize(imgui.ImVec2(343, 302))
		end
		if imgui_page == 2 then
			imgui.SetWindowSize(imgui.ImVec2(343, 204))
			imgui.BeginChild('##settings', imgui.ImVec2(206, 172), true)
			imgui.CenterText(u8'Настройки')
			imgui.Separator()
			imgui.Checkbox(u8'Задержка:', delay)
			if delay_time.v ~= '' then
				delay.v = true
			else
				delay.v = false
			end
			imgui.PushItemWidth(26)
			imgui.InputText(u8'мин.##delay', delay_time, imgui.InputTextFlags.CharsDecimal, imgui.SameLine())
			if delay_time.v then
				cfg.settings.delay_time = delay_time.v
				inicfg.save(cfg, 'auto_opening_chests.ini')
			end
			imgui.Checkbox(u8'Рандомная задержка', random_delay)
			if random_delay.v then 
				cfg.settings.random_delay = true
				inicfg.save(cfg, 'auto_opening_chests.ini')
			else
				cfg.settings.random_delay = false
				inicfg.save(cfg, 'auto_opening_chests.ini')
			end
			imgui.Checkbox(u8'ADD VIP', add_vip)
			if add_vip.v then 
				cfg.settings.add_vip = true
				inicfg.save(cfg, 'auto_opening_chests.ini')
			else
				cfg.settings.add_vip = false
				inicfg.save(cfg, 'auto_opening_chests.ini')
			end
			imgui.Checkbox(u8'Не закрывать инвентарь', open_inventory)
			if open_inventory.v then 
				cfg.settings.open_inventory = true
				inicfg.save(cfg, 'auto_opening_chests.ini')
			else
				cfg.settings.open_inventory = false
				inicfg.save(cfg, 'auto_opening_chests.ini')
			end
			imgui.Checkbox(u8'Запустить через:', timer)
			imgui.InputText(u8'мин.##timer', timer_time, imgui.InputTextFlags.CharsDecimal, imgui.SameLine())
			if timer_time.v ~= '' then
				timer.v = true
			else
				timer.v = false
			end
			imgui.PopItemWidth()
			imgui.EndChild()
		end
		if imgui_page == 3 then
			imgui.SetWindowSize(imgui.ImVec2(343, 204))
			imgui.BeginChild('##information', imgui.ImVec2(206, 172), true)
			imgui.CenterText(u8'Информация')
			imgui.Separator()
			imgui.TextColoredRGB('{FFFFFF}Автор скрипта: {AE433D}Severus')
			imgui.TextColoredRGB('{FFFFFF}Обновлено by {FF00FF}AlexKrut')
			imgui.TextColoredRGB('{FFFFFF}Обновление: {AE433D}25.05.2024')
			imgui.Text(u8'- Команды:')
			imgui.TextColoredRGB('{AE433D}/aoc [time] {FFFFFF}- быстрый запуск')
			imgui.TextColoredRGB('{AE433D}/cstats {FFFFFF}- статистика открытия')
			imgui.Separator()
			if imgui.Link(u8'www.blast.hk/threads/150314') then
				os.execute(('explorer.exe "%s"'):format('http://www.blast.hk/threads/150314/'))
			end
			imgui.EndChild()
		end
		imgui.End()
	end
	if stats_window.v then
		imgui.SetNextWindowPos(imgui.ImVec2(sw/2, sh/2), imgui.Cond.FirstUseEver, imgui.ImVec2(0.5, 0.5))
		imgui.SetNextWindowSize(imgui.ImVec2(366, 418), imgui.Cond.FirstUseEver) -- всё окно
		imgui.Begin(u8'Статистика открытия сундуков', stats_window, imgui.WindowFlags.NoCollapse + imgui.WindowFlags.NoResize)
		imgui.BeginChild('##stats_window', imgui.ImVec2(354, 386), true) --целое окно с ларцами и кнопками
		imgui.SetCursorPosX((imgui.GetWindowHeight()-imgui.CalcTextSize(u8'Статистика за: '..temp_date).x)/3+25)
		imgui.TextColoredRGB('{FFFFFF}Статистика за: {FFD700}'..temp_date)
		imgui.Separator()
		imgui.BeginChild('##stats', imgui.ImVec2(340, 286), false) --список ларцов не включая рамку
		for k in ipairs(item) do
			if log[temp_date] ~= nil then
				if temp_date ~= last_date then
					profit = 0
					last_date = temp_date
				end
				if log[temp_date][item[k][1]] ~= nil then
					imgui.TextColoredRGB('{FFFFFF}- '..item[k][1]..': {FFD700}'..log[temp_date][item[k][1]]..' {FFFFFF}шт. {42B02C}('..money_separator(log[temp_date][item[k][1]]*cfg.prices[item[k][3]])..'$)')
					if item[k][6] ~= temp_date then
						item[k][5] = nil
						item[k][6] = nil
					end
					if item[k][5] ~= log[temp_date][item[k][1]]*cfg.prices[item[k][3]] then
						if item[k][5] == nil then
							profit = profit+log[temp_date][item[k][1]]*cfg.prices[item[k][3]]
						else
							profit = (profit+log[temp_date][item[k][1]]*cfg.prices[item[k][3]])-item[k][5]
						end
						item[k][5] = log[temp_date][item[k][1]]*cfg.prices[item[k][3]]
						item[k][6] = temp_date
					end
				else
					item[k][5] = nil
					item[k][6] = nil
				end
			end
		end
		imgui.EndChild()
		imgui.Separator()
		imgui.SetCursorPosX((imgui.GetWindowHeight()-imgui.CalcTextSize(u8'Итог: '..money_separator(profit)..'$').x)/3+48)
		imgui.TextColoredRGB('{FFFFFF}Итог: {42B02C}'..money_separator(profit)..'$')
		imgui.Separator()
		if imgui.Button(u8'Выбрать дату', imgui.ImVec2(108, 28)) then
			imgui.OpenPopup(u8'Выбор даты')
		end
		if imgui.BeginPopupModal(u8'Выбор даты', _, imgui.WindowFlags.NoCollapse + imgui.WindowFlags.NoResize + imgui.WindowFlags.NoMove) then
			imgui.SetWindowSize(imgui.ImVec2(180, 180))
			imgui.BeginChild('##dates_window', imgui.ImVec2(164, 146), true)
			imgui.BeginChild('##dates', imgui.ImVec2(154, 94), false)
			if log[temp_date] ~= nil then
				local tkeys = {}
				for k in pairs(log) do table.insert(tkeys, k) end
				table.sort(tkeys, function(a, b)
					local d, m, y = a:match('(%d+).(%d+).(%d+)')
					local d2, m2, y2 = b:match('(%d+).(%d+).(%d+)')
					return y..m..d > y2..m2..d2
				end)
				for _, k in ipairs(tkeys) do
					if imgui.Selectable(' '..k) then
						temp_date = k
						imgui.CloseCurrentPopup()
					end
					if k == temp_date then
						imgui.TextColoredRGB('{42B02C}(выбрано)', imgui.SameLine())
					end
				end
			else
				imgui.SetCursorPosY((imgui.GetWindowHeight()-imgui.CalcTextSize(u8'Пусто').y)/2)
				imgui.CenterText(u8'Пусто')
			end
			imgui.EndChild()
			imgui.Separator()
			if imgui.Button(u8('Закрыть'), imgui.ImVec2(-1, 28)) then
				imgui.CloseCurrentPopup()
			end
			imgui.EndChild()
			imgui.EndPopup()
		end
		if imgui.Button(u8'Изменить цены', imgui.ImVec2(108, 28), imgui.SameLine()) then
			imgui.OpenPopup(u8'Установка цен на рулетки / ларцы')
		end
		if imgui.BeginPopupModal(u8'Установка цен на рулетки / ларцы', _, imgui.WindowFlags.NoCollapse + imgui.WindowFlags.NoResize) then
			imgui.SetWindowSize(imgui.ImVec2(412, 308))
			imgui.BeginChild('##prices_window', imgui.ImVec2(396, 274), true)
			imgui.BeginChild('##prices', imgui.ImVec2(386, 222), false)
			imgui.PushItemWidth(54)
			for k, v in ipairs(item) do
				imgui.TextColoredRGB('{FFFFFF}- '..item[k][1]..': {42B02C}('..money_separator(cfg.prices[item[k][3]])..'$)')
				imgui.InputInt(u8'$##'..k, item[k][4], 0, 0, imgui.SameLine(300))
				if item[k][4].v then
					if item[k][4].v < 0 then item[k][4].v = 0 end
					if item[k][4].v > 9999999 then item[k][4].v = 9999999 end
					if cfg.prices[item[k][3]] ~= item[k][4].v then
						cfg.prices[item[k][3]] = item[k][4].v
						inicfg.save(cfg, 'auto_opening_chests.ini')
					end
				end
				imgui.Separator()
			end
			imgui.PopItemWidth()
			imgui.EndChild()
			imgui.Separator()
			if imgui.Button(u8('Закрыть'), imgui.ImVec2(-1, 28)) then
				imgui.CloseCurrentPopup()
			end
			imgui.EndChild()
			imgui.EndPopup()
		end
		if imgui.Button(u8'Настройки', imgui.ImVec2(108, 28), imgui.SameLine()) then
			sampAddChatMessage('[Информация] {FFFFFF}В разработке...', 0xFFFF00)
		end
		imgui.EndChild()
		imgui.End()
	end
end


function table.remove_by_value(tbl, value)
    for i, v in ipairs(tbl) do
        if v == value then
            table.remove(tbl, i)
            return
        end
    end
end


function se.onShowTextDraw(id, data)
	if data.text == 'INVENTORY' or data.text == '…H‹EHЏAP’' and data.style == 2 and data.letterColor == -1 then
		inventory_id = id
		Vc_ids = {}
		Mask_ids = {}
		Sobiratel_ids = {}
	end
	if work then
		if data.modelId == 1333 and data.rotation.x == -120 and data.rotation.y == 0 and data.rotation.z == 180 and data.backgroundColor == -13487452 then
			table.insert(Vc_ids, id)
			--sampAddChatMessage('VC IDS', -1)
		end
		if data.modelId == 1733 and data.rotation.x == 180 and data.rotation.y == 0 and data.rotation.z == 20 and data.backgroundColor == -13469276 then
			table.insert(Mask_ids, id)
			--sampAddChatMessage('MASK IDS', -1)
		end
		if data.zoom == 2 and data.modelId == 0 and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.backgroundColor == -13469276 then
			table.insert(Sobiratel_ids, id)
		end
		if chest[1][3].v and data.modelId == 19918 and data.rotation.x == 161 and data.rotation.y == 174 and data.rotation.z == 126 and data.backgroundColor == -13421773 then
			chest[1][4] = id
		end
		if chest[2][3].v and data.modelId == 19613 and data.rotation.x == 180 and data.rotation.y == 180 and data.rotation.z == 0 and data.backgroundColor == -13421773 then
			chest[2][4] = id
		end
		if chest[3][3].v and data.modelId == 1353 and data.rotation.x == 0 and data.rotation.y == 180 and data.rotation.z == 120 and data.backgroundColor == -13469276 then
			chest[3][4] = id
		end
		if chest[4][3].v and data.modelId == 1733 and data.rotation.x == 180 and data.rotation.y == 0 and data.rotation.z == 20 and data.backgroundColor == -13469276 then
			if Mask_ids[1] then
				chest[4][4] = Mask_ids[1]
				--sampAddChatMessage('mask 1 '.. Mask_ids[1], -1)
			end
		end
		if chest[5][3].v and data.modelId == 1733 and data.rotation.x == 180 and data.rotation.y == 0 and data.rotation.z == 20 and data.backgroundColor == -13469276 then
			if Mask_ids[2] then
				chest[5][4] = Mask_ids[2]
				--sampAddChatMessage('mask 2 '.. Mask_ids[2], -1)
			end
		end
		if chest[6][3].v and data.modelId == 2887 and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 180 and data.backgroundColor == -13469276 then
			chest[6][4] = id
		end
		if chest[7][3].v and data.modelId == 1333 and data.rotation.x == -120 and data.rotation.y == 0 and data.rotation.z == 180 and data.backgroundColor == -13487452 then
			if Vc_ids[1] then
				chest[7][4] = Vc_ids[1]
				--sampAddChatMessage('vc 1 '.. Vc_ids[1], -1)
			end
		end
		if chest[8][3].v and data.modelId == 1333 and data.rotation.x == -120 and data.rotation.y == 0 and data.rotation.z == 180 and data.backgroundColor == -13487452 then
			if Vc_ids[2] then
				chest[8][4] = Vc_ids[2]
				--sampAddChatMessage('vc 2 '.. Vc_ids[2], -1)
			end
		end
		if chest[9][3].v and data.modelId == 1333 and data.rotation.x == -120 and data.rotation.y == 0 and data.rotation.z == 180 and data.backgroundColor == -13487452  then
			if Vc_ids[3] then
				chest[9][4] = Vc_ids[3]
				--sampAddChatMessage('vc 3 '.. Vc_ids[3], -1)
			end
		end
		if chest[10][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[1] then
				chest[10][4] = Sobiratel_ids[1]
			end
		end
		if chest[11][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[2] then
				chest[11][4] = Sobiratel_ids[2]
			end
		end
		if chest[12][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[3] then
				chest[12][4] = Sobiratel_ids[3]
			end
		end
		if chest[13][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[4] then
				chest[13][4] = Sobiratel_ids[4]
			end
		end
		if chest[14][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[5] then
				chest[14][4] = Sobiratel_ids[5]
			end
		end
		if chest[15][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[6] then
				chest[15][4] = Sobiratel_ids[6]
			end
		end
		if chest[16][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[7] then
				chest[16][4] = Sobiratel_ids[7]
			end
		end
		if chest[17][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[8] then
				chest[17][4] = Sobiratel_ids[8]
			end
		end
		if chest[18][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[9] then
				chest[18][4] = Sobiratel_ids[9]
			end
		end
		if chest[19][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[10] then
				chest[19][4] = Sobiratel_ids[10]
			end
		end
		if chest[20][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[11] then
				chest[20][4] = Sobiratel_ids[11]
			end
		end
		if chest[21][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[12] then
				chest[21][4] = Sobiratel_ids[12]
			end
		end
		if chest[22][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[13] then
				chest[22][4] = Sobiratel_ids[13]
			end
		end
		if chest[23][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[14] then
				chest[23][4] = Sobiratel_ids[14]
			end
		end
		if chest[24][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[15] then
				chest[24][4] = Sobiratel_ids[15]
			end
		end
		if chest[25][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[16] then
				chest[25][4] = Sobiratel_ids[16]
			end
		end
		if chest[26][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[17] then
				chest[26][4] = Sobiratel_ids[17]
			end
		end
		if chest[27][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[18] then
				chest[27][4] = Sobiratel_ids[18]
			end
		end
		if chest[28][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[19] then
				chest[28][4] = Sobiratel_ids[19]
			end
		end
		if chest[29][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[20] then
				chest[29][4] = Sobiratel_ids[20]
			end
		end
		if chest[30][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[21] then
				chest[30][4] = Sobiratel_ids[21]
			end
		end
		if chest[31][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[22] then
				chest[31][4] = Sobiratel_ids[22]
			end
		end
		if chest[32][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[23] then
				chest[32][4] = Sobiratel_ids[23]
			end
		end
		if chest[33][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[24] then
				chest[33][4] = Sobiratel_ids[24]
			end
		end
		if chest[34][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[25] then
				chest[34][4] = Sobiratel_ids[25]
			end
		end
		if chest[35][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[26] then
				chest[35][4] = Sobiratel_ids[26]
			end
		end
		if chest[36][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[27] then
				chest[36][4] = Sobiratel_ids[27]
			end
		end
		if chest[37][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[28] then
				chest[37][4] = Sobiratel_ids[28]
			end
		end
		if chest[38][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[29] then
				chest[38][4] = Sobiratel_ids[29]
			end
		end
		if chest[39][3] and data.rotation.x == 0 and data.rotation.y == 0 and data.rotation.z == 90 and data.zoom == 2 and data.backgroundColor == -13469276 then
			if Sobiratel_ids[30] then
				chest[39][4] = Sobiratel_ids[30]
			end
		end
		
		if data.text == 'USE' or data.text == '…CЊO‡’€O‹AЏ’' then 
			chest[1][5] = id + 1 --сундук рулетки
			chest[2][5] = id + 1 --сундук донат рулетки
			chest[3][5] = id + 1 --сундук платиновой рулетки
			chest[4][5] = id + 1 --тайник маска 1
			chest[5][5] = id + 1 --тайник маска 2
			chest[6][5] = id + 1 --тайник ЛС
			chest[7][5] = id + 1 --тайники ВС 1
			chest[8][5] = id + 1 --тайники ВС 2
			chest[9][5] = id + 1 --тайники ВС 3
			chest[10][5] = id + 1 --тайник собирателя 1
			chest[11][5] = id + 1 --тайник собирателя 2
			chest[12][5] = id + 1 --тайник собирателя 3
			chest[13][5] = id + 1 --тайник собирателя 4
			chest[14][5] = id + 1 --тайник собирателя 5
			chest[15][5] = id + 1 --тайник собирателя 6
			chest[16][5] = id + 1 --тайник собирателя 7
			chest[17][5] = id + 1 --тайник собирателя 8
			chest[18][5] = id + 1 --тайник собирателя 9
			chest[19][5] = id + 1 --тайник собирателя 10
			chest[20][5] = id + 1 --тайник собирателя 11
			chest[21][5] = id + 1 --тайник собирателя 12
			chest[22][5] = id + 1 --тайник собирателя 13
			chest[23][5] = id + 1 --тайник собирателя 14
			chest[24][5] = id + 1 --тайник собирателя 15
			chest[25][5] = id + 1 --тайник собирателя 16
			chest[26][5] = id + 1 --тайник собирателя 17
			chest[27][5] = id + 1 --тайник собирателя 18
			chest[28][5] = id + 1 --тайник собирателя 19
			chest[29][5] = id + 1 --тайник собирателя 20
			chest[30][5] = id + 1 --тайник собирателя 21
			chest[31][5] = id + 1 --тайник собирателя 22
			chest[32][5] = id + 1 --тайник собирателя 23
			chest[33][5] = id + 1 --тайник собирателя 24
			chest[34][5] = id + 1 --тайник собирателя 25
			chest[35][5] = id + 1 --тайник собирателя 26
			chest[36][5] = id + 1 --тайник собирателя 27
			chest[37][5] = id + 1 --тайник собирателя 28
			chest[38][5] = id + 1 --тайник собирателя 29
			chest[39][5] = id + 1 --тайник собирателя 30
		end
	end
end

function se.onShowDialog(dialogId, style, title, b1, b2, text)
	if inventory_fix and title:find('Игровое меню') then
		sampSendDialogResponse(dialogId, 0, nil, nil)
		inventory_fix = false
		return false
	end
	if dialogId == 0 and text:find('{FF0000}К сожалению сундук сейчас открыть не получится') and work then
		sampSendClickTextdraw(65535)
		showCursor(false)
		thisScript():reload()
	end
	if dialogId == 0 and text:find('Удача!') then 
		sampAddChatMessage('[Информация] {FFFFFF}Вам был добавлен предмет «Эффект x4 пополнение счёта».', 0xFFFF00)
		sampSendDialogResponse(dialogId, 1, nil, nil)
		return false
	end
end

function se.onServerMessage(color, text)
	if text:find('^%[Информация%] %{ffffff%}Вы использовали сундук с рулетками и получили') then
		local drop_starter_donate = text:match('^%[Информация%] %{ffffff%}Вы использовали сундук с рулетками и получили (.+)!')
		if log[os.date('%d.%m.%Y')] == nil then log[os.date('%d.%m.%Y')] = {} end
		for i in pairs(item) do
			if item[i][2] == drop_starter_donate then
				if log[os.date('%d.%m.%Y')][item[i][1]] == nil then
					log[os.date('%d.%m.%Y')][item[i][1]] = 1
				else
					log[os.date('%d.%m.%Y')][item[i][1]] = log[os.date('%d.%m.%Y')][item[i][1]] + 1
				end
				drop_starter_donate = nil
			end
		end
		json('chests_opening_stats.json'):Save(log)
		if chest[1][6] then chest[1][6] = false --sampAddChatMessage('1 chest open', -1) 
		end
		if chest[2][6] then 
			if add_vip.v then block_donate = true end
			chest[2][6] = false
			--sampAddChatMessage('2 chest open', -1)
		end
	elseif chest[1][6] and text:find('^%[Ошибка%] %{ffffff%}Время после прошлого использования ещё не прошло!') then
		chest[1][6] = false
		--sampAddChatMessage('1 chest kd', -1)
	elseif chest[1][6] and text:find('^%[Ошибка%] %{ffffff%}Открывать этот сундук можно только с 3 уровня!') then
		sampSendClickTextdraw(65535)
		showCursor(false)
		thisScript():reload()
	elseif chest[2][6] and text:find('^%[Ошибка%] %{ffffff%}Время после прошлого использования ещё не прошло!') then
		if add_vip.v then block_donate = false end
		chest[2][6] = false
		--sampAddChatMessage('2 chest kd', -1)
	end	
	if text:find('^%[Информация%] %{ffffff%}Вы использовали платиновый сундук с рулетками и получили') then
		local drop_platinum = text:match('^%[Информация%] %{ffffff%}Вы использовали платиновый сундук с рулетками и получили (.+)!')
		if log[os.date('%d.%m.%Y')] == nil then log[os.date('%d.%m.%Y')] = {} end
		for i in pairs(item) do
			if item[i][2] == drop_platinum then
				if log[os.date('%d.%m.%Y')][item[i][1]] == nil then
					log[os.date('%d.%m.%Y')][item[i][1]] = 1
				else
					log[os.date('%d.%m.%Y')][item[i][1]] = log[os.date('%d.%m.%Y')][item[i][1]] + 1
				end
				drop_platinum = nil
			end
		end
		json('chests_opening_stats.json'):Save(log)
		if chest[3][6] then
			if add_vip.v then block_platinum = true end
			chest[3][6] = false
			--sampAddChatMessage('3 chest open', -1)
		end
	elseif chest[3][6] and text:find('^%[Ошибка%] %{ffffff%}Время после прошлого использования ещё не прошло!') then
		if add_vip.v then block_platinum = false end
		chest[3][6] = false
		--sampAddChatMessage('3 chest kd', -1)
	end
	if text:find('^%[Информация%] %{ffffff%}Вы использовали тайник Илона Маска и получили') then
		local drop_elon_musk = text:match('^%[Информация%] %{ffffff%}Вы использовали тайник Илона Маска и получили (.+)!')
		if log[os.date('%d.%m.%Y')] == nil then log[os.date('%d.%m.%Y')] = {} end
		if 'Ларец с премией' == drop_elon_musk then
			if log[os.date('%d.%m.%Y')][item[5][1]] == nil then
				log[os.date('%d.%m.%Y')][item[5][1]] = 1
			else
				log[os.date('%d.%m.%Y')][item[5][1]] = log[os.date('%d.%m.%Y')][item[5][1]] + 1
			end
			drop_elon_musk = nil
		elseif 'Ларец Super Car' == drop_elon_musk then
			if log[os.date('%d.%m.%Y')][item[6][1]] == nil then
				log[os.date('%d.%m.%Y')][item[6][1]] = 1
			else
				log[os.date('%d.%m.%Y')][item[6][1]] = log[os.date('%d.%m.%Y')][item[6][1]] + 1
			end
			drop_elon_musk = nil
		end
		json('chests_opening_stats.json'):Save(log)
		if chest[4][6] then
			if add_vip.v then block_elon_musk1 = true end
			chest[4][6] = false
			--sampAddChatMessage('4 chest open', -1)
		end
		if chest[5][6] then
			if add_vip.v then block_elon_musk2 = true end
			chest[5][6] = false
			--sampAddChatMessage('5 chest open', -1)
		end
	elseif chest[4][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть контейнер через (.+).') then
		if add_vip.v then block_elon_musk1 = false end
		chest[4][6] = false
		--sampAddChatMessage('4 chest kd', -1)
	elseif chest[5][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть контейнер через (.+).') then
		if add_vip.v then block_elon_musk2 = false end
		chest[5][6] = false
		--sampAddChatMessage('5 chest kd', -1)
	end
	if text:find('^Вы открыли Тайник Лос Сантоса!') or text:find('^Вы открыли Тайник Vice City!') then
	elseif text:find('^%[Информация%] %{ffffff%}Получено: (.+) и (.+)!') then
		local drop_ls_vc_1, drop_ls_vc_2 = text:match('^%[Информация%] %{ffffff%}Получено: (.+) и (.+)!')
		if log[os.date('%d.%m.%Y')] == nil then log[os.date('%d.%m.%Y')] = {} end
		for i in pairs(item) do
			if item[i][2] == drop_ls_vc_1 then
				if log[os.date('%d.%m.%Y')][item[i][1]] == nil then
					log[os.date('%d.%m.%Y')][item[i][1]] = 1
				else
					log[os.date('%d.%m.%Y')][item[i][1]] = log[os.date('%d.%m.%Y')][item[i][1]] + 1
				end
				drop_ls_vc_1 = nil
			end
			if item[i][2] == drop_ls_vc_2 then
				if log[os.date('%d.%m.%Y')][item[i][1]] == nil then
					log[os.date('%d.%m.%Y')][item[i][1]] = 1
				else
					log[os.date('%d.%m.%Y')][item[i][1]] = log[os.date('%d.%m.%Y')][item[i][1]] + 1
				end
				drop_ls_vc_2 = nil
			end
		end
		json('chests_opening_stats.json'):Save(log)
		if chest[6][6] then chest[6][6] = false --sampAddChatMessage('6 chest open', -1) 
		end
		if chest[7][6] then chest[7][6] = false --sampAddChatMessage('7 chest open', -1) 
		end
		if chest[8][6] then chest[8][6] = false --sampAddChatMessage('7 chest open', -1) 
		end
		if chest[9][6] then chest[9][6] = false --sampAddChatMessage('9 chest open', -1) 
		end
	elseif chest[6][6] and text:find('^%[Ошибка%] %{ffffff%}Время после прошлого использования ещё не прошло!') then
		chest[6][6] = false
		--sampAddChatMessage('6 chest kd', -1)
	elseif chest[7][6] then
		if text:find('^%[Подсказка%] %{ffffff%}Вы открыли максимальное количество Тайников VC (.+).') then
			chest[7][6] = false
			--sampAddChatMessage('7 chest kd max', -1)
		elseif text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть контейнер через (.+).') then
			chest[7][6] = false
			--sampAddChatMessage('7 chest kd', -1)
		end
	elseif chest[8][6] then
		if text:find('^%[Подсказка%] %{ffffff%}Вы открыли максимальное количество Тайников VC (.+).') then
			chest[8][6] = false
			--sampAddChatMessage('8 chest kd max', -1)
		elseif text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть контейнер через (.+).') then
			chest[8][6] = false
			--sampAddChatMessage('8 chest kd', -1)
		end
	elseif chest[9][6] then
		if text:find('^%[Подсказка%] %{ffffff%}Вы открыли максимальное количество Тайников VC (.+).') then
			chest[9][6] = false
			--sampAddChatMessage('9 chest kd max', -1)
		elseif text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть контейнер через (.+).') then
			chest[9][6] = false
			--sampAddChatMessage('9 chest kd', -1)
		end
	end
    if text:find('^Вы открыли Тайник Собирателя!')then
    elseif text:find('^%[Информация%] %{ffffff%}Получено: (.+)!') then
        local drop_sob = text:match('^%[Информация%] %{ffffff%}Получено: (.+)!')
        if log[os.date('%d.%m.%Y')] == nil then log[os.date('%d.%m.%Y')] = {} end
        for i in pairs(item) do
            if item[i][2] == drop_sob then
                if log[os.date('%d.%m.%Y')][item[i][1]] == nil then
                    log[os.date('%d.%m.%Y')][item[i][1]] = 1
                else
                    log[os.date('%d.%m.%Y')][item[i][1]] = log[os.date('%d.%m.%Y')][item[i][1]] + 1
                end
                drop_sob = nil
            end
        end
        json('chests_opening_stats.json'):Save(log)
        if chest[10][6] then chest[10][6] = false
        end
        if chest[11][6] then chest[11][6] = false
        end
        if chest[12][6] then chest[12][6] = false
        end
        if chest[13][6] then chest[13][6] = false
        end
        if chest[14][6] then chest[14][6] = false
        end
        if chest[15][6] then chest[15][6] = false
        end
        if chest[16][6] then chest[16][6] = false
        end
        if chest[17][6] then chest[17][6] = false
        end
        if chest[18][6] then chest[18][6] = false
        end
        if chest[19][6] then chest[19][6] = false
        end
        if chest[20][6] then chest[20][6] = false
        end
        if chest[21][6] then chest[21][6] = false
        end
        if chest[22][6] then chest[22][6] = false
        end
        if chest[23][6] then chest[23][6] = false
        end
        if chest[24][6] then chest[24][6] = false
        end
        if chest[25][6] then chest[25][6] = false
        end
        if chest[26][6] then chest[26][6] = false
        end
        if chest[27][6] then chest[27][6] = false
        end
        if chest[28][6] then chest[28][6] = false
        end
        if chest[29][6] then chest[29][6] = false
        end
        if chest[30][6] then chest[30][6] = false
        end
        if chest[31][6] then chest[31][6] = false
        end
        if chest[32][6] then chest[32][6] = false
        end
        if chest[33][6] then chest[33][6] = false
        end
        if chest[34][6] then chest[34][6] = false
        end
        if chest[35][6] then chest[35][6] = false
        end
        if chest[36][6] then chest[36][6] = false
        end
        if chest[37][6] then chest[37][6] = false
        end
        if chest[38][6] then chest[38][6] = false
        end
        if chest[39][6] then chest[39][6] = false
        end
    elseif chest[10][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[10][6] = false
    elseif chest[11][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[11][6] = false
    elseif chest[12][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[12][6] = false
    elseif chest[13][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[13][6] = false
    elseif chest[14][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[14][6] = false
    elseif chest[15][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[15][6] = false
    elseif chest[16][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[16][6] = false
    elseif chest[17][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[17][6] = false
    elseif chest[18][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[18][6] = false
    elseif chest[19][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[19][6] = false
    elseif chest[20][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[20][6] = false
    elseif chest[21][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[21][6] = false
    elseif chest[22][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[22][6] = false
    elseif chest[23][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[23][6] = false
    elseif chest[24][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[24][6] = false
    elseif chest[25][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[25][6] = false
    elseif chest[26][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[26][6] = false
    elseif chest[27][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[27][6] = false
    elseif chest[28][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[28][6] = false
    elseif chest[29][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[29][6] = false
    elseif chest[30][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[30][6] = false
    elseif chest[31][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[31][6] = false
    elseif chest[32][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[32][6] = false
    elseif chest[33][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[33][6] = false
    elseif chest[34][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[34][6] = false
    elseif chest[35][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[35][6] = false
    elseif chest[36][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[36][6] = false
    elseif chest[37][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[37][6] = false
    elseif chest[38][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[38][6] = false
    elseif chest[39][6] and text:find('^%[Подсказка%] %{ffffff%}Вы сможете открыть тайник через (.+).') then
        chest[39][6] = false
    end
end

function onReceivePacket(id)
	if id == 31 or id == 32 or id == 33 or id == 35 or id == 36 or id == 37 then
		cfg.settings.connected = false
		inicfg.save(cfg, 'auto_opening_chests.ini')
	elseif id == 34 then
		cfg.settings.connected = true
		inicfg.save(cfg, 'auto_opening_chests.ini')
	end
end

function onQuitGame()
	cfg.settings.connected = false
	inicfg.save(cfg, 'auto_opening_chests.ini')
end

function money_separator(n)
    local left,num,right = string.match(n,'^([^%d]*%d)(%d*)(.-)$')
    return left..(num:reverse():gsub('(%d%d%d)','%1.'):reverse())..right
end

function imgui.CenterText(text)
	local width = imgui.GetWindowWidth()
	local size = imgui.CalcTextSize(text)
	imgui.SetCursorPosX(width/2-size.x/2)
	imgui.Text(text)
end

function imgui.TextColoredRGB(text)
	local style = imgui.GetStyle()
	local colors = style.Colors
	local ImVec4 = imgui.ImVec4
	local explode_argb = function(argb)
		local a = bit.band(bit.rshift(argb, 24), 0xFF)
		local r = bit.band(bit.rshift(argb, 16), 0xFF)
		local g = bit.band(bit.rshift(argb, 8), 0xFF)
		local b = bit.band(argb, 0xFF)
		return a, r, g, b
	end
	local getcolor = function(color)
		if color:sub(1, 6):upper() == 'SSSSSS' then
			local r, g, b = colors[1].x, colors[1].y, colors[1].z
			local a = tonumber(color:sub(7, 8), 16) or colors[1].w * 255
			return ImVec4(r, g, b, a / 255)
		end
		local color = type(color) == 'string' and tonumber(color, 16) or color
		if type(color) ~= 'number' then return end
		local r, g, b, a = explode_argb(color)
		return imgui.ImColor(r, g, b, a):GetVec4()
	end
	local render_text = function(text_)
		for w in text_:gmatch('[^\r\n]+') do
			local text, colors_, m = {}, {}, 1
			w = w:gsub('{(......)}', '{%1FF}')
			while w:find('{........}') do
				local n, k = w:find('{........}')
				local color = getcolor(w:sub(n + 1, k - 1))
				if color then
					text[#text], text[#text + 1] = w:sub(m, n - 1), w:sub(k + 1, #w)
					colors_[#colors_ + 1] = color
					m = n
				end
				w = w:sub(1, n - 1) .. w:sub(k + 1, #w)
			end
			if text[0] then
				for i = 0, #text do
					imgui.TextColored(colors_[i] or colors[1], u8(text[i]))
					imgui.SameLine(nil, 0)
				end
				imgui.NewLine()
			else imgui.Text(u8(w)) end
		end
	end
	render_text(text)
end

function imgui.Link(label, description)
	local width = imgui.GetWindowWidth()
	local size = imgui.CalcTextSize(label)
	local p = imgui.GetCursorScreenPos()
	local p2 = imgui.GetCursorPos()
	local result = imgui.InvisibleButton(label, imgui.ImVec2(width-16, size.y))
	imgui.SetCursorPos(p2)
	imgui.SetCursorPosX(width/2-size.x/2)
	if imgui.IsItemHovered() then
		if description then
			imgui.BeginTooltip()
			imgui.PushTextWrapPos(500)
			imgui.TextUnformatted(description)
			imgui.PopTextWrapPos()
			imgui.EndTooltip()
		end
		imgui.TextColored(imgui.GetStyle().Colors[imgui.Col.CheckMark], label)
		imgui.GetWindowDrawList():AddLine(imgui.ImVec2(width/2-size.x/2+p.x-8, p.y + size.y), imgui.ImVec2(width/2-size.x/2+p.x-8 + size.x, p.y + size.y), imgui.GetColorU32(imgui.GetStyle().Colors[imgui.Col.CheckMark]))
	else
		imgui.TextColored(imgui.GetStyle().Colors[imgui.Col.CheckMark], label)
	end
	return result
end

function theme()
	imgui.SwitchContext()
	local style = imgui.GetStyle()
	local colors = style.Colors
	local clr = imgui.Col
	local ImVec4 = imgui.ImVec4
	local ImVec2 = imgui.ImVec2

	style.WindowPadding = ImVec2(8, 8)
	style.WindowRounding = 5.0
	style.ChildWindowRounding = 5.0
	style.FramePadding = ImVec2(2, 2)
	style.FrameRounding = 5.0
	style.ItemSpacing = ImVec2(5, 5)
	style.ItemInnerSpacing = ImVec2(5, 5)
	style.TouchExtraPadding = ImVec2(0, 0)
	style.IndentSpacing = 5.0
	style.ScrollbarSize = 15.0
	style.ScrollbarRounding = 5.0
	style.GrabMinSize = 20.0
	style.GrabRounding = 5.0
	style.WindowTitleAlign = ImVec2(0.5, 0.5)

	colors[clr.Text]                    = ImVec4(1.00, 1.00, 1.00, 1.00)
	colors[clr.TextDisabled]            = ImVec4(0.20, 0.20, 0.20, 1.00)
	colors[clr.WindowBg]                = ImVec4(0.05, 0.05, 0.05, 1.00)
	colors[clr.ChildWindowBg]           = ImVec4(0.05, 0.05, 0.05, 1.00)
	colors[clr.PopupBg]                 = ImVec4(0.05, 0.05, 0.05, 1.00)
	colors[clr.Border]                  = ImVec4(1.00, 1.00, 1.00, 1.00)
	colors[clr.BorderShadow]            = ImVec4(0.05, 0.05, 0.05, 1.00)
	colors[clr.FrameBg]                 = ImVec4(0.13, 0.13, 0.13, 1.00)
	colors[clr.FrameBgHovered]          = ImVec4(0.20, 0.20, 0.20, 1.00)
	colors[clr.FrameBgActive]           = ImVec4(0.13, 0.13, 0.13, 1.00)
	colors[clr.TitleBg]                 = ImVec4(0.13, 0.13, 0.13, 1.00)
	colors[clr.TitleBgCollapsed]        = ImVec4(0.13, 0.13, 0.13, 1.00)
	colors[clr.TitleBgActive]           = ImVec4(0.13, 0.13, 0.13, 1.00)
	colors[clr.MenuBarBg]               = ImVec4(0.13, 0.13, 0.13, 1.00)
	colors[clr.ScrollbarBg]             = ImVec4(0.05, 0.05, 0.05, 1.00)
	colors[clr.ScrollbarGrab]           = ImVec4(0.13, 0.13, 0.13, 1.00)
	colors[clr.ScrollbarGrabHovered]    = ImVec4(0.20, 0.20, 0.20, 1.00)
	colors[clr.ScrollbarGrabActive]     = ImVec4(0.13, 0.13, 0.13, 1.00)
	colors[clr.ComboBg]                 = ImVec4(0.13, 0.13, 0.13, 1.00)
	colors[clr.CheckMark]               = ImVec4(1.00, 1.00, 1.00, 1.00)
	colors[clr.SliderGrab]              = ImVec4(1.00, 1.00, 1.00, 1.00)
	colors[clr.SliderGrabActive]        = ImVec4(1.00, 1.00, 1.00, 1.00)
	colors[clr.Button]                  = ImVec4(0.13, 0.13, 0.13, 1.00)
	colors[clr.ButtonHovered]           = ImVec4(0.20, 0.20, 0.20, 1.00)
	colors[clr.ButtonActive]            = ImVec4(0.13, 0.13, 0.13, 1.00)
	colors[clr.Header]                  = ImVec4(0.13, 0.13, 0.13, 1.00)
	colors[clr.HeaderHovered]           = ImVec4(0.20, 0.20, 0.20, 1.00)
	colors[clr.HeaderActive]            = ImVec4(0.13, 0.13, 0.13, 1.00)
	colors[clr.ResizeGrip]              = ImVec4(0.13, 0.13, 0.13, 1.00)
	colors[clr.ResizeGripHovered]       = ImVec4(0.20, 0.20, 0.20, 1.00)
	colors[clr.ResizeGripActive]        = ImVec4(0.13, 0.13, 0.13, 1.00)
	colors[clr.CloseButton]             = ImVec4(0.05, 0.05, 0.05, 1.00)
	colors[clr.CloseButtonHovered]      = ImVec4(0.05, 0.05, 0.05, 1.00)
	colors[clr.CloseButtonActive]       = ImVec4(0.05, 0.05, 0.05, 1.00)
	colors[clr.PlotLines]               = ImVec4(0.13, 0.13, 0.13, 1.00)
	colors[clr.PlotLinesHovered]        = ImVec4(0.20, 0.20, 0.20, 1.00)
	colors[clr.PlotHistogram]           = ImVec4(0.13, 0.13, 0.13, 1.00)
	colors[clr.PlotHistogramHovered]    = ImVec4(0.20, 0.20, 0.20, 1.00)
	colors[clr.TextSelectedBg]          = ImVec4(0.05, 0.05, 0.05, 1.00)
	colors[clr.ModalWindowDarkening]    = ImVec4(0.13, 0.13, 0.13, 0.00)
end
theme()