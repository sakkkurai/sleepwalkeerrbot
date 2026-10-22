import traceback
from aiogram import Router, Bot, html
from aiogram.types import ErrorEvent
from config import config

router = Router()

@router.errors()
async def error_handler(event: ErrorEvent, bot: Bot):
    exception = event.exception

    tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
    tb_text = "".join(tb_lines)

    update_info = "Не удалось определить апдейт"
    if event.update.message:
        msg = event.update.message
        update_info = f"💬 Сообщение от {html.quote(msg.from_user.full_name)} ({msg.from_user.id}): {html.quote(msg.text or '')}"
    elif event.update.callback_query:
        call = event.update.callback_query
        update_info = f"🔘 Коллбэк от {html.quote(call.from_user.full_name)} ({call.from_user.id}): {html.quote(call.data or '')}"

    error_message = (
        f"🚨 ПРОИЗОШЛА ОШИБКА В БОТЕ!\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🔍 Контекст: {update_info}\n\n"
        f"❌ Тип ошибки:{html.quote(type(exception).__name__)}\n"
        f"💬 Описание: {html.quote(str(exception))}\n\n"
        f"📋 Стек вызовов:"
    )

    try:
        if len(error_message) + len(tb_text) < 4000:
            await bot.send_message(
                chat_id=config.MODERATION_CHAT_ID,
                text=f"{error_message}\n<pre><code class='language-python'>{html.quote(tb_text)}</code></pre>"
            )
        else:
            from aiogram.types import BufferedInputFile

            full_log = f"{error_message.replace('<b>', '').replace('</b>', '')}\n\n{tb_text}"
            file_data = BufferedInputFile(full_log.encode('utf-8'), filename="error_log.txt")

            await bot.send_document(
                chat_id=config.MODERATION_CHAT_ID,
                document=file_data,
                caption=f"🚨 <b>Критическая ошибка:</b> {html.quote(type(exception).__name__)}. Вывод слишком длинный, логи прикреплены файлом."
            )
    except Exception as e:
        print(f"Не удалось отправить лог ошибки в чат: {e}")
        print(f"Исходная ошибка: {type(exception).__name__}: {exception}")
        traceback.print_exception(
            type(exception),
            exception,
            exception.__traceback__
        )
