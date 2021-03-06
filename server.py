from api import opendota
from constants import model_constants
from model import model_fitter
from flask import Flask, request
from flask import render_template
from flask.json import jsonify
from model import predictor

app = Flask(__name__)


# @api.route('/leaderboard')
@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    player_ids = request.args.get("players").split(',')
    print(player_ids)
    time_frame = request.args.get("time_window", default='all')
    board = get_board_data(player_ids, time_frame)
    return jsonify(sorted(board, key=lambda x: -x['win_rate']))


def get_board_data(player_ids, time_frame):
    board = []
    players = [opendota.resolve(player_id) for player_id in player_ids]
    days = model_constants.TIME_WINDOW[time_frame]
    print(players)
    for player in players:
        data = fetch_player_data(days, player)
        win = data['win']
        lose = data['lose']
        board.append({'player_id': player, 'win_rate': safe_div(win,(win + lose))})
    print(board)
    return board


def safe_div(x,y):
    if y == 0:
        return 0
    return x / y


def fetch_player_data(days, player):
    if days == -1:
        return opendota.call_opendota(('players', player, 'wl'))
    else:
        return opendota.call_opendota(('players', player, 'wl'), {'date': days})


@app.route('/compare', methods=['GET'])
def compare():
    player1 = opendota.get_stats(request.args.get("player1"))
    player2 = opendota.get_stats(request.args.get("player2"))

    labels = ['kda', 'last_hits/10', 'actions_per_min/10', 'neutral_kills/10', 'tower_kills', 'tower_damage/100',
              'hero_damage/1000', 'gold_per_min/1000', 'xp_per_min/100']
    values = [
        (player1.kda, player2.kda),
        (player1.last_hits/10, player2.last_hits/10),
        (player1.actions_per_min/10, player2.actions_per_min/10),
        (player1.neutral_kills/10, player2.neutral_kills/10),
        (player1.tower_kills, player2.tower_kills),
        (player1.tower_damage/100, player2.tower_damage/100),
        (player1.hero_damage/1000, player2.hero_damage/1000),
        (player1.gold_per_min/100, player2.gold_per_min/100),
        (player1.xp_per_min/100, player2.xp_per_min/100)
    ]

    return render_template('chart.html', values=values, labels=labels)


@app.route('/suggest', methods=['GET'])
def suggest():
    player = opendota.resolve(request.args.get("player"))
    result = {'suggested_hero': predictor.predict(player)}
    return jsonify(result)


# Train model
@app.route('/train', methods=['GET'])
def train_model():
    model_fitter.train_model(request.args.get("training_size", default=model_constants.TRAINING_SIZE),
                             model_constants.REMOTE_MODE)
    result = {'message': 'Training done', 'status': '200'}
    return jsonify(result)


@app.route('/train_locally', methods=['GET'])
def train_model_locally():
    model_fitter.train_model(request.args.get("training_size", default=model_constants.TRAINING_SIZE),
                             model_constants.LOCAL_MODE)
    result = {'message': 'Training done', 'status': '200'}
    return jsonify(result)


@app.route("/")
def chart():
    return render_template('main.html', values=None, labels=None)


if __name__ == '__main__':
    app.run(debug=True)  # Start a development server
