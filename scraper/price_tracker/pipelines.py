import boto3
import json
import os
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
        # Format: raw/tata1mg/2025-12-09/my_product_name.json
        safe_name = item['name'].replace(' ', '_').replace('/', '')[:50]
        # Handle cases where scraped_at might not be in item yet (though it should be)
        date_str = item.get('scraped_at', '').split('T')[0]
        object_key = f"raw/tata1mg/{date_str}/{safe_name}.json"

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
        self.connection = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres"),
            user="user",
            password="password",
            dbname="prices_db"
        )
        self.cur = self.connection.cursor()
        
        # Initialize Schema (Create if not exists)
        self._create_tables()

    def _create_tables(self):
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name TEXT,
                url TEXT UNIQUE,
                image_url TEXT,
                pack_size TEXT,
                rating TEXT,
                rating_count TEXT,
                category TEXT,
                description TEXT,
                key_ingredients TEXT,
                safety_information TEXT,
                directions_for_use TEXT
            );
        """)
        
        # Add columns if they don't exist (for existing tables)
        for col in ['description', 'key_ingredients', 'safety_information', 'directions_for_use']:
            try:
                self.cur.execute(f"ALTER TABLE products ADD COLUMN IF NOT EXISTS {col} TEXT;")
            except psycopg2.Error:
                self.connection.rollback()
            else:
                self.connection.commit()
        
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                id SERIAL PRIMARY KEY,
                product_id INTEGER REFERENCES products(id),
                price DECIMAL(10, 2),
                scraped_at TIMESTAMP
            );
        """)
        self.connection.commit()

    def close_spider(self, spider):
        self.cur.close()
        self.connection.close()

    def process_item(self, item, spider):
        try:
            # INSERT into products (Static Data)
            # We update all fields on conflict to ensure we capture the latest details
            self.cur.execute("""
                INSERT INTO products (
                    name, url, image_url, pack_size, rating, rating_count, category,
                    description, key_ingredients, safety_information, directions_for_use
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO UPDATE SET 
                    name = EXCLUDED.name,
                    image_url = EXCLUDED.image_url,
                    pack_size = EXCLUDED.pack_size,
                    rating = EXCLUDED.rating,
                    rating_count = EXCLUDED.rating_count,
                    category = EXCLUDED.category,
                    description = COALESCE(EXCLUDED.description, products.description),
                    key_ingredients = COALESCE(EXCLUDED.key_ingredients, products.key_ingredients),
                    safety_information = COALESCE(EXCLUDED.safety_information, products.safety_information),
                    directions_for_use = COALESCE(EXCLUDED.directions_for_use, products.directions_for_use)
                RETURNING id;
            """, (
                item['name'], 
                item['url'], 
                item['image_url'],
                item.get('pack_size'),
                item.get('rating'),
                item.get('rating_count'),
                item.get('category'),
                item.get('description'),
                item.get('key_ingredients'),
                item.get('safety_information'),
                item.get('directions_for_use')
            ))
            
            # Get the ID of the product we just touched
            result = self.cur.fetchone()
            if result:
                product_id = result[0]
                
                # INSERT into prices (History Data)
                self.cur.execute("""
                    INSERT INTO prices (product_id, price, scraped_at)
                    VALUES (%s, %s, %s)
                """, (product_id, item['price'], item['scraped_at']))

                # Save changes
                self.connection.commit()
                
        except Exception as e:
            spider.logger.error(f"Error processing item: {e}")
            self.connection.rollback()
            
        return item