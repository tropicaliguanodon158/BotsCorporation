local imgui = require('mimgui')

local new = imgui.new
local st = false
local one_raz_gaz = false

local WinState = new.bool()
local mode = new.int(2)
local waiting = new.int(7)

imgui.OnFrame(function() return WinState[0] end, function(player)
    imgui.SetNextWindowPos(imgui.ImVec2(500,500), imgui.Cond.FirstUseEver, imgui.ImVec2(0.5, 0.5))
    imgui.SetNextWindowSize(imgui.ImVec2(377, 270), imgui.Cond.Always)
    imgui.Begin('TrainBot v2.1 (youtube.com/@TheSampHack)', WinState, imgui.WindowFlags.NoResize)
    imgui.RadioButtonIntPtr('Medium',mode,1)
    imgui.RadioButtonIntPtr('Legit',mode,2)
    imgui.SliderInt('Waiting in ostanovka', waiting, 5, 24) 
    if (imgui.Button(st and 'Stop work' or 'Start work')) then 
        st = not st
    end
    imgui.End()
end)

function main()
    repeat wait(0)
    until isSampAvailable()
    sampRegisterChatCommand('TrainBot',function ()
        WinState[0] = not WinState[0]
        
    end)
    while true do
        wait(0)
        if (isCharInAnyCar(PLAYER_PED) and st and mode[0] == 1) then
            local finded, x, y, z = SearchMarker()
            if finded then
                local mX, mY, mZ = getCharCoordinates(PLAYER_PED)
                local dist = getDistanceBetweenCoords3d(x, y, z, mX, mY, mZ)
                if dist > 1 then
                    setTrainSpeed(storeCarCharIsInNoSave(PLAYER_PED), 42.0)
                else
                    setTrainSpeed(storeCarCharIsInNoSave(PLAYER_PED), 0.0)
                    wait(5000)
                    if isCharInAnyCar(PLAYER_PED) then
                        setTrainSpeed(storeCarCharIsInNoSave(PLAYER_PED), 42.0)
                    end
                end
            end
        elseif (st and not isCharInAnyCar(PLAYER_PED)) then
           
            runToPoint(-2102.4118652344, 512.90368652344, 1487.6927490234) 
            while (not isCharInAnyCar(PLAYER_PED) and st) do
                setGameKeyState(21, 255)
                wait(0)
                setGameKeyState(21, 0)
                wait(100)
                local reysdialogid = sampGetCurrentDialogId()
                sampSendDialogResponse(reysdialogid, 1, 0, "")
                wait(500)
            end
        elseif (isCharInAnyCar(PLAYER_PED) and st and mode[0] == 2) then
            local finded, x, y, z = SearchMarker()
            if finded then
                if one_raz_gaz == false then
                    gaz()
                    wait(30000)
                    one_raz_gaz = true
                else
                    local mX, mY, mZ = getCharCoordinates(PLAYER_PED)
                    local dist = getDistanceBetweenCoords3d(x, y, z, mX, mY, mZ)
                    if dist > 200 then
                        setTrainSpeed(storeCarCharIsInNoSave(PLAYER_PED),42.0)
                    else
                        brake()
                        wait(10000)
                        wait(waiting[0]*1000)
                        one_raz_gaz = false
                        if isCharInAnyCar(PLAYER_PED) then
                            setTrainSpeed(storeCarCharIsInNoSave(PLAYER_PED), 42.0)
                        end
                    end
                end
            end
        end
    end
end


function gaz()
    lua_thread.create(function ()
        for i=0, 42 do 
            if st and isCharInAnyCar(PLAYER_PED) then
                setTrainSpeed(storeCarCharIsInNoSave(PLAYER_PED), i+0.0)
                wait(30000/42)
            end
        end
    end)
end

function brake()
    lua_thread.create(function ()
        for i = 42, 0, -1 do
            if st and isCharInAnyCar(PLAYER_PED) then
                setTrainSpeed(storeCarCharIsInNoSave(PLAYER_PED), i+0.0)
                wait(10000/42)
            end
        end
    end)
end

function SearchMarker()
    local isFind = false
    if not isFind then
        local ret_posX = 0.0
        local ret_posY = 0.0
        local ret_posZ = 0.0
        for id = 0, 31, 1 do
            local MarkerStruct = 0
            MarkerStruct = 0xC7F168 + id * 56
            local MarkerPosX = representIntAsFloat(readMemory(MarkerStruct + 0, 4, false))
            local MarkerPosY = representIntAsFloat(readMemory(MarkerStruct + 4, 4, false))
            local MarkerPosZ = representIntAsFloat(readMemory(MarkerStruct + 8, 4, false))
            if MarkerPosX ~= 0.0 or MarkerPosY ~= 0.0 or MarkerPosZ ~= 0.0 then
                ret_posX = MarkerPosX
                ret_posY = MarkerPosY
                ret_posZ = MarkerPosZ
                isFind = true
            end
        end
        return isFind, ret_posX, ret_posY, ret_posZ
    end
end

function runToPoint(tox, toy)
    if st then
        local x, y, z = getCharCoordinates(PLAYER_PED)
        local angle = getHeadingFromVector2d(tox - x, toy - y)
        local xAngle = math.random(-50, 50)/100
        setCameraPositionUnfixed(xAngle, math.rad(angle - 90))
        stopRun = false
        while getDistanceBetweenCoords2d(x, y, tox, toy) > 0.8 and st do
            setGameKeyState(1, -255)
      
            wait(1)
            x, y, z = getCharCoordinates(PLAYER_PED)
            angle = getHeadingFromVector2d(tox - x, toy - y)
            setCameraPositionUnfixed(xAngle, math.rad(angle - 90))
            if stopRun then
                stopRun = false
                break
            end
        end
    end
end
