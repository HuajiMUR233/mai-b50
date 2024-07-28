import functools
import json
import math
import csv
import sys

from pydantic import BaseModel

CURRENT_VERSION = 21


class Score(BaseModel):
    id: int
    level: int
    constant: float
    combo: int
    sync: int
    ra: int


class Player(BaseModel):
    sd: list[Score] = []
    dx: list[Score] = []


def compute_ra(constant: float, achievement: float) -> int:
    base_ra = 22.4
    if achievement < 10:
        base_ra = 0.0
    elif achievement < 20:
        base_ra = 1.6
    elif achievement < 30:
        base_ra = 3.2
    elif achievement < 40:
        base_ra = 4.8
    elif achievement < 50:
        base_ra = 6.4
    elif achievement < 60:
        base_ra = 8.0
    elif achievement < 70:
        base_ra = 9.6
    elif achievement < 75:
        base_ra = 11.2
    elif achievement < 80:
        base_ra = 12.0
    elif achievement < 90:
        base_ra = 13.6
    elif achievement < 94:
        base_ra = 15.2
    elif achievement < 97:
        base_ra = 16.8
    elif achievement < 98:
        base_ra = 20.0
    elif achievement < 99:
        base_ra = 20.3
    elif achievement < 99.5:
        base_ra = 20.8
    elif achievement < 100:
        base_ra = 21.1
    elif achievement < 100.5:
        base_ra = 21.6

    return math.floor(constant * (min(100.5, achievement) / 100) * base_ra)


@functools.lru_cache()
def load_db():
    result = []
    with open("data/db.csv", "r", encoding="utf8", newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            result.append({
                "id": int(row["id"]),
                "level": int(row["level"]),
                "constant": float(row["constant"]),
                "add_version": int(row["add_version"]),
            })
    return result


@functools.lru_cache()
def load_ng_musics():
    with open("data/ng.txt", "r", encoding="utf8") as f:
        return list(map(int, f.readlines()))


def parse_data(data: list):
    player = Player()
    db = load_db()
    ng_musics = load_ng_musics()
    for music in data:
        for detail in music["userMusicDetailList"]:
            music_id = detail["musicId"]
            if music_id >= 100000 or music_id in ng_musics:
                continue
            level = detail["level"] + 1
            try:
                row = next(filter(lambda x: x["id"] == music_id and x["level"] == level, db))
            except StopIteration:
                continue
            score = Score(
                id=music_id,
                level=level,
                constant=row["constant"],
                combo=detail["comboStatus"],
                sync=detail["syncStatus"],
                ra=compute_ra(row["constant"], detail["achievement"] / 10000)
            )
            if row["add_version"] == CURRENT_VERSION:
                player.dx.append(score)
            else:
                player.sd.append(score)
    player.dx.sort(key=lambda x: x.ra, reverse=True)
    player.sd.sort(key=lambda x: x.ra, reverse=True)
    return player


def compute_best(player: Player):
    b35 = sum(map(lambda x: x.ra, player.sd[:min(35, len(player.sd))]))
    b15 = sum(map(lambda x: x.ra, player.dx[:min(15, len(player.dx))]))
    return b35, b15


def compute_bad(player: Player):
    filtered_sd = list(filter(lambda x: x.ra > 0, player.sd))
    filtered_sd.sort(key=lambda x: x.ra)
    filtered_dx = list(filter(lambda x: x.ra > 0, player.dx))
    filtered_dx.sort(key=lambda x: x.ra)
    b35 = sum(map(lambda x: x.ra, filtered_sd[:min(35, len(filtered_sd))]))
    b15 = sum(map(lambda x: x.ra, filtered_dx[:min(15, len(filtered_dx))]))
    return b35, b15


def main():
    with open(sys.argv[1], "r", encoding="utf8") as f:
        js = json.load(f)
    player = parse_data(js)
    b35, b15 = compute_best(player)
    print("b35", b35)
    print("b15", b15)
    print("b50", b35 + b15)
    
    bad35, bad15 = compute_bad(player)
    print("bad35", bad35)
    print("bad15", bad15)
    print("bad50", bad35 + bad15)


if __name__ == "__main__":
    main()
