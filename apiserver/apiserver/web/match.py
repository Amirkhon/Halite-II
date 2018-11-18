"""
Match API endpoints - list matches and get replays/error logs.
"""
import io
import os

import flask
import sqlalchemy
#import google.cloud.exceptions as gcloud_exceptions
#import google.cloud.storage as gcloud_storage

from .. import model, util

from .blueprint import web_api
from . import util as api_util


def get_match_helper(match_id):
    """
    Get a particular match by its ID.

    :param match_id: The ID of the match.
    :return: A dictionary with the game information.
    """
    with model.engine.connect() as conn:
        query = conn.execute(sqlalchemy.sql.select([
            model.game_participants.c.user_id,
            model.game_participants.c.bot_id,
            model.game_participants.c.rank,
            model.game_participants.c.version_number,
            model.game_participants.c.player_index,
            model.game_participants.c.timed_out,
            model.game_participants.c.leaderboard_rank,
            model.game_participants.c.mu,
            model.game_participants.c.sigma,
        ]).where(
            model.game_participants.c.game_id == match_id
        ))

        match = conn.execute(sqlalchemy.sql.select([
            model.games.c.replay_name,
            model.games.c.replay_bucket,
            model.games.c.map_width,
            model.games.c.map_height,
            model.games.c.time_played,
            model.games.c.challenge_id,
        ]).where(
            model.games.c.id == match_id
        )).first()

        if not match:
            return None

        result = {
            "map_width": match["map_width"],
            "map_height": match["map_height"],
            "replay": match["replay_name"],
            "replay_class": match["replay_bucket"],
            "time_played": match["time_played"],
            "challenge_id": match["challenge_id"],
            "players": {}
        }
        for row in query.fetchall():
            result["game_id"] = match_id
            result["players"][row["user_id"]] = {
                "bot_id": row["bot_id"],
                "version_number": row["version_number"],
                "player_index": row["player_index"],
                "rank": row["rank"],
                "timed_out": bool(row["timed_out"]),
                "leaderboard_rank": row["leaderboard_rank"],
                "mu": row["mu"],
                "sigma": row["sigma"],
            }

        # Update game_view_stat table
        conn.execute(model.game_view_stats.update().where(
            model.game_view_stats.c.game_id == match_id
        ).values(
            views_total=model.game_view_stats.c.views_total + 1,
        ))

    return result


def list_matches_helper(offset, limit, participant_clause,
                        where_clause, order_clause):
    """
    Generate a list of matches by certain criteria.

    :param int offset: How
    :param int limit: How many results to return.
    :param participant_clause: An SQLAlchemy clause to filter the matches,
    based on the participants in the match.
    :param where_clause: An SQLAlchemy clause to filter the matches.
    :param list order_clause: A list of SQLAlchemy conditions to sort the
    results on.
    :return: A list of game data dictionaries.
    """
    result = []

    with model.engine.connect() as conn:
        query = sqlalchemy.sql.select([
            model.games.c.id,
            model.games.c.replay_name,
            model.games.c.replay_bucket,
            model.games.c.map_width,
            model.games.c.map_height,
            model.games.c.time_played,
            model.games.c.challenge_id,
            model.game_stats.c.turns_total,
            model.game_stats.c.planets_destroyed,
            model.game_stats.c.ships_produced,
            model.game_stats.c.ships_destroyed,
        ]).select_from(model.games.outerjoin(
            model.game_stats,
            (model.games.c.id == model.game_stats.c.game_id)
        )).where(
            where_clause &
            sqlalchemy.sql.exists(
                model.game_participants.select(
                    participant_clause &
                    (model.game_participants.c.game_id == model.games.c.id)
                )
            )
        ).order_by(
            *order_clause
        ).offset(offset).limit(limit).reduce_columns()
        matches = conn.execute(query)

        for match in matches.fetchall():
            participants = conn.execute(
                model.game_participants.join(
                    model.users,
                    model.game_participants.c.user_id == model.users.c.id
                ).select(
                    model.game_participants.c.game_id == match["id"]
                )
            )

            match = {
                "game_id": match["id"],
                "map_width": match["map_width"],
                "map_height": match["map_height"],
                "replay": match["replay_name"],
                "replay_class": match["replay_bucket"],
                "time_played": match["time_played"],
                "turns_total": match["turns_total"],
                "planets_destroyed": match["planets_destroyed"],
                "ships_produced": match["ships_produced"],
                "ships_destroyed": match["ships_destroyed"],
                "challenge_id": match["challenge_id"],
                "players": {},
            }

            for participant in participants:
                match["players"][participant["user_id"]] = {
                    "username": participant["username"],
                    "bot_id": participant["bot_id"],
                    "version_number": participant["version_number"],
                    "player_index": participant["player_index"],
                    "rank": participant["rank"],
                    "timed_out": bool(participant["timed_out"]),
                    "leaderboard_rank": participant["leaderboard_rank"],
                    "mu": participant["mu"],
                    "sigma": participant["sigma"],
                }

            result.append(match)

    return result


@web_api.route("/match")
@util.cross_origin(methods=["GET"])
def list_matches():
    offset, limit = api_util.get_offset_limit()
    where_clause, order_clause, manual_sort = api_util.get_sort_filter({
        "game_id": model.games.c.id,
        "time_played": model.games.c.time_played,
        "views_total": model.game_view_stats.c.views_total,
        "turns_total": model.game_stats.c.turns_total,
        "planets_destroyed": model.game_stats.c.planets_destroyed,
        "ships_produced": model.game_stats.c.ships_produced,
        "ships_destroyed": model.game_stats.c.ships_destroyed,
        "challenge_id": model.games.c.challenge_id,
    }, ["timed_out"])

    participant_clause = sqlalchemy.true()
    for (field, _, _) in manual_sort:
        if field == "timed_out":
            participant_clause &= model.game_participants.c.timed_out

    result = list_matches_helper(
        offset, limit, participant_clause, where_clause, order_clause)

    return flask.jsonify(result)


@web_api.route("/match/<int:match_id>")
def get_match(match_id):
    match = get_match_helper(match_id)
    if not match:
        raise util.APIError(404, message="Match not found.")
    return flask.jsonify(match)


@web_api.route("/replay/class/<int:replay_bucket>/name/<replay_name>",
               methods=["GET"])
@util.cross_origin(methods=["GET"])
def get_replay(replay_bucket, replay_name):
    bucket = model.get_replay_bucket(replay_bucket)
    #blob = gcloud_storage.Blob(replay_name, bucket, chunk_size=262144)
    #buffer = io.BytesIO()

    #try:
        #blob.download_to_file(buffer)
    #except gcloud_exceptions.NotFound:
    if not os.path.isfile(replay_name):
        raise util.APIError(404, message="Replay not found.")

    #buffer.seek(0)
    response = flask.make_response(flask.send_from_directory(
        bucket, replay_name,
        mimetype="application/x-halite-2-replay",
        as_attachment=True,
        attachment_filename="{}.{}.hlt".format(replay_name, replay_bucket)))

    response.headers["Content-Length"] = str(os.stat(os.path.join(bucket, replay_name)).st_size)

    return response
