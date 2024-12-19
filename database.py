import os
import ydb

YDB_ENDPOINT = os.getenv("YDB_ENDPOINT")
YDB_DATABASE = os.getenv("YDB_DATABASE")

def get_ydb_pool(ydb_endpoint, ydb_database, timeout=30):
    ydb_driver_config = ydb.DriverConfig(
        ydb_endpoint,
        ydb_database,
        credentials=ydb.credentials_from_env_variables(),
        root_certificates=ydb.load_ydb_root_certificate(),
    )

    ydb_driver = ydb.Driver(ydb_driver_config)
    ydb_driver.wait(fail_fast=True, timeout=timeout)
    return ydb.SessionPool(ydb_driver)

def _format_kwargs(kwargs):
    return {"${}".format(key): value for key, value in kwargs.items()}

def execute_update_query(pool, query, **kwargs):
    def callee(session):
        prepared_query = session.prepare(query)
        session.transaction(ydb.SerializableReadWrite()).execute(
            prepared_query, _format_kwargs(kwargs), commit_tx=True
        )

    return pool.retry_operation_sync(callee)

def execute_select_query(pool, query, **kwargs):
    def callee(session):
        prepared_query = session.prepare(query)
        result_sets = session.transaction(ydb.SerializableReadWrite()).execute(
            prepared_query, _format_kwargs(kwargs), commit_tx=True
        )
        return result_sets[0].rows

    return pool.retry_operation_sync(callee)

# Зададим настройки базы данных
pool = get_ydb_pool(YDB_ENDPOINT, YDB_DATABASE)

# Функция для получения текущего индекса вопроса и очков
def get_quiz_state(user_id):
    query = """
    DECLARE $user_id AS Uint64;
    SELECT question_index, score
    FROM quiz_state
    WHERE user_id = $user_id;
    """
    rows = execute_select_query(pool, query, user_id=user_id)
    if rows:
        return rows[0].question_index, rows[0].score
    else:
        return None, 0

def get_quiz_data_from_db():
    query = """
    SELECT question, options, correct_option
    FROM quiz_data;
    """
    rows = execute_select_query(pool, query)

    quiz_data = []
    for row in rows:
        question = row.question
        options = row.options.split(',')
        correct_option = row.correct_option
        quiz_data.append({
            'question': question,
            'options': options,
            'correct_option': correct_option
        })

    return quiz_data

quiz_data = get_quiz_data_from_db()
