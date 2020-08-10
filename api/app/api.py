from flask import Flask, Blueprint, jsonify, request, current_app
from random import randint
from json import dumps
from time import sleep

def create_api() -> Blueprint:
    """
    Creates an instance of your API. If you'd like to toggle behavior based on
    command line flags or other inputs, add them as arguments to this function.
    """
    api = Blueprint('api', __name__)

    def error(message: str, status: int = 400) -> (str, int):
        return jsonify({ 'error': message}), status

    # This route simply tells anything that depends on the API that it's
    # working. If you'd like to redefine this behavior that's ok, just
    # make sure a 200 is returned.
    @api.route('/')
    def index() -> (str, int):
        return '', 204

    # The route below is an example API route. You can delete it and add
    # your own.
    @api.route('/api/solve', methods=['POST'])
    def solve():
        data = request.get_json()

        question = data['question']
        if question is None or len(question.strip()) == 0:
            return error('Please enter a question.')

        choices = data['choices']
        if len(choices) != 2:
            return error('Please enter two answers.')

        (first_answer, second_answer) = choices
        if first_answer is None or len(first_answer.strip()) == 0:
            return error('Please enter two answers.')
        if second_answer is None or len(second_answer.strip()) == 0:
            return error('Please enter two answers.')

        # We use a randomly generated value between 0 and 100, and select
        # answer 1 if it's > 50 and answer 2 if it's < 50.
        random_value = randint(0, 100)
        if random_value >= 50:
            selected = first_answer
        else:
            selected = second_answer

        # We produce a score with no actual meaning, it's just for demonstration
        # purposes
        score = random_value - 50 if random_value > 50 else random_value - 0

        answer = {
            'query': {
                'question': question,
                'choices': [ first_answer, second_answer ]
            },
            'answer': selected,
            'score': score
        }
        current_app.logger.info(dumps(answer))

        # Create simulated latency. You should definitely remove this. It's
        # just so that the API actually behaves like one we'd expect you to
        # build
        sleep(randint(1,3))

        return jsonify(answer)

    return api
