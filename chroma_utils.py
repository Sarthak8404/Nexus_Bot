import chromadb
import os
from dotenv import load_dotenv
import json
import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize ChromaDB client with persistence
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Define a fixed vocabulary for consistent dimensions
FIXED_VOCABULARY = [
    'category', 'description', 'price', 'availability', 'imageurl',
    'name', 'brand', 'rating', 'reviews', 'specifications',
    'features', 'details', 'information', 'product', 'business',
    'data', 'analysis', 'insights', 'metrics', 'performance',
    'sales', 'revenue', 'customers', 'market', 'trends'
]

# Initialize TF-IDF vectorizer with fixed vocabulary
vectorizer = TfidfVectorizer(
    vocabulary=dict(zip(FIXED_VOCABULARY, range(len(FIXED_VOCABULARY)))),
    max_features=25  # Increased to accommodate more business-related terms
)

def get_user_collection_name(user_id):
    """Generate a unique collection name for a user."""
    return f"user_{user_id}_data"

def get_embedding(text):
    """Generate embedding using TF-IDF vectorization with fixed dimension."""
    try:
        # Convert text to TF-IDF vector
        tfidf_matrix = vectorizer.fit_transform([text])
        # Convert to dense array
        embedding = tfidf_matrix.toarray()[0]
        
        # Ensure the embedding has exactly 25 dimensions
        if len(embedding) < 25:
            # Pad with zeros if shorter
            embedding = np.pad(embedding, (0, 25 - len(embedding)))
        elif len(embedding) > 25:
            # Truncate if longer
            embedding = embedding[:25]
            
        # Normalize the embedding
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
            
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        return None

def store_data_in_chroma(data, user_id):
    """Store data in ChromaDB with embeddings for a specific user."""
    try:
        if not data:
            logger.error("No data provided to store in ChromaDB")
            return False

        if not user_id:
            logger.error("No user ID provided")
            return False

        logger.info(f"Starting to store {len(data)} items for user {user_id}")

        # Create or get user-specific collection
        collection_name = get_user_collection_name(user_id)
        logger.info(f"Collection name: {collection_name}")
        
        # Always delete existing collection to avoid dimension issues
        try:
            chroma_client.delete_collection(collection_name)
            logger.info(f"Deleted existing collection {collection_name}")
        except Exception as e:
            logger.info(f"No existing collection to delete: {str(e)}")
        
        # Create new collection
        try:
            collection = chroma_client.create_collection(
                name=collection_name,
                metadata={
                    "description": f"Business data collection for user {user_id}",
                    "user_id": user_id,
                    "created_at": time.time()
                }
            )
            logger.info(f"Created new collection {collection_name}")
        except Exception as e:
            logger.error(f"Failed to create collection: {str(e)}")
            return False
        
        # Process each item
        successful_stores = 0
        for i, item in enumerate(data):
            try:
                logger.info(f"Processing item {i+1}/{len(data)}")
                
                # Convert item to string for embedding
                item_text = json.dumps(item, ensure_ascii=False)
                logger.debug(f"Item text length: {len(item_text)}")
                
                # Get embedding
                embedding = get_embedding(item_text)
                if not embedding:
                    logger.warning(f"Failed to get embedding for item {i+1}")
                    continue
                
                logger.info(f"Generated embedding with {len(embedding)} dimensions")
                
                # Create unique ID
                item_id = f"item_{hash(item_text)}_{user_id}"
                
                # Store in ChromaDB
                collection.add(
                    ids=[item_id],
                    embeddings=[embedding],
                    documents=[item_text],
                    metadatas=[{
                        **item,
                        "user_id": user_id,
                        "stored_at": time.time()
                    }]
                )
                successful_stores += 1
                logger.info(f"Successfully stored item {successful_stores} in collection {collection_name}")
                
            except Exception as e:
                logger.error(f"Error processing item {i+1}: {str(e)}")
                continue
        
        logger.info(f"Successfully stored {successful_stores} items in ChromaDB for user {user_id}")
        return successful_stores > 0
        
    except Exception as e:
        logger.error(f"Error storing data in ChromaDB: {str(e)}")
        return False

def query_chroma(query_text, user_id, n_results=5):
    """Query ChromaDB for similar documents for a specific user."""
    try:
        if not user_id:
            logger.error("No user ID provided for query")
            return None

        collection_name = get_user_collection_name(user_id)
        logger.info(f"Querying collection: {collection_name}")
        
        try:
            collection = chroma_client.get_collection(collection_name)
            logger.info(f"Found collection: {collection_name}")
        except Exception as e:
            logger.error(f"Collection not found for user {user_id}: {str(e)}")
            return None
        
        # Get embedding for query
        query_embedding = get_embedding(query_text)
        if not query_embedding:
            logger.error("Failed to get embedding for query")
            return None
            
        logger.info(f"Generated query embedding with {len(query_embedding)} dimensions")
            
        # Query the collection without metadata filtering first
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]  # Include all relevant data
            )
            
            logger.info(f"Raw query results: {results}")
            
            if not results or not results.get('documents') or not results['documents'][0]:
                logger.warning(f"No results found in collection {collection_name}")
                return None
                
            logger.info(f"Successfully queried collection {collection_name} with {len(results.get('documents', [[]])[0])} results")
            
            # Sort results by distance if available
            if results.get('distances'):
                sorted_indices = np.argsort(results['distances'][0])
                results['documents'][0] = [results['documents'][0][i] for i in sorted_indices]
                results['metadatas'][0] = [results['metadatas'][0][i] for i in sorted_indices]
                results['distances'][0] = [results['distances'][0][i] for i in sorted_indices]
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying collection: {str(e)}")
            return None
        
    except Exception as e:
        logger.error(f"Error querying ChromaDB: {str(e)}")
        return None

def delete_user_data(user_id):
    """Delete all data for a specific user from ChromaDB."""
    try:
        if not user_id:
            logger.error("No user ID provided for deletion")
            return False

        collection_name = get_user_collection_name(user_id)
        try:
            chroma_client.delete_collection(collection_name)
            logger.info(f"Successfully deleted collection for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection for user {user_id}: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Error in delete_user_data: {str(e)}")
        return False 