from database import pool, execute_update_query, execute_select_query, quiz_data
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types

def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()

    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data="right_answer" if option == right_answer else "wrong_answer")
        )

    builder.adjust(1)
    return builder.as_markup()

async def get_question(message, user_id):
    # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await get_quiz_index(user_id)
    correct_index = quiz_data[current_question_index]['correct_option']
    opts = quiz_data[current_question_index]['options']
    kb = generate_options_keyboard(opts, opts[correct_index])
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)

async def new_quiz(message):
    user_id = message.from_user.id
    reset_quiz_score(user_id)
    await get_question(message, user_id)

async def get_quiz_index(user_id):
    get_user_index = """
    DECLARE $user_id AS Uint64;
    SELECT question_index
    FROM `quiz_state`
    WHERE user_id = $user_id;
    """
    results = execute_select_query(pool, get_user_index, user_id=user_id)

    if len(results) == 0:
        return 0
    if results[0]["question_index"] is None:
        return 0
    return results[0]["question_index"]

# Функция для обновления индекса вопроса и очков
def update_quiz_state(user_id, question_index, score):
    query = """
    DECLARE $user_id AS Uint64;
    DECLARE $question_index AS Uint64;
    DECLARE $score AS Uint64;
    UPSERT INTO quiz_state (user_id, question_index, score)
    VALUES ($user_id, $question_index, $score);
    """
    execute_update_query(pool, query, user_id=user_id, question_index=question_index, score=score)

# Функция для обнуления очков при начале нового квиза
def reset_quiz_score(user_id):
    query = """
    DECLARE $user_id AS Uint64;
    UPSERT INTO quiz_state (user_id, question_index, score)
    VALUES ($user_id, 0, 0);
    """
    execute_update_query(pool, query, user_id=user_id)
