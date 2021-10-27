# GlickoAssessor
Generates [Glicko2](http://glicko.net/glicko/glicko2.pdf) rating list from the given pgn file. The data is saved in sqlite db specified by the user, see Example section. It will also detect if certain pgn file is already used in the calculation and in this case it will be skipped. The database has two tables namely `rating` and `pgn`. The rating table records the rating list of players while the pgn table records the pgn file that is used in the rating calculation.


### Setup
* Copy the repo
* Install python 3.8 or later
* Intall dependencies
    * pip install pandas

### Example
Define your sqlite db filename and prepare your pgn file.

```python
import glicko_assessor

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
```

##### Output
```
                       Name  Rating  RD  Volatility  Games  Pts  PtsRate  MinRating  MaxRating
1          Nakamura, Hikaru    2716  44    0.059954     15  9.0    0.600       2628       2804
2           Carlsen, Magnus    2716  44    0.059954     15  9.0    0.600       2628       2804
3            Aronian, Levon    2711  44    0.059933     15  8.5    0.567       2623       2799
4                So, Wesley    2711  44    0.059933     15  8.5    0.567       2623       2799
5       Nepomniachtchi, Ian    2711  44    0.059933     15  8.5    0.567       2623       2799
6               Giri, Anish    2705  44    0.059920     15  8.0    0.533       2617       2793
7   Vachier-Lagrave, Maxime    2705  44    0.059920     15  8.0    0.533       2617       2793
8            Le, Quang Liem    2705  44    0.059920     15  8.0    0.533       2617       2793
9         Firouzja, Alireza    2705  44    0.059920     15  8.0    0.533       2617       2793
10        Radjabov, Teimour    2705  44    0.059920     15  8.0    0.533       2617       2793
11              Ding, Liren    2700  44    0.059916     15  7.5    0.500       2612       2788
12  Vidit, Santosh Gujrathi    2688  44    0.059933     15  6.5    0.433       2600       2776
13    Anton Guijarro, David    2688  44    0.059933     15  6.5    0.433       2600       2776
14           Svidler, Peter    2683  44    0.059954     15  6.0    0.400       2595       2771
15         Karjakin, Sergey    2677  44    0.059984     15  5.5    0.367       2589       2765
16      Duda, Jan-Krzysztof    2666  44    0.060070     15  4.5    0.300       2578       2754
```

`See also the sample.py` script.

You can query the rating table of db.
```python
for row in meltwater.query(f"select * from rating"):
    print(row)
    
(1, 'Giri, Anish', 2705, 44, 0.05992012388069119, 15, 8.0)
(2, 'Vachier-Lagrave, Maxime', 2705, 44, 0.05992012388069119, 15, 8.0)
(3, 'Karjakin, Sergey', 2677, 44, 0.05998400427218611, 15, 5.5)
(4, 'Ding, Liren', 2700, 44, 0.05991587688489624, 15, 7.5)
(5, 'Nakamura, Hikaru', 2716, 44, 0.05995417384593459, 15, 9.0)
(6, 'Duda, Jan-Krzysztof', 2666, 44, 0.06006970783454598, 15, 4.5)
(7, 'Aronian, Levon', 2711, 44, 0.059932873752186616, 15, 8.5)
(8, 'Le, Quang Liem', 2705, 44, 0.05992012388069119, 15, 8.0)
(9, 'Vidit, Santosh Gujrathi', 2688, 44, 0.059932873752186616, 15, 6.5)
...
That is id, name, rating, ratingdeviation, volatility, games, points
```

Or see the contents of pgn table to see which pgn files were already considered in the rating calculation.
```python
for row in meltwater.query(f"select * from pgn"):
    print(row)
    
(1, '1-skillingopp20.pgn')
```

Or return a player list of dictionary.
```python
rlist = meltwater.get_rating()
for r in rlist:
    print(r)

{'id': 1, 'name': 'Giri, Anish', 'rating': 2705, 'ratingdeviation': 44, 'volatility': 0.05992012388069119, 'games': 15, 'points': 8.0}
{'id': 2, 'name': 'Vachier-Lagrave, Maxime', 'rating': 2705, 'ratingdeviation': 44, 'volatility': 0.05992012388069119, 'games': 15, 'points': 8.0}
{'id': 3, 'name': 'Karjakin, Sergey', 'rating': 2677, 'ratingdeviation': 44, 'volatility': 0.05998400427218611, 'games': 15, 'points': 5.5}
{'id': 4, 'name': 'Ding, Liren', 'rating': 2700, 'ratingdeviation': 44, 'volatility': 0.05991587688489624, 'games': 15, 'points': 7.5}
{'id': 5, 'name': 'Nakamura, Hikaru', 'rating': 2716, 'ratingdeviation': 44, 'volatility': 0.05995417384593459, 'games': 15, 'points': 9.0}
...
```

You can update the rating by adding other pgn files from meltwater.
```
pgnfn = './pgn/2-airthingsmastp20.pgn'
meltwater.generate_rating(pgnfn)
```

If you like to generate and save rating list for other tournament use a different db file.
```python
import glicko_assessor

dbname = 'myratinglist.db'
myrating = glicko_assessor.GlickoAssessor(
    dbname,
    init_rating=1500,
    init_rating_deviation=350
)

# 1st rating period
pgnfn = 'tour1.pgn'
myrating.generate_rating(pgnfn)
myrating.print_rating()
```

### Credits
* Mark E. Glickman the designer of [glicko2](http://glicko.net/glicko/glicko2.pdf)
* [Glicko2 library](https://github.com/sublee/glicko2) from sublee
* [markustoivonen](https://github.com/markustoivonen/glicko2) for the bug fix and other modifications
* The [week in chess](https://theweekinchess.com/) for pgn files
