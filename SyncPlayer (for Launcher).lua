local sampev = require 'lib.samp.events'
local imgui = require 'imgui'
local encoding = require 'encoding'
encoding.default = 'CP1251' 
u8 = encoding.UTF8

local myfile = getWorkingDirectory().."//config//routes.json"
local w,h = getScreenResolution()
local check_Box = imgui.ImBool(true)
local check_Box2 = imgui.ImBool(false)
local state = imgui.ImBool(false)
local wait_ = imgui.ImInt(50)
local radioButton = imgui.ImInt(0)
local record,play,pause = false,false,false
local textBuffer = imgui.ImBuffer('', 256)
local table_ = {}
local timeTable_ = {}

imgui.SwitchContext()
local style = imgui.GetStyle()
local colors = style.Colors
local clr = imgui.Col
local ImVec4 = imgui.ImVec4
style.WindowRounding = 2.0
style.WindowTitleAlign = imgui.ImVec2(0.5, 0.84)
style.ChildWindowRounding = 2.0
style.FrameRounding = 2.0
style.ItemSpacing = imgui.ImVec2(5.0, 4.0)
style.ScrollbarSize = 13.0
style.ScrollbarRounding = 0
style.GrabMinSize = 8.0
style.GrabRounding = 1.0
colors[clr.FrameBg]                = ImVec4(0.16, 0.29, 0.48, 0.54)
colors[clr.FrameBgHovered]         = ImVec4(0.26, 0.59, 0.98, 0.40)
colors[clr.FrameBgActive]          = ImVec4(0.26, 0.59, 0.98, 0.67)
colors[clr.TitleBg]                = ImVec4(0.04, 0.04, 0.04, 1.00)
colors[clr.TitleBgActive]          = ImVec4(0.16, 0.29, 0.48, 1.00)
colors[clr.TitleBgCollapsed]       = ImVec4(0.00, 0.00, 0.00, 0.51)
colors[clr.CheckMark]              = ImVec4(0.26, 0.59, 0.98, 1.00)
colors[clr.SliderGrab]             = ImVec4(0.24, 0.52, 0.88, 1.00)
colors[clr.SliderGrabActive]       = ImVec4(0.26, 0.59, 0.98, 1.00)
colors[clr.Button]                 = ImVec4(0.26, 0.59, 0.98, 0.40)
colors[clr.ButtonHovered]          = ImVec4(0.26, 0.59, 0.98, 1.00)
colors[clr.ButtonActive]           = ImVec4(0.06, 0.53, 0.98, 1.00)
colors[clr.Header]                 = ImVec4(0.26, 0.59, 0.98, 0.31)
colors[clr.HeaderHovered]          = ImVec4(0.26, 0.59, 0.98, 0.80)
colors[clr.HeaderActive]           = ImVec4(0.26, 0.59, 0.98, 1.00)
colors[clr.Separator]              = colors[clr.Border]
colors[clr.SeparatorHovered]       = ImVec4(0.26, 0.59, 0.98, 0.78)
colors[clr.SeparatorActive]        = ImVec4(0.26, 0.59, 0.98, 1.00)
colors[clr.ResizeGrip]             = ImVec4(0.26, 0.59, 0.98, 0.25)
colors[clr.ResizeGripHovered]      = ImVec4(0.26, 0.59, 0.98, 0.67)
colors[clr.ResizeGripActive]       = ImVec4(0.26, 0.59, 0.98, 0.95)
colors[clr.TextSelectedBg]         = ImVec4(0.26, 0.59, 0.98, 0.35)
colors[clr.Text]                   = ImVec4(1.00, 1.00, 1.00, 1.00)
colors[clr.TextDisabled]           = ImVec4(0.50, 0.50, 0.50, 1.00)
colors[clr.WindowBg]               = ImVec4(0.06, 0.06, 0.06, 0.94)
colors[clr.ChildWindowBg]          = ImVec4(1.00, 1.00, 1.00, 0.00)
colors[clr.PopupBg]                = ImVec4(0.08, 0.08, 0.08, 0.94)
colors[clr.ComboBg]                = colors[clr.PopupBg]
colors[clr.Border]                 = ImVec4(0.43, 0.43, 0.50, 0.50)
colors[clr.BorderShadow]           = ImVec4(0.00, 0.00, 0.00, 0.00)
colors[clr.MenuBarBg]              = ImVec4(0.14, 0.14, 0.14, 1.00)
colors[clr.ScrollbarBg]            = ImVec4(0.02, 0.02, 0.02, 0.53)
colors[clr.ScrollbarGrab]          = ImVec4(0.31, 0.31, 0.31, 1.00)
colors[clr.ScrollbarGrabHovered]   = ImVec4(0.41, 0.41, 0.41, 1.00)
colors[clr.ScrollbarGrabActive]    = ImVec4(0.51, 0.51, 0.51, 1.00)
colors[clr.CloseButton]            = ImVec4(0.41, 0.41, 0.41, 0.50)
colors[clr.CloseButtonHovered]     = ImVec4(0.98, 0.39, 0.36, 1.00)
colors[clr.CloseButtonActive]      = ImVec4(0.98, 0.39, 0.36, 1.00)
colors[clr.PlotLines]              = ImVec4(0.61, 0.61, 0.61, 1.00)
colors[clr.PlotLinesHovered]       = ImVec4(1.00, 0.43, 0.35, 1.00)
colors[clr.PlotHistogram]          = ImVec4(0.90, 0.70, 0.00, 1.00)
colors[clr.PlotHistogramHovered]   = ImVec4(1.00, 0.60, 0.00, 1.00)
colors[clr.ModalWindowDarkening]   = ImVec4(0.80, 0.80, 0.80, 0.35)

function tableCopy(t)
	local t2 = {}
	for k,v in pairs(t) do
		t2[k] = v
	end
	return t2
end

function checkDist(x1, y1, z1)
	local x, y, z = getCharCoordinates(PLAYER_PED)
	if getDistanceBetweenCoords3d(x, y, z, x1, y1, z1) <= 20 then
		return true
	end
	return false, math.floor(getDistanceBetweenCoords3d(x, y, z, x1, y1, z1))
end

function freeze(bool)
	pause = bool
	if not isCharInAnyCar(PLAYER_PED) then
		freezeCharPosition(PLAYER_PED, bool)
	else
		freezeCarPosition(storeCarCharIsInNoSave(PLAYER_PED), bool)
	end
end

function showRoute(item)
	while #item ~= 0 and play do wait(0)
		for i=1, #item do
			if item[i+1] ~= nil and isPointOnScreen(item[i].position.x, item[i].position.y,item[i].position.z, 0) and isPointOnScreen(item[i+1].position.x, item[i+1].position.y,item[i+1].position.z, 0) then
				local x,y = convert3DCoordsToScreen(item[i].position.x, item[i].position.y,item[i].position.z)
				local x1,y1 = convert3DCoordsToScreen(item[i+1].position.x, item[i+1].position.y,item[i+1].position.z)
				renderDrawLine(x,y,x1,y1,3,0xFF10BEF1)
			end
		end
	end
end

function playRoute()
	table.remove(timeTable_, 1)
	play = true
	if isCharInAnyCar(PLAYER_PED) and getDriverOfCar(storeCarCharIsInNoSave(PLAYER_PED)) == PLAYER_PED then
		vHealth = getCarHealth(storeCarCharIsInNoSave(PLAYER_PED))
	end
	printStyledString('~y~route played',2000,4)
	while #timeTable_ ~= 0 do wait(wait_.v)
		if not pause then
			if timeTable_[1].mode == 'onFoot' then
				local sync = samp_create_sync_data('player')
				sync.leftRightKeys = timeTable_[1].leftRightKeys
				sync.upDownKeys = timeTable_[1].upDownKeys
				sync.keysData = timeTable_[1].keysData
				sync.position = {timeTable_[1].position.x, timeTable_[1].position.y, timeTable_[1].position.z}
				sync.quaternion = {timeTable_[1].quaternion.w, timeTable_[1].quaternion.x, timeTable_[1].quaternion.y, timeTable_[1].quaternion.z}  
				sync.moveSpeed = {timeTable_[1].moveSpeed.x, timeTable_[1].moveSpeed.y, timeTable_[1].moveSpeed.z}
				sync.animationId = timeTable_[1].animationId
				sync.animationFlags = timeTable_[1].animationFlags
				sync.send()
				setCharCoordinates(PLAYER_PED, timeTable_[1].position.x, timeTable_[1].position.y, timeTable_[1].position.z)
				setCharQuaternion(PLAYER_PED, timeTable_[1].quaternionFix.x, timeTable_[1].quaternionFix.y, timeTable_[1].quaternionFix.z, timeTable_[1].quaternionFix.w)
			elseif timeTable_[1].mode == 'onVeh' and isCharInAnyCar(PLAYER_PED) and getDriverOfCar(storeCarCharIsInNoSave(PLAYER_PED)) == PLAYER_PED then
				local vHandle = storeCarCharIsInNoSave(PLAYER_PED)
				setCarCoordinates(vHandle, timeTable_[1].position.x, timeTable_[1].position.y, timeTable_[1].position.z)
				setVehicleQuaternion(vHandle, timeTable_[1].quaternionFix.x, timeTable_[1].quaternionFix.y, timeTable_[1].quaternionFix.z, timeTable_[1].quaternionFix.w)
				local sync = samp_create_sync_data('vehicle')
				sync.leftRightKeys = timeTable_[1].leftRightKeys
				sync.upDownKeys = timeTable_[1].upDownKeys
				sync.keysData = timeTable_[1].keysData
				sync.position = {timeTable_[1].position.x, timeTable_[1].position.y, timeTable_[1].position.z}
				sync.quaternion = {timeTable_[1].quaternion.w, timeTable_[1].quaternion.x, timeTable_[1].quaternion.y, timeTable_[1].quaternion.z}  
				sync.moveSpeed = {timeTable_[1].moveSpeed.x, timeTable_[1].moveSpeed.y, timeTable_[1].moveSpeed.z}
				if check_Box2.v then
					setCarHealth(vHandle, vHealth)
					sync.vehicleHealth = vHealth
				end
				sync.send()
			end
			table.remove(timeTable_, 1)
		end
	end
	play = false
	printStyledString('~y~route ended',2000,4)
end

function saveConfig()
	local file = io.open(myfile, "w")
	file:write(encodeJson(table_))
	file:close()
end

function main()
    while not isSampAvailable() do wait(0) end
	if not doesFileExist(myfile) then
		createDirectory(getWorkingDirectory()..'\\config')
		local file = io.open(myfile, "w") file:close()
	else
		local file = io.open(myfile, "r")
		local fText = file:read()
		if fText ~= nil then
			table_ = decodeJson(fText)
		end
		file:close()
	end
	
	sampRegisterChatCommand('record', function()
		if not record and not play and not sampIsDialogActive() then
			timeTable_ = {}
			record = true
			printStyledString('~g~record started',2000,4)
		elseif record then
			record = false
			if #timeTable_ ~= 0 then
				table.insert(timeTable_, 1, {name = 'route '..#table_})
				table.insert(table_, timeTable_)
				saveConfig()
				printStyledString('~r~record stopped~n~~y~route saved',2000,4)
			else
				printStyledString('~r~record not saved~n~not enough packets',2000,4)
			end
		end
	end)
	
	while true do wait(0)
		imgui.Process = state.v
		if play then
			for i=1, #timeTable_ do
				if timeTable_[i+1] ~= nil and isPointOnScreen(timeTable_[i].position.x, timeTable_[i].position.y,timeTable_[i].position.z, 0) and isPointOnScreen(timeTable_[i+1].position.x, timeTable_[i+1].position.y,timeTable_[i+1].position.z, 0) then
					local x,y = convert3DCoordsToScreen(timeTable_[i].position.x, timeTable_[i].position.y,timeTable_[i].position.z)
					local x1,y1 = convert3DCoordsToScreen(timeTable_[i+1].position.x, timeTable_[i+1].position.y,timeTable_[i+1].position.z)
					renderDrawLine(x,y,x1,y1,3,0xFF10BEF1)
				end
			end
		end
		if testCheat('pp') then
            state.v = not state.v
        end
	end
end

function imgui.TextQuestion(text)
	imgui.TextDisabled('(?)')
	if imgui.IsItemHovered() then
		imgui.BeginTooltip()
		imgui.PushTextWrapPos(450)
		imgui.TextUnformatted(text)
		imgui.PopTextWrapPos()
		imgui.EndTooltip()
	end
end

function imgui.OnDrawFrame()
	if state.v then
		imgui.SetNextWindowSize(imgui.ImVec2(250,310), imgui.Cond.FirstUseEver)
		imgui.SetNextWindowPos(imgui.ImVec2(w/2,h/2), imgui.Cond.FirstUseEver, imgui.ImVec2(0.5,0.5))
		imgui.Begin('Sync Player', state, imgui.WindowFlags.NoCollapse + imgui.WindowFlags.NoResize + imgui.WindowFlags.NoScrollbar)
		imgui.Text('Record command /record')
		imgui.SliderInt('', wait_, 0, 100, 1, imgui.PushItemWidth(150))
		imgui.TextQuestion('Delay playback route', imgui.SameLine())
		imgui.Checkbox('Distance', check_Box)
		imgui.TextQuestion('Checking the distance to the start point(<20metres)', imgui.SameLine())
		imgui.Checkbox('GM Car', check_Box2, imgui.SameLine())
		imgui.TextQuestion('Car will not take damage when route play', imgui.SameLine())
		imgui.BeginChild('', imgui.ImVec2(235, 100), true)
		for i, item in pairs(table_) do
			if imgui.RadioButton(item[1].name..'##a'..i, radioButton, i) then textBuffer.v = table_[radioButton.v][1].name end
		end
		imgui.EndChild()
		if table_[radioButton.v] ~= nil then
			local item = table_[radioButton.v]
			if imgui.InputText('Change name', textBuffer) then item[1].name = textBuffer.v saveConfig() end
			imgui.Text('Name: '..item[1].name..'\nPackets: '..(#item-1)..'\nType: '..item[2].mode)
			if not play then
				if imgui.Button('Start', imgui.ImVec2(60,20)) then
					if check_Box.v then
						local bool, dist = checkDist(item[2].position.x, item[2].position.y, item[2].position.z)
						if bool then
							timeTable_ = tableCopy(item)
							workthread = lua_thread.create(function() playRoute() end)
						else
							sampAddChatMessage('Too far, '..dist..'m to the start point', -1)
						end
					else
						timeTable_ = tableCopy(item)
						workthread = lua_thread.create(function() playRoute() end)
					end
				elseif imgui.Button('Repeat', imgui.ImVec2(60,20), imgui.SameLine()) then
					if check_Box.v then
						local bool, dist = checkDist(item[2].position.x, item[2].position.y, item[2].position.z)
						if bool then
							workthread = lua_thread.create(function() while true do wait(0) timeTable_ = tableCopy(item) playRoute() end end)
						else
							sampAddChatMessage('Too far, '..dist..'m to the start point', -1)
						end
					else
						workthread = lua_thread.create(function() while true do wait(0) timeTable_ = tableCopy(item) playRoute() end end)
					end
				end
				if imgui.Button('Remove', imgui.ImVec2(60,20), imgui.SetCursorPos(imgui.ImVec2(180, 280))) then
					table.remove(table_, radioButton.v)
					saveConfig()
				end
			elseif play then
				if imgui.Button('Stop', imgui.ImVec2(60,20)) then
					workthread:terminate()
					play = false
					freeze(false)
				end
				imgui.SameLine()
				if not pause and imgui.Button('Pause', imgui.ImVec2(60,20)) then
					freeze(true)
				elseif pause and imgui.Button('Resume', imgui.ImVec2(60,20)) then
					freeze(false)
				end
			end
		end
		imgui.End()
	end
end

function sampev.onSendPlayerSync(data)
	if play then return false end
	if record then
		local x, y, z, w = getCharQuaternion(PLAYER_PED)
		table.insert(timeTable_, {mode = 'onFoot',
		leftRightKeys = data.leftRightKeys,
		upDownKeys = data.upDownKeys,
		keysData = data.keysData,
		position = {x = data.position.x, y = data.position.y, z = data.position.z},
		quaternion = {w = data.quaternion[0], x = data.quaternion[1], y = data.quaternion[2], z = data.quaternion[3]},
		quaternionFix = {x = x, y = y, z = z, w = w},
		moveSpeed = {x = data.moveSpeed.x, y = data.moveSpeed.y, z = data.moveSpeed.z},
		animationId = data.animationId,
		animationFlags = data.animationFlags})
	end
end

function sampev.onSendVehicleSync(data)
	if play then return false end
	if record then
		local x, y, z, w = getVehicleQuaternion(storeCarCharIsInNoSave(PLAYER_PED))
		table.insert(timeTable_, {mode = 'onVeh',
		leftRightKeys = data.leftRightKeys,
		upDownKeys = data.upDownKeys,
		keysData = data.keysData,
		position = {x = data.position.x, y = data.position.y, z = data.position.z},
		quaternion = {w = data.quaternion[0], x = data.quaternion[1], y = data.quaternion[2], z = data.quaternion[3]},
		quaternionFix = {x = x, y = y, z = z, w = w},
		moveSpeed = {x = data.moveSpeed.x, y = data.moveSpeed.y, z = data.moveSpeed.z}})
	end
end

function samp_create_sync_data(sync_type, copy_from_player)
    local ffi = require 'ffi'
    local sampfuncs = require 'sampfuncs'
    -- from SAMP.Lua
    local raknet = require 'samp.raknet'
    -- require 'samp.synchronization'

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