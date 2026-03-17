import chromadb
from chromadb.config import Settings
import logging
from typing import List, Dict, Any, Optional
from config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME
from models import RegulatoryDocument, RegulatorySection

logger = logging.getLogger(__name__)


class ChromaRegulatoryClient:
    """
    ChromaDB client for regulatory document storage and retrieval.
    Handles embedding and similarity search.
    """
    
    def __init__(self, persist_directory: str = None, collection_name: str = None):
        self.persist_directory = persist_directory or str(CHROMA_PERSIST_DIR)
        self.collection_name = collection_name or CHROMA_COLLECTION_NAME
        self.client = None
        self.collection = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client and collection"""
        try:
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Try to get existing collection, create if doesn't exist
            try:
                self.collection = self.client.get_collection(self.collection_name)
                logger.info(f"Loaded existing collection: {self.collection_name}")
            except Exception:  # Catch all exceptions for "not found"
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def add_documents(self, documents: List[RegulatoryDocument]):
        """
        Add regulatory documents to the collection.
        """
        if not documents:
            logger.warning("No documents to add")
            return
        
        ids = []
        metadatas = []
        documents_text = []
        
        for i, doc in enumerate(documents):
            doc_id = f"{doc.drug_name}_{doc.section}_{i}_{hash(doc.content[:50])}"
            ids.append(doc_id)
            
            metadata = {
                "drug_name": doc.drug_name,
                "section": doc.section.value,
                "source": doc.source
            }
            # Add any additional metadata
            if doc.metadata:
                metadata.update(doc.metadata)
            
            metadatas.append(metadata)
            documents_text.append(doc.content)
        
        try:
            self.collection.add(
                ids=ids,
                documents=documents_text,
                metadatas=metadatas
            )
            logger.info(f"Added {len(documents)} documents to ChromaDB")
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    def search(self, query: str, n_results: int = 10, 
               filter_dict: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        """
        try:
            where = filter_dict or {}
            
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where if where else None
            )
            
            # Format results
            formatted_results = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if results['distances'] else None
                    })
            
            logger.debug(f"Search for '{query}' returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def search_by_drug(self, drug_name: str, section: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search specifically for a drug name with optional section filter.
        """
        filter_dict = {"drug_name": drug_name.lower()}
        if section:
            filter_dict["section"] = section
        
        return self.search(
            query=drug_name,
            n_results=20,
            filter_dict=filter_dict
        )
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        try:
            count = self.collection.count()
            
            # Get unique drugs and sections
            # This is a simplified approach - in production you might want to track this metadata
            return {
                "total_documents": count,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
    
    def delete_collection(self):
        """Delete the current collection"""
        try:
            self.client.delete_collection(self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
            self.collection = None
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = ChromaRegulatoryClient()
    print(client.get_collection_stats())