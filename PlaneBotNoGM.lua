local samp = require("samp.events")
local ffi = require("ffi")
local memory = require("memory")
local effil = require("effil")
local ini = require("inicfg")
local encoding = require("encoding")

local bot_state = false
local rep = false
local counter = 0
local bot_mode = 0
encoding.default = 'CP1251'
u8 = encoding.UTF8

local currentList = 0

local Routes = {
    LSLV = {},
    LSSF = {},
    LVLS = {},
    LVSF = {},
    SFLS = {},
    SFLV = {},
    ToExit = {},
    ToAeroLS = {},
    ToAeroSF = {},
    ToAeroLV = {},
    ToPlaneCH = {}
}

local cfg = ini.load({
    settings = {
        chat_id = 0,
        token = "token"
    }
}, "plane.ini")

local CurrentRoute = {}

local Dest = nil

function main()
    if isSampLoaded() and isSampfuncsLoaded() then
        while not isSampAvailable() or not isPlayerPlaying(PLAYER_HANDLE) do
			wait(0)
		end

        local result = sampRegisterChatCommand("pbot", function() 
            bot_state = not bot_state
            sampAddChatMessage(string.format("[Plane Bot] {FFFFFF}%s", bot_state and "Активирован." or "Деактивирован."), 0xEFDECD)
            if not bot_state then 
                bot_mode = 0 
                rep = false
                CurrentRoute = {}
            end
        end)

        if not result then
            script.this:unload()
        else
            local conf = ini.load(nil, "plane.ini")
            ini.save(cfg, "plane.ini")
            sendTelegramNotification("Скрипт был загружен в игру!")
            sampAddChatMessage("[Plane Bot] {FFFFFF}Загружен.", 0xEFDECD)
            -- allocate bitstream class for sync

            sampAddChatMessage("[Plane Bot] {FFFFFF} Идет загрузка маршрутов... Игра может зависнуть на пару секунд.", 0xEFDECD)

            Routes.LSLV = LoadRoute(getWorkingDirectory() .. "/plane_route/lslv_1.rt")
            Routes.LSSF = LoadRoute(getWorkingDirectory() .. "/plane_route/lssf_1.rt")

            Routes.LVLS = LoadRoute(getWorkingDirectory() .. "/plane_route/lvls_1.rt")
            Routes.LVSF = LoadRoute(getWorkingDirectory() .. "/plane_route/lvsf_1.rt")

            Routes.SFLS = LoadRoute(getWorkingDirectory() .. "/plane_route/sfls_1.rt")
            Routes.SFLV = LoadRoute(getWorkingDirectory() .. "/plane_route/sflv_1.rt")

            Routes.ToExit = LoadRoute(getWorkingDirectory() .. "/plane_route/to_exit_1.rt")

            Routes.ToAeroLS = LoadRoute(getWorkingDirectory() .. "/plane_route/to_aero_ls_1.rt")
            Routes.ToAeroSF = LoadRoute(getWorkingDirectory() .. "/plane_route/to_aero_sf_1.rt")
            Routes.ToAeroLV = LoadRoute(getWorkingDirectory() .. "/plane_route/to_aero_lv_1.rt")

            Routes.ToPlaneCH = LoadRoute(getWorkingDirectory() .. "/plane_route/to_plane_ch_1.rt")
        end
    else
        script.this:unload()
    end

    while true do
        wait(60)
        if bot_state then
            if bot_mode == 0 then
                local data = samp_create_sync_data('player')
                data.keysData = 1024
                data.send()
                wait(150)
            end
        end

        if rep then
            counter = counter + 1

            if bot_mode == 2 or bot_mode == 5 or bot_mode == 7 then
                local data = samp_create_sync_data('player')
                data.leftRightKeys = CurrentRoute[counter].lr
                data.upDownKeys = CurrentRoute[counter].ud
                data.keysData = CurrentRoute[counter].keys
                data.position = { CurrentRoute[counter].x, CurrentRoute[counter].y, CurrentRoute[counter].z }
                data.quaternion[0] = CurrentRoute[counter].qw
                data.quaternion[1] = CurrentRoute[counter].qx
                data.quaternion[2] = CurrentRoute[counter].qy
                data.quaternion[3] = CurrentRoute[counter].qz
                -- data.health = getCharHealth(PLAYER_PED)
                -- data.armor = getCharArmour(PLAYER_PED)
                data.specialAction = CurrentRoute[counter].sa
                data.moveSpeed = { CurrentRoute[counter].sx, CurrentRoute[counter].sy, CurrentRoute[counter].sz }
                data.animationId = CurrentRoute[counter].anim
                data.animationFlags = CurrentRoute[counter].flags
                data.send()

                setCharCoordinatesNoOffset(PLAYER_PED, CurrentRoute[counter].x, CurrentRoute[counter].y, CurrentRoute[counter].z)
                setCharQuaternion(PLAYER_PED, -CurrentRoute[counter].qx, -CurrentRoute[counter].qy, -CurrentRoute[counter].qz, CurrentRoute[counter].qw)

                if counter == #CurrentRoute then
                    rep = false
                    setCharCoordinatesNoOffset(PLAYER_PED, CurrentRoute[counter].x, CurrentRoute[counter].y, CurrentRoute[counter].z)
                    setCharQuaternion(PLAYER_PED, -CurrentRoute[counter].qx, -CurrentRoute[counter].qy, -CurrentRoute[counter].qz, CurrentRoute[counter].qw)
                    CurrentRoute = {}
                    counter = 1
                    if bot_mode == 5 then
                        if Dest == "'Сан Фиерро' -> 'Лос Сантос'" or Dest == "'Лас Вентурас' -> 'Лос Сантос'" then
                            setCharCoordinatesNoOffset(PLAYER_PED, 1892.5109, -2328.2786, 13.5469) --  костыль нахуй
                        elseif Dest == "'Сан Фиерро' -> 'Лас Вентурас'" or Dest == "'Лос Сантос' -> 'Лас Вентурас'" then
                            setCharCoordinatesNoOffset(PLAYER_PED, 1598.2915, 1446.1893, 10.8281)
                        elseif Dest == "'Лос Сантос' -> 'Сан Фиерро'" or Dest == "'Лас Вентурас' -> 'Сан Фиерро'" then
                            setCharCoordinatesNoOffset(PLAYER_PED, -1383.2415, -255.5413, 14.1440)
                        end
                    end
                    if bot_mode == 7 then
                        bot_mode = 0
                        sampAddChatMessage("[Plane Bot] {FFFFFF}Круг успешно пройден! Начинаем по новой...", 0xEFDECD)
                    else
                        bot_mode = bot_mode + 1 -- for 3 and 6 bot mode
                    end
                end
            elseif bot_mode == 4 then
                local result, vehId = sampGetVehicleIdByCarHandle(storeCarCharIsInNoSave(PLAYER_PED))
                if result then
                    local data = samp_create_sync_data('vehicle')

                    data.vehicleId = vehId
                    data.leftRightKeys = CurrentRoute[counter].lr
                    data.upDownKeys = CurrentRoute[counter].ud
                    data.keysData = CurrentRoute[counter].keys

                    data.quaternion[0] = CurrentRoute[counter].qw
                    data.quaternion[1] = CurrentRoute[counter].qx
                    data.quaternion[2] = CurrentRoute[counter].qy
                    data.quaternion[3] = CurrentRoute[counter].qz

                    data.position = { CurrentRoute[counter].x, CurrentRoute[counter].y, CurrentRoute[counter].z }
                    data.moveSpeed = { CurrentRoute[counter].sx, CurrentRoute[counter].sy, CurrentRoute[counter].sz }

                    -- data.vehicleHealth = getCarHealth(storeCarCharIsInNoSave(PLAYER_PED))
                    -- data.playerHealth = getCharHealth(PLAYER_PED)
                    data.armor = getCharArmour(PLAYER_PED)
                    data.landingGearState = CurrentRoute[counter].gear

                    data.send() -- send vehicle sync data

                    setCarCoordinatesNoOffset(storeCarCharIsInNoSave(PLAYER_PED), CurrentRoute[counter].x, CurrentRoute[counter].y, CurrentRoute[counter].z)
                    -- setCarProofs(storeCarCharIsInNoSave(PLAYER_PED), true, true, true, true, true)

                    -- local objectsTable = getAllObjects()
                    -- local vehiclesTable = getAllVehicles()

                    -- for k, v in pairs(objectsTable) do
                    --     setObjectCollision(v, false)
                    -- end

                    -- for k, l in pairs(vehiclesTable) do
                    --     if l ~= storeCarCharIsInNoSave(PLAYER_PED) then
                    --         setCarCollision(l, false)
                    --     end
                    -- end

                    if counter == #CurrentRoute then
                        rep = false
                        setCarCoordinates(storeCarCharIsInNoSave(PLAYER_PED), CurrentRoute[counter].x, CurrentRoute[counter].y, CurrentRoute[counter].z)
                        setVehicleQuaternion(storeCarCharIsInNoSave(PLAYER_PED), -CurrentRoute[counter].qx, -CurrentRoute[counter].qy, -CurrentRoute[counter].qz, CurrentRoute[counter].qw)
                        sampSendExitVehicle(vehId)
                        taskLeaveCar(PLAYER_PED, storeCarCharIsInNoSave(PLAYER_PED))
                        sampAddChatMessage("[Plane Bot] {FFFFFF} Рейс был окончен. Жду 3 секунды пока персонаж выйдет из самолета.", 0xEFDECD)
                        wait(3000)
                        CurrentRoute = {}
                        counter = 1
                        bot_mode = 5
                        if Dest == "'Сан Фиерро' -> 'Лос Сантос'" or Dest == "'Лас Вентурас' -> 'Лос Сантос'" then
                            RunRoute(Routes.ToAeroLS)
                        elseif Dest == "'Сан Фиерро' -> 'Лас Вентурас'" or Dest == "'Лос Сантос' -> 'Лас Вентурас'" then
                            RunRoute(Routes.ToAeroLV)
                        elseif Dest == "'Лос Сантос' -> 'Сан Фиерро'" or Dest == "'Лас Вентурас' -> 'Сан Фиерро'" then
                            RunRoute(Routes.ToAeroSF)
                        end
                    end
                end
            end
            printStringNow("PACKETS: ~g~" .. counter, 1000)
        end
    end
end

function samp.onShowDialog(dialogId, style, title, button1, button2, text)
    if bot_state then
        if bot_mode == 0 then
            if title:find("Выберите самолет") then
                currentList = 0
                for str in text:gmatch("[^\n]+") do
                    if str:find("Частный самолет") then
                        sampSendDialogResponse(dialogId, 1, currentList - 1, "")
                        sampAddChatMessage("[Plane Bot] {FFFFFF}Выбрал частный самолет. Жду от сервера пункт назначения.", 0xEFDECD)
                        bot_mode = 1
                        break
                    end
                    currentList = currentList + 1
                end
                return false
            end
        end
        if text:find('Администратор ') and text:find('ответил вам:') then
            lua_thread.create(function()
                wait(2000)
                sampSendDialogResponse(dialogId, 1, -1, "")
                sendTelegramNotification("[DIALOG] " .. text)
                sampAddChatMessage("[Plane Bot] {FFFFFF}Диалог был автоматически закрыт! Содержимое диалога отправлено в телеграм.", 0xEFDECD)
            end)
            return false
        end
    end
end

function samp.onServerMessage(color, text)
    if bot_state then
        if text:find('Администратор ') and text:find('ответил вам:') then
            sendTelegramNotification(text)
        elseif text:find("Вы были телепортированы администратором") then
            bot_state = false
            bot_mode = 0
            rep = false
            CurrentRoute = {}
            sendTelegramNotification("Вы были телепортированы администратором. Срочно разверните игру! Бот выключен.")
        elseif text:find("%(%( Администратор") or text:find("говорит:") then
            sendTelegramNotification(text)
        elseif text:find("%(%( Через 30 секунд вы сможете") then
            sendTelegramNotification("Бот умер!")
            bot_state = false
            bot_mode = 0 
            rep = false
            CurrentRoute = {}
        end
    end
    if bot_state and bot_mode == 1 then
        if color == 1724710911 and text:find("Сотрудник Бюро") then
            text = string.gsub(text, "%{......%}", "")
            Dest = text:match("%[(.*)%]")
            bot_mode = 2
            RunRoute(Routes.ToExit)
        end
    end
end

function samp.onSetInterior(interior)
    if bot_state then
        if interior ~= 139 and interior ~= 0 then
            sendTelegramNotification("Администратор сменил вам интерьер.")
            bot_state = false
            bot_mode = 0 
            rep = false
            CurrentRoute = {}
        end
    end
end

function samp.onPutPlayerInVehicle(vehicleId, seatId)
    if bot_state and bot_mode ~= 3 then
        sendTelegramNotification("Администратор выдал вам машину. Скрипт отключен!")
        bot_state = false
        bot_mode = 0 
        rep = false
        CurrentRoute = {}
    end
    if bot_state and bot_mode == 3 then
lua_thread.create(function()
            wait(150)
        if Dest == "'Сан Фиерро' -> 'Лос Сантос'" then
            RunRoute(Routes.SFLS)
        elseif Dest == "'Сан Фиерро' -> 'Лас Вентурас'" then
            RunRoute(Routes.SFLV)
        elseif Dest == "'Лос Сантос' -> 'Лас Вентурас'" then
            RunRoute(Routes.LSLV)
        elseif Dest == "'Лос Сантос' -> 'Сан Фиерро'" then
            RunRoute(Routes.LSSF)
        elseif Dest == "'Лас Вентурас' -> 'Сан Фиерро'" then
            RunRoute(Routes.LVSF)
        elseif Dest == "'Лас Вентурас' -> 'Лос Сантос'" then
            RunRoute(Routes.LVLS)
        end
        bot_mode = 4
end)
    end
end

function samp.onSendPlayerSync(data)
    if rep then
        return false
    end
end

function samp.onConnectionClosed()
    if bot_state then
        sendTelegramNotification("Server closed the connection.")
    end
end

function samp.onConnectionLost()
    if bot_state then
        sendTelegramNotification("Lost connection to the server.")
    end
end

function samp.onSendVehicleSync(data)
    if rep then
        return false
    end
end

function RunRoute(routePointer)
    CurrentRoute = {}
    counter = 1
	rep = true

    CurrentRoute = routePointer

    sampAddChatMessage("[Plane Bot] {FFFFFF} Запускаю маршрут. Количество пакетов: {00FF00}" .. #CurrentRoute, 0xEFDECD)
end

function StopRoute()
    if counter > 1 then rep = not rep end
end

function LoadRoute(fileName)
    local file = io.open(fileName, 'r')
    if file then
		local data = {}
		local section
		for line in file:lines() do
			local tempSection = line:match('^%[([^%[%]]+)%]$')
			if tempSection then
				section = tonumber(tempSection) and tonumber(tempSection) or tempSection
				data[section] = data[section] or {}
			end
			local param, value = line:match('^([%w|_]+)%s-=%s-(.+)$')
			if param and value ~= nil then
				if tonumber(value) then
					value = tonumber(value)
				elseif value == 'true' then
					value = true
				elseif value == 'false' then
					value = false
				end
				if tonumber(param) then
					param = tonumber(param)
				end
				data[section][param] = value
			end
		end
		file:close()
		return data
	end
    sampAddChatMessage("[Plane Bot] {FF0000} Ошибка загрузки " .. fileName, 0xEFDECD)
    sampAddChatMessage(" ", 0xEFDECD)
    return false
end

function setVehicleMoveSpeed(handle, x, y, z)
    local ptr = getCarPointer(handle)
    if ptr ~= 0 then
        ffi.cast("void (__thiscall *)(uint32_t, float, float, float)", 0x441130)(ptr, x, y, z)
    end
end

function threadHandle(runner, url, args, resolve, reject)
    local t = runner(url, args)
    local r = t:get(0)
    while not r do
        r = t:get(0)
        wait(0)
    end
    local status = t:status()
    if status == 'completed' then
        local ok, result = r[1], r[2]
        if ok then resolve(result) else reject(result) end
    elseif err then
        reject(err)
    elseif status == 'canceled' then
        reject(status)
    end
    t:cancel(0)
end

function requestRunner()
    return effil.thread(function(u, a)
        local https = require 'ssl.https'
        local ok, result = pcall(https.request, u, a)
        if ok then
            return {true, result}
        else
            return {false, result}
        end
    end)
end

function async_http_request(url, args, resolve, reject)
    local runner = requestRunner()
    if not reject then reject = function() end end
    lua_thread.create(function()
        threadHandle(runner, url, args, resolve, reject)
    end)
end

function encodeUrl(str)
    str = str:gsub(' ', '%+')
    str = str:gsub('\n', '%%0A')
    return u8:encode(str, 'CP1251')
end

function sendTelegramNotification(msg) -- from Telegram Control by Vespan
    msg = os.date('[%H:%M:%S]') .. msg 
    msg = msg:gsub('{......}', '')
    msg = encodeUrl(msg)
    async_http_request('https://api.telegram.org/bot' .. cfg.settings.token .. '/sendMessage?chat_id=' .. cfg.settings.chat_id .. '&text='..msg,'', function(result) end)
end

function samp_create_sync_data(sync_type, copy_from_player)
    local ffi = require 'ffi'
    local sampfuncs = require 'sampfuncs'
    -- from SAMP.Lua
    local raknet = require 'samp.raknet'
    require 'samp.synchronization'

    copy_from_player = copy_from_player or true
    local sync_traits = {
        player = {'PlayerSyncData', raknet.PACKET.PLAYER_SYNC, sampStorePlayerOnfootData},
        vehicle = {'VehicleSyncData', raknet.PACKET.VEHICLE_SYNC, sampStorePlayerIncarData},
        passenger = {'PassengerSyncData', raknet.PACKET.PASSENGER_SYNC, sampStorePlayerPassengerData},
        aim = {'AimSyncData', raknet.PACKET.AIM_SYNC, sampStorePlayerAimData},
        trailer = {'TrailerSyncData', raknet.PACKET.TRAILER_SYNC, sampStorePlayerTrailerData},
        unoccupied = {'UnoccupiedSyncData', raknet.PACKET.UNOCCUPIED_SYNC, nil},
        bullet = {'BulletSyncData', raknet.PACKET.BULLET_SYNC, nil},
        spectator = {'SpectatorSyncData', raknet.PACKET.SPECTATOR_SYNC, nil}
    }
    local sync_info = sync_traits[sync_type]
    local data_type = 'struct ' .. sync_info[1]
    local data = ffi.new(data_type, {})
    local raw_data_ptr = tonumber(ffi.cast('uintptr_t', ffi.new(data_type .. '*', data)))
    -- copy player's sync data to the allocated memory
    if copy_from_player then
        local copy_func = sync_info[3]
        if copy_func then
            local _, player_id
            if copy_from_player == true then
                _, player_id = sampGetPlayerIdByCharHandle(PLAYER_PED)
            else
                player_id = tonumber(copy_from_player)
            end
            copy_func(player_id, raw_data_ptr)
        end
    end
    -- function to send packet
    local func_send = function()
        local bs = raknetNewBitStream()
        raknetBitStreamWriteInt8(bs, sync_info[2])
        raknetBitStreamWriteBuffer(bs, raw_data_ptr, ffi.sizeof(data))
        raknetSendBitStreamEx(bs, sampfuncs.HIGH_PRIORITY, sampfuncs.UNRELIABLE_SEQUENCED, 1)
        raknetDeleteBitStream(bs)
    end
    -- metatable to access sync data and 'send' function
    local mt = {
        __index = function(t, index)
            return data[index]
        end,
        __newindex = function(t, index, value)
            data[index] = value
        end
    }
    return setmetatable({send = func_send}, mt)
end

function samp.onSetPlayerPos(position)
    if bot_state then
        local x, y, z = getCharCoordinates(PLAYER_PED)
        if position.x == x and position.y == y and position.z ~= z then
            sendTelegramNotification("Администратор дал вам поджопник. Скрипт отключен.")
            bot_state = false
            bot_mode = 0 
            rep = false
            CurrentRoute = {}
        end
    end
    if math.ceil(position.x) == 1520 and math.ceil(position.y) == 1326 and math.ceil(position.z) == 11 and bot_mode == 6 then
        RunRoute(Routes.ToPlaneCH)
        bot_mode = 7
    end
end