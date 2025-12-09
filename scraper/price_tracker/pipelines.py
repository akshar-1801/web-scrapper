import boto3
import json
from botocore.client import Config

class MinioPipeline:
    def open_spider(self, spider):
        # 1. Connect to MinIO
        self.s3 = boto3.client(
            's3',
            endpoint_url=spider.settings.get('AWS_ENDPOINT_URL'),
            aws_access_key_id=spider.settings.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=spider.settings.get('AWS_SECRET_ACCESS_KEY'),
            region_name=spider.settings.get('AWS_REGION_NAME'),
            config=Config(signature_version='s3v4')
        )
        self.bucket_name = spider.settings.get('RAW_DATA_BUCKET')

        # 2. Create the bucket if it doesn't exist
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
        except:
            self.s3.create_bucket(Bucket=self.bucket_name)

    def process_item(self, item, spider):
        # 3. Create a unique filename for the object
        # Format: raw/books/2025-12-09/my_book_title.json
        safe_name = item['name'].replace(' ', '_').replace('/', '')[:50]
        date_str = item['scraped_at'].split('T')[0]
        object_key = f"raw/books/{date_str}/{safe_name}.json"

        # 4. Upload to MinIO
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=object_key,
            Body=json.dumps(dict(item))
        )
        
        return item # Pass item to the next pipeline (Postgres)

import psycopg2

class PostgresPipeline:
    def open_spider(self, spider):
        # Connect to the database
        # We use "postgres" as the host because that is the service name in docker-compose
        self.connection = psycopg2.connect(
            host="postgres",
            user="user",
            password="password",
            dbname="prices_db"
        )
        self.cur = self.connection.cursor()

    def close_spider(self, spider):
        self.cur.close()
        self.connection.close()

    def process_item(self, item, spider):
        # Logic: 
        # 1. We check if the product exists in the 'products' table.
        # 2. If it does, we update it. If not, we create it.
        # 3. We always add a new entry to the 'prices' table.
        
        # INSERT into products (Static Data)
        self.cur.execute("""
            INSERT INTO products (name, url, image_url)
            VALUES (%s, %s, %s)
            ON CONFLICT (url) DO UPDATE SET name = EXCLUDED.name
            RETURNING id;
        """, (item['name'], item['url'], item['image_url']))
        
        # Get the ID of the product we just touched
        product_id = self.cur.fetchone()[0]

        # INSERT into prices (History Data)
        self.cur.execute("""
            INSERT INTO prices (product_id, price, scraped_at)
            VALUES (%s, %s, %s)
        """, (product_id, item['price'], item['scraped_at']))

        # Save changes
        self.connection.commit()
        return item