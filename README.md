# ITEventFukuoka

Tweet bot for events in Fukuoka obtained from connpass API

## bot

[福岡新着ITイベント（@ITEventFukuoka）](https://twitter.com/ITEventFukuoka)

## SQLite

```sql
sqlite3 connpass-ITEventFukuoka.sqlite3

CREATE TABLE events (
id INTEGER PRIMARY KEY AUTOINCREMENT,
event_id varchar(128),
created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
updated_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime'))
);

CREATE TRIGGER trigger_events_updated_at AFTER UPDATE ON events
BEGIN
UPDATE events SET updated_at = DATETIME('now', 'localtime') WHERE rowid == NEW.rowid;
END;
```

