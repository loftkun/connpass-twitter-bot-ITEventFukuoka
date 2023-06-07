import time
import requests
import json
import datetime
import sqlite3
import tweepy

# 検索用のパラメータ
ENDPOINT='https://connpass.com/api/v1/event/'
keyword_or='福岡,fukuoka'
start=1
count=50
order=3 #新着順

# 絞り込み用のパラメータ
address_matcher=['福岡','北九州','fukuoka']

# DB情報
DB_NAME='connpass-ITEventFukuoka.sqlite3'
TABLE_NAME='events'

# Twitter API情報
consumer_key = ""
consumer_secret = ""
access_token = ""
access_token_secret = ""

def search_events():
    response = requests.get(f"{ENDPOINT}?start={start}&count={count}&keyword_or={keyword_or}&order={order}")
    status_code=response.status_code
    print(f"status_code={status_code}")
    if status_code != 200:
        print("exit")
        exit()
    results = json.loads(response.text)
    return results['events']

def filter_events(events):
    results = []
    for event in events:

        # 終了時刻が過去のイベントは除外
        ended_at = event['ended_at'][:-6] # 2023-06-14T20:30:00+09:00 の 末尾の 6文字を 削除し datetime に変換できるようにする
        if datetime.datetime.strptime(ended_at, "%Y-%m-%dT%H:%M:%S") < datetime.datetime.now():
            print(f"continue: old event : {ended_at}")
            continue

        # 住所が空のイベントは除外
        address = event['address']
        if address is None:
            print("continue: address is None")
            continue

        # 住所がマッチしないイベントは除外
        matched = False
        for matcher in address_matcher:
            if matcher in address:
                matched = True
                break
        if not matched:
            print("continue: address is not matched")
            continue

        # DBにあるイベントは除外
        if existsInTable(event['event_id']):
            print("continue: exists in table")
            continue

        print(f"target: {event['event_id']} {event['title']}")
        results.append(event)
    return results

def existsInTable(event_id):
    exists = False
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(f'SELECT * FROM {TABLE_NAME} where event_id = {event_id}')
    rows = c.fetchall()
    for row in rows:
        #print(row)
        exists = True
        break
    conn.close()
    return exists

def tweet_events(events):
    for event in events:
        post_text = create_post_txt(event)
        #exit()
        result = post_tweet(post_text)
        print('---------')
        if result:
            save_event(event)
        time.sleep(1)

def create_post_txt(event):

    # タイトル(必須)
    post_text = event['title']

    # 期間
    start = ""
    end = ""
    try:
        fmt = "%Y-%m-%dT%H:%M:%S"
        started_at = datetime.datetime.strptime(event['started_at'][:-6], fmt)
        ended_at = datetime.datetime.strptime(event['ended_at'][:-6], fmt)

        # 月と日は0埋めしない
        fmt = "%-m/%-d %H:%M"
        start = started_at.strftime(fmt)
        end = ended_at.strftime(fmt)

        # 同日開催ならば end の方には日付は表記しない
        if started_at.strftime("%d") == ended_at.strftime("%d"):
            end = ended_at.strftime("%H:%M")
    except Exception as e:
        print(f"Exception : {e}")

    if start and end:
        post_text += f"\n{start}～{end}"

    # 開催会場
    place = event['place']
    if place:
        post_text += '\n' + place

    # 開催場所
    address = event['address']
    if address:
        post_text += '\n' + address

    # ハッシュタグ
    hash_tag = event['hash_tag']
    if hash_tag:
        post_text += '\n#' + hash_tag

    # connpass.com 上のURL
    post_text += '\n' + event['event_url']

    print(post_text)
    return post_text

def post_tweet(post_text):

    client = tweepy.Client(
        consumer_key=consumer_key, consumer_secret=consumer_secret,
        access_token=access_token, access_token_secret=access_token_secret
    )
    try:
        response = client.create_tweet(
            #text="[メンテナンス中] これは Twitter API v2 のテストです。"
            #text="[メンテナンス終了] Twitter API v2 に移行いたしました。"
            text=post_text
        )
    except Exception as e:
        print(f"Exception : {e}")
        return False
    print(f"tweet : https://twitter.com/user/status/{response.data['id']}")

    return True

def save_event(event):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(f"INSERT INTO {TABLE_NAME}( event_id ) VALUES ( {event['event_id']} )")
    conn.commit()
    conn.close()

def main():
    events = search_events()
    events = filter_events(events)
    tweet_events(events)

if __name__ == "__main__":
    main()
