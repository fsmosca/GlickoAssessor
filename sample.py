import glicko_assessor


def main():
    print(glicko_assessor.__version__)

    dbname = 'meltwater.db'  # sqlite db
    meltwater = glicko_assessor.GlickoAssessor(
        dbname,
        init_rating=2700,
        init_rating_deviation=50
    )

    # 1st rating period
    pgnfn = './pgn/1-skillingopp20.pgn'
    meltwater.generate_rating(pgnfn)
    meltwater.print_rating()
    print()

    # 2nd rating period
    pgnfn = './pgn/2-airthingsmastp20.pgn'
    meltwater.generate_rating(pgnfn)
    meltwater.print_rating()
    print()


if __name__ == "__main__":
    main()
