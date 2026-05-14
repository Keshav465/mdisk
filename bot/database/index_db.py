import motor.motor_asyncio
from bot.config import Config
import re

class IndexDB:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Config.DATABASE_URL)
        self.db = self.client[Config.DATABASE_NAME]
        self.collection = self.db['indexed_files']

    async def save_file(self, file_data):
        """Save a file's metadata to the database."""
        # Use message_id and chat_id as unique identifier
        query = {
            'message_id': file_data['message_id'],
            'chat_id': file_data['chat_id']
        }
        await self.collection.update_one(query, {'$set': file_data}, upsert=True)

    async def save_files_bulk(self, files_list):
        """Save multiple files to the database efficiently."""
        if not files_list:
            return
        
        from pymongo import UpdateOne
        operations = []
        for file_data in files_list:
            query = {
                'message_id': file_data['message_id'],
                'chat_id': file_data['chat_id']
            }
            operations.append(UpdateOne(query, {'$set': file_data}, upsert=True))
        
        if operations:
            await self.collection.bulk_write(operations)

    async def search_files(self, query_str, offset=0, limit=Config.LIMIT):
        """Search files using MongoDB text search or regex."""
        # Clean query
        query_str = re.sub(r'[^a-zA-Z0-9 ]', ' ', query_str).strip()
        if not query_str:
            return [], 0

        # Create regex pattern for fuzzy-like matching
        pattern = ' '.join([f'(?=.*{re.escape(word)})' for word in query_str.split()])
        
        mongo_query = {
            'file_name': {'$regex': pattern, '$options': 'i'}
        }
        
        cursor = self.collection.find(mongo_query).skip(offset).limit(limit)
        results = await cursor.to_list(length=limit)
        total_results = await self.collection.count_documents(mongo_query)
        
        return results, total_results

    async def total_files(self):
        """Get total number of indexed files."""
        return await self.collection.count_documents({})

    async def delete_all_files(self):
        """Clear the entire index."""
        await self.collection.delete_many({})

index_db = IndexDB()
