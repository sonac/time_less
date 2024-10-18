import datetime
from pathlib import Path

from peewee import *

db_file =  Path(__file__).parent / "db" / "time_less.db"

db = SqliteDatabase(db_file)

class BaseModel(Model):
    class Meta:
        database = db


class Article(BaseModel):
    title = CharField(unique=True)
    link = TextField()
    text = TextField()
    date = DateField()

class Subscriber(BaseModel):
    chat_id = BigIntegerField(unique=True)
    subscribed_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        table_name = 'subscribers'

def create_new_article(article: Article):
    try:
        db.connect(reuse_if_open=True)
        article, created = Article.get_or_create(title=article.title, link=article.link, text=article.text, date=article.date)
        if created:
            print(f"Article {article.title} was created")
        else:
            print(f"Article {article.title} already exists")
    except Exception as e:
        print(f"an error occured when creating a new article: {e}")
    finally:
        if not db.is_closed():
            db.close()

def get_all_articles():
    try:
        db.connect(reuse_if_open=True)
        articles = Article.select()
        return articles
    except Exception as e:
        print(f"an error occurred when getting all articles: {e}")
    finally:
        if not db.is_closed():
            db.close()