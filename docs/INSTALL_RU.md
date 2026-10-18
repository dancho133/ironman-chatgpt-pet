# Руководство по установке Iron Man Pet (ChatGPT Pets v2)

Данное руководство описывает способы установки кастомного анимированного компаньона **Iron Man (Tony Stark)** в **ChatGPT Desktop / Work Mode**.

---

## Вариант 1. Установка в 1 клик (Самый быстрый способ)

Если вы используете официальный клиент ChatGPT с поддержкой Work Mode и Pets:

1. Перейдите по официальной ссылке:  
   👉 **[Установить Iron Man в ChatGPT Pets](https://chatgpt.com/s/sharepet_6ad48e2159088191a19a5b11b898c6c1)**
2. Нажмите кнопку **"Adopt Pet"** (или **"Усыновить питомца"**).
3. Питомец мгновенно появится в вашей библиотеке и будет готов к активации.

---

## Вариант 2. Установка через диалог с Codex / ChatGPT Work Mode

Если вы находитесь в сессии Codex / ChatGPT Work:

1. Скачайте файл спрайт-шита:  
   [`assets/ironman_funko_anime_v2_spritesheet.png`](../assets/ironman_funko_anime_v2_spritesheet.png)
2. Прикрепите этот файл к сообщению (кнопка `+` или перетаскиванием).
3. Отправьте ассистенту следующий текст:

```text
Я прикрепил готовый, полностью прошедший валидацию 3D-спрайт-шит стандарта v2 (1536×2288 px, 11 строк, 73 активных кадра, 15 прозрачных ячеек): ironman_funko_anime_v2_spritesheet.png.

ВАЖНО: НЕ перерисовывай его и НЕ запускай генераторы картинок — используй этот файл напрямую байт-в-байт!
Выполни по шагам:
1. Вызови mcp_codex_apps_pets_validate_pet_spritesheet для файла ironman_funko_anime_v2_spritesheet.png и убедись, что valid=true (sprite_version=2).
2. Вызови mcp_codex_apps_pets_prepare_pet_upload для этого же файла и получи upload_session_id.
3. Создай или обнови пета через mcp_codex_apps_pets_create_pet (или update_pet), передав upload_session_id, name="Iron Man" и description="3D Funko Pop & Anime Nendoroid Iron Man (Tony Stark) with reactive repulsor particles and v2 cursor tracking".
4. Сделай этого пета активным через mcp_codex_apps_pets_select_pet.
```

---

## Вариант 3. Установка через прямой API / MCP Tools

Разработчики могут использовать официальный плагин `Pets` через протокол Model Context Protocol (MCP):

```python
# 1. Валидация
validation = call_mcp("pets_validate_pet_spritesheet", {
    "file": "/path/to/ironman_funko_anime_v2_spritesheet.png"
})
assert validation["valid"] is True

# 2. Подготовка сессии загрузки
upload = call_mcp("pets_prepare_pet_upload", {
    "file": "/path/to/ironman_funko_anime_v2_spritesheet.png"
})
session_id = upload["upload"]["upload_session_id"]

# 3. Создание пета
pet = call_mcp("pets_create_pet", {
    "upload_session_id": session_id,
    "name": "Iron Man",
    "description": "3D Funko Pop & Anime Nendoroid Iron Man (Tony Stark)"
})
pet_id = pet["pet"]["id"]

# 4. Активация
call_mcp("pets_select_pet", {"pet_id": pet_id})
```

---

## Проверка валидности локально

Перед загрузкой любого кастомного спрайт-шита вы можете протестировать его локальным скриптом:

```bash
python scripts/validate_spritesheet.py assets/ironman_funko_anime_v2_spritesheet.png --v2
```

Ожидаемый вывод:
```text
================================================================
         ChatGPT Pets Spritesheet Validation Report
================================================================
File:            assets/ironman_funko_anime_v2_spritesheet.png
Dimensions:      1536x2288 px
Standard:        v2
Active Frames:   73
Empty Cells:     15
Residue Pixels:  0
----------------------------------------------------------------
RESULT: PASSED (valid=True) - Spritesheet is 100% compliant!
================================================================
```
