# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from sqlalchemy.orm import sessionmaker
from redfin_test.models import Search_DB, db_connect, create_table

class RedfinTestPipeline(object):
    def __init__(self):
        """
        Initializes database connection and sessionmaker.
        Creates deals table.
        """
        engine = db_connect()
        create_table(engine)
        self.Session = sessionmaker(bind=engine)

    def process_item(self, item, spider):
        """Save deals in the database.

        This method is called for every item pipeline component.
        """
        session = self.Session()
        result = Search_DB()
        result.price = item["price"]
        result.street = item["street"]
        result.zipcode = item["zipcode"]
        try:
            session.add(result)
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

        return item