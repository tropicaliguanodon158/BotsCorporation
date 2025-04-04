require "lib.moonloader"
local huy = require("samp.events")
local timeOffset = 0 -- Смещение времени для МСК

local oX = 250
local oY = 430

function main()
    if not isSampLoaded() or not isSampfuncsLoaded() then return end
    while not isSampAvailable() do wait(100) end
    
    -- Создаем статичные текстдравы один раз
    sampTextdrawCreate(221, "Server_time:", oX, oY)
    sampTextdrawSetLetterSizeAndColor(221, 0.3, 1.7, 0xFFe1e1e1)
    sampTextdrawSetOutlineColor(221, 0.5, 0xFF000000)
    sampTextdrawSetAlign(221, 1)
    sampTextdrawSetStyle(221, 2)
    
    sampTextdrawCreate(222, "", oX + 90, oY) -- Пустой текстдрав для времени
    sampTextdrawSetLetterSizeAndColor(222, 0.3, 1.7, 0xFFff6347)
    sampTextdrawSetOutlineColor(222, 0.5, 0xFF000000)
    sampTextdrawSetAlign(222, 1)
    sampTextdrawSetStyle(222, 2)
    
    while true do
        -- Получаем текущее время сервера с учетом смещения
        local serverTime = os.time() + timeOffset
        -- Форматируем время как МСК (HH:MM:SS)
        local mskTime = os.date("%H:%M:%S", serverTime)
        
        -- Обновляем только текст с временем
        sampTextdrawSetString(222, mskTime)
        
        wait(500)
    end
end

function huy.onShowDialog(dialogId, style, title, button1, button2, text)
    if string.match(text, "Текущее время") then
        -- Парсим дату и время из диалога
        local chislo, mesyac, god = string.match(text, "Сегодняшняя дата:%s+{2EA42E}(%d+):(%d+):(%d+)")
        local chas, minuti, sekundi = string.match(text, "Текущее время:%s+{345690}(%d+):(%d+):(%d+)")
        
        if chislo and mesyac and god and chas and minuti and sekundi then
            -- Создаем таблицу с серверным временем
            local serverDatetime = {
                year = tonumber(god),
                month = tonumber(mesyac),
                day = tonumber(chislo),
                hour = tonumber(chas),
                min = tonumber(minuti),
                sec = tonumber(sekundi)
            }
            
            -- Вычисляем разницу между серверным временем и локальным (в секундах)
            timeOffset = os.time(serverDatetime) - os.time()
            
            -- Для МСК+0 не нужно дополнительных корректировок,
            -- так как скрипт теперь использует серверное время напрямую
        end
    end
end