from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from database import quiz_data, get_quiz_state
from service import get_question, new_quiz, update_quiz_state, reset_quiz_score

router = Router()

@router.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    await callback.bot.edit_message_reply_markup(
        chat_id=user_id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    await callback.message.answer("Верно!")

    # Получение текущего индекса вопроса и очков
    current_question_index, score = get_quiz_state(user_id)

    if current_question_index is None:
        # Если пользователь начинает квиз заново, обнуляем очки
        reset_quiz_score(user_id)
        current_question_index, score = get_quiz_state(user_id)

    # Обновление очков
    score += 1

    # Обновление номера текущего вопроса и очков в базе данных
    current_question_index += 1
    update_quiz_state(user_id, current_question_index, score)

    if current_question_index < len(quiz_data):
        await get_question(callback.message, user_id)
    else:
        await callback.message.answer(f"Это был последний вопрос. Квиз завершен! Ваш счет: {score}")
        reset_quiz_score(user_id)

@router.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    await callback.bot.edit_message_reply_markup(
        chat_id=user_id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    # Получение текущего индекса вопроса и очков
    current_question_index, score = get_quiz_state(user_id)

    if current_question_index is None:
        # Если пользователь начинает квиз заново, обнуляем очки
        reset_quiz_score(user_id)
        current_question_index, score = get_quiz_state(user_id)

    correct_option = quiz_data[current_question_index]['correct_option']

    await callback.message.answer(f"Неправильно. Правильный ответ: {quiz_data[current_question_index]['options'][correct_option]}")

    # Обновление номера текущего вопроса и очков в базе данных
    current_question_index += 1
    update_quiz_state(user_id, current_question_index, score)

    if current_question_index < len(quiz_data):
        await get_question(callback.message, user_id)
    else:
        await callback.message.answer(f"Это был последний вопрос. Квиз завершен! Ваш счет: {score}")
        reset_quiz_score(user_id)

# Хэндлер на команду /start
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))

# Хэндлер на команду /quiz
@router.message(F.text == "Начать игру")
@router.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    await message.answer(f"Давайте начнем квиз!")
    await new_quiz(message)
