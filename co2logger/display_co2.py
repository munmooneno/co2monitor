#!/usr/bin/env python
from pathlib import Path
import sys
import argparse
from datetime import datetime, timedelta
import time

from database import DB
from lib.lcd import LCD


def create_parser(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--dbpath", default="./co2.db")
    parser.add_argument("--fp_csv", default="./co2.db")
    parser.add_argument("--interval_sec", type=int, default=10, help="log interval [sec]")

    args = parser.parse_args(argv[1:])
    return args

def read_data(dbpath, sql='select * from co2'):
    db = DB(dbpath)
    df = db.read_sql_in_df(sql)
    db.close()

    times = [datetime.strptime(date.strip().split(".")[0], "%Y-%m-%d %H:%M:%S") for date in df["date"]]
    co2 = df["co2"].values

    return times, co2


def read_csv(fp):
    res = None
    if fp.exists():
        with open(fp,"r") as f:
            res = f.readlines()
    res  = res[-1].strip().split(",")
    temperature, humidity = float(res[0]),float(res[1])

    return temperature, humidity


def update_display(lcd, time,co2, temp, humid):
    row0 =f"{time:%H:%M:%S}   {temp:.1f}C"
    row1= f"{co2[-1]:.1f}ppm  {humid:.1f}%"
    lcd.show(row0,row=0)
    lcd.show(row1,row=1)


def main(args):
    gpio_display=None
    gpio_display=17

    print("init lcd")
    lcd = LCD(gpio_id=gpio_display)
    p_csv = Path(args.fp_csv)

    interval = timedelta(seconds=args.interval_sec)
    last = datetime.now()-interval
    
    try:
        while True:
            # set sql conditions
            now = datetime.now()
            cnd = (now - timedelta(minutes=5)).date()
            sql = f"select * from co2 where date > '{cnd}'"

            # read data in every interval[sec]
            if now-last>interval:
                times, co2 = read_data(args.dbpath, sql)
                temp, humid = read_csv(p_csv)
                last = now            

            # display
            update_display(lcd, now, co2, temp, humid)
            if args.interval_sec <= 0:
                break

            time.sleep(1)

    finally:
        lcd.clear()


if __name__ == "__main__":
    args = create_parser(sys.argv)
    main(args)
