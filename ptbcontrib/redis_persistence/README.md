# Bot persistence via a Redis database
## Notes

    1. `RedisPersistence` class only writes data to the database when the bot is shut down.
    2. As `RedisPersistence` is a subclass of `DictPersistence`, all data set to be stored by the class must be JSON-serializable.

## How to use
### Passing URL of the database
```python
import telegram
from ptbcontrib.redispersistence import RedisPersistence

persistence = RedisPersistence(url = 'redis://username:password@localhost:12345')

updater = telegram.ext.Updater(..., persistence = persistence, ...)
...
```
### Passing existing connection to the database
```python
import telegram
import redis
from ptbcontrib.redispersistence import RedisPersistence

db = redis.Redis(host = 'localhost', password = 'secret123', ssl = True)

updater = telegram.ext.Updater(..., persistence = RedisPersistence(db = db), ...)
...
```

## Requirements

*   `python-telegram-bot>=12.0`
*   `redis-py`

## Authors

*   [Tim Kurdov](https://github.com/schvv31n)  
