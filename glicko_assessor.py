# -*- coding: utf-8 -*-

"""
glicko_assessor.py


glicko2.py is taken from https://github.com/sublee/glicko2

2021.10.21
    The glicko2.py used in GlickoAssessor is taken from https://github.com/fsmosca/glicko2/tree/Fix-RD-calculation
    which is from https://github.com/markustoivonen/glicko2/tree/61f927346d61ec0f9a96208725fd8bff0cea41c6

References:
    http://glicko.net/glicko/glicko2.pdf

Notes:
    Determine a rating and RD for each player at the onset of the rating period. The
    system constant, τ , which constrains the change in volatility over time, needs to be
    set prior to application of the system. Reasonable choices are between 0.3 and 1.2,
    though the system should be tested to decide which value results in greatest predictive
    accuracy. Smaller values of τ prevent the volatility measures from changing by large
    amounts, which in turn prevent enormous changes in ratings based on very improbable
    results. If the application of Glicko-2 is expected to involve extremely improbable
    collections of game outcomes, then τ should be set to a small value, even as small as,
    say, τ = 0.2.
    (a) If the player is unrated, set the rating to 1500 and the RD to 350. Set the player’s
    volatility to 0.06 (this value depends on the particular application).
    (b) Otherwise, use the player’s most recent rating, RD, and volatility σ.
"""


__author__ = 'fsmosca'
__script_name__ = 'glicko_assessor'
__version__ = 'v0.1.0'


from pathlib import Path

from glicko2 import Glicko2
import sqlite3
from sqlite3 import Error
import pandas as pd


TAU = 0.75  # system constant, see Notes.


SQL_CREATE_RATING_TABLE = """ CREATE TABLE IF NOT EXISTS rating (
                                    id integer PRIMARY KEY,
                                    name text NOT NULL,
                                    rating integer NOT NULL,
                                    rd integer NOT NULL,
                                    vola float NOT NULL,
                                    games integer NOT NULL,
                                    pts float NOT NULL
                                ); """

SQL_CREATE_PGN_TABLE = """ CREATE TABLE IF NOT EXISTS pgn (
                                    id integer PRIMARY KEY,
                                    name text NOT NULL
                                ); """


class GlickoAssessor:
    def __init__(self, dbfile, init_rating=1500, init_rating_deviation=350, init_volatility=0.06, init_tau=TAU):
        self.dbfile = dbfile
        self.init_rating = init_rating
        self.init_rating_deviation = init_rating_deviation
        self.init_volatility = init_volatility
        self.init_tau = init_tau
        self.conn = self.create_connection()
        self.cur = self.conn.cursor()

    def __repr__(self):
        return (f'rating: {self.init_rating}, ratingdeviation: {self.init_rating_deviation}, '
                f'volatility: {self.init_volatility}, tau: {self.init_tau}')

    def query(self, arg):
        self.cur.execute(arg)
        self.conn.commit()
        return self.cur

    def __del__(self):
        self.conn.close()

    def create_connection(self):
        self.conn = None
        try:
            self.conn = sqlite3.connect(self.dbfile)
        except Error as e:
            print(e)
        else:
            return self.conn

    def update_data(self, newdata):
        """Update player info."""
        sql = ''' UPDATE rating
                  SET rating = ? ,
                      rd = ? ,
                      vola = ? ,
                      games = games + ? ,
                      pts = pts + ?
                  WHERE name = ?'''
        self.cur.execute(sql, newdata)
        self.conn.commit()

    def query_name(self, name):
        """Query rating, rating_deviation and volatility based on given name."""
        self.cur.execute("SELECT * FROM rating WHERE name=?", (name,))

        rows = self.cur.fetchall()
        if not len(rows):
            return None

        for r in rows:
            return r[2], r[3], r[4]  # rating, rating_deviation, volatility

    def insert_pgn_data(self, pgnfn):
        """Save the pgn file in pgn table."""
        sql = ''' INSERT INTO pgn(name)
                  VALUES(?) '''
        self.cur.execute(sql, pgnfn)
        self.conn.commit()
        return self.cur.lastrowid

    def insert_player_data(self, init_player_data):
        """Create player data in rating table."""
        sql = ''' INSERT INTO rating(name,rating,rd,vola,games,pts)
                  VALUES(?,?,?,?,?,?) '''
        self.cur.execute(sql, init_player_data)
        self.conn.commit()
        return self.cur.lastrowid

    def get_rating(self):
        """Returns a list of dict of rating data."""
        self.cur.execute("SELECT * FROM rating")

        rows = self.cur.fetchall()

        ratings = []
        for v in rows:
            ratings.append({'id': v[0], 'name': v[1], 'rating': v[2], 'ratingdeviation': v[3],
                            'volatility': v[4], 'games': v[5], 'points': v[6]})

        return ratings

    def print_rating(self):
        """Print rating list from the dbfile"""
        if not Path(self.dbfile).is_file():
            print(f'Warning, file {self.dbfile} is missing!')
            return

        self.cur.execute("SELECT * FROM rating")

        rows = self.cur.fetchall()

        data = []
        for r in rows:
            data.append({'Name': r[1], 'Rating': r[2], 'RD': r[3], 'Volatility': r[4], 'Games': r[5], 'Pts': r[6]})

        df = pd.DataFrame(data)

        # Create new columns
        df['PtsRate'] = df['Pts'] / df['Games']
        df['MinRating'] = df['Rating'] - df['RD'] * 2
        df['MaxRating'] = df['Rating'] + df['RD'] * 2

        # Round-off pts rate to 3 decimal places.
        df.PtsRate = df.PtsRate.round(3)

        df.sort_values(by=['Rating', 'RD'], ascending=[False, True], inplace=True)
        df = df.reset_index(drop=True)
        df.index += 1

        print(df.to_string())

    def create_table(self, create_table_sql):
        self.cur.execute(create_table_sql)

    def query_pgn_name(self, name):
        """Query the contents of pgn table"""
        self.cur.execute("SELECT * FROM pgn WHERE name=?", (name,))

        rows = self.cur.fetchall()
        if not len(rows):
            return None

        for r in rows:
            return r[1]  # name

    def generate_rating(self, pgnfile):
        """Calculates rating from pgnfile and save it in dbfile."""
        init_rating = self.init_rating
        init_rd = self.init_rating_deviation
        init_volatility = self.init_volatility

        # Create a table called rating.
        self.create_table(SQL_CREATE_RATING_TABLE)
        self.create_table(SQL_CREATE_PGN_TABLE)

        # Start processing the games in pgn file.
        env = Glicko2(tau=self.init_tau)

        # Every pgn file is a rating period.
        pgnfiles = [pgnfile]

        # Calculate rating based on game results, and register new players in db.
        for fn in pgnfiles:
            # Check if this pgn file is already used.
            pgnfilename = Path(fn).name
            if self.query_pgn_name(pgnfilename) is not None:
                print(f'Warning the file {pgnfilename} was already used in rating calculation.')
                continue

            player_names = get_player_names(fn)
            results = read_games(fn)  # [(me, you, mypts) ...]

            # Record new names to db.
            for r in results:
                name = r[0]
                num_games = 0
                num_pts = 0
                with self.conn:
                    if self.query_name(name) is None:
                        init_player_data = (name, init_rating, init_rd, init_volatility, num_games, num_pts,)
                        self.insert_player_data(init_player_data)

            # Update rating.
            rating_res = {}
            with self.conn:
                results = read_games(fn)
                for p in player_names:
                    opp_data_for_rating = []
                    games = 0
                    total_pts = 0

                    # Update rating of player p.
                    for r in results:
                        myname = r[0]

                        if myname != p:
                            continue

                        games += 1

                        oppname = r[1]
                        mypts = r[2]
                        total_pts += mypts

                        # Query db to get rating, RD and volatility.
                        myr, myrd, myvola = self.query_name(myname)

                        # For opponent, we don't need volatility.
                        oppr, opprd, _ = self.query_name(oppname)

                        # Create glicko player object.
                        mydata = env.create_rating(myr, myrd, myvola)
                        oppdata = env.create_rating(oppr, opprd)

                        opp_data_for_rating.append((mypts, oppdata))

                    # Rate the match and save new info to a dict,
                    # we will update the db once all the players are evaluated.
                    mynew = env.rate(mydata, opp_data_for_rating)
                    rating_res.update({p: [mynew, games, total_pts]})

                # All players are evaluated, now update the db.
                for p in player_names:
                    for k, v in rating_res.items():
                        if k != p:
                            continue

                        mynewr = v[0].mu  # new rating
                        mynewrd = v[0].phi  # new RD or rating deviation
                        myvola = v[0].sigma  # new volatility
                        games = v[1]  # games played by this player from the pgn file
                        pts = v[2]  # points scored by this player from the pgn file
                        self.update_data((int(mynewr), int(mynewrd), float(myvola), games, pts, p))

            # Save the filename to pgn table.
            self.insert_pgn_data((pgnfilename,))


def get_player_names(fn):
    """
    Returns a list of player names.

    [White "Thomason, J."]
    [Black "Fischer, Robert James"]
    [Result "0-1"]
    """
    ret = []
    with open(fn) as h:
        for lines in h:
            line = lines.rstrip()
            if '[White ' in line:
                wp = line.split('"')[1].strip()
                ret.append(wp)
            elif '[Black ' in line:
                bp = line.split('"')[1].strip()
                ret.append(bp)

    return list(set(ret))


def read_games(fn):
    """
    Returns a list of results of the form (p1, p2, p1_pts).
    """
    ret = []
    wp, bp = None, None

    with open(fn) as h:
        for lines in h:
            line = lines.rstrip()

            if '[White ' in line:
                wp = line.split('"')[1].strip()
            elif '[Black ' in line:
                bp = line.split('"')[1].strip()
            elif '[Result ' in line:
                res = line.split('"')[1].strip()

                assert(wp is not None)
                assert(bp is not None)

                if res == '1-0':
                    ret.append((wp, bp, 1))
                    ret.append((bp, wp, 0))
                elif res == '0-1':
                    ret.append((bp, wp, 1))
                    ret.append((wp, bp, 0))
                elif res == '1/2-1/2':
                    ret.append((wp, bp, 0.5))
                    ret.append((bp, wp, 0.5))
                else:
                    print(f'Warning, game result is {res}. This game result will not be saved.')

                wp, bp = None, None  # start of new game

    return ret
