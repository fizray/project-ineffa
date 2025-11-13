"""
Embedding Extraction Component
Converts face images to numerical embeddings using FaceNet model
"""

import cv2
import numpy as np
from facenet_pytorch import InceptionResnetV1, MTCNN, fixed_image_standardization
import torch
from typing import List, Optional, Tuple, Dict, Any
import os
from PIL import Image

class EmbeddingExtractor:
    def __init__(self, model_name: str = "vgg_face2", device: str = None, config: Dict[str, Any] = None):
        """
        Initialize embedding extractor with FaceNet model
        
        Args:
            model_name: Model variant ('vgg_face2' or 'casia-webface')
            device: Computation device ('cpu' or 'cuda'). If None, use config or auto-detect
            config: Configuration dict containing GPU settings
        """
        # Determine device based on config or auto-detection
        if device is None:
            if config and config.get('enable_gpu', False):
                if torch.cuda.is_available():
                    device = "cuda"
                    print(f"GPU enabled in config and detected: {torch.cuda.get_device_name(0)}")
                else:
                    device = "cpu"
                    print("GPU enabled in config but not available, using CPU")
            elif torch.cuda.is_available():
                device = "cuda"
                print(f"GPU auto-detected: {torch.cuda.get_device_name(0)}")
            else:
                device = "cpu"
                print("Using CPU for embedding extraction")
        
        self.model_name = model_name
        self.device = device
        
        # Load pre-trained FaceNet model
        if model_name == "vgg_face2":
            self.model = InceptionResnetV1(pretrained='vggface2').eval()
        else:
            self.model = InceptionResnetV1(pretrained='casia-webface').eval()
        self.model = self.model.to(device)
        self.use_fp16 = False
        try:
            if self.device == "cuda":
                import torch.backends.cudnn as cudnn
                cudnn.benchmark = True
                self.model = self.model.half()
                self.use_fp16 = True
        except Exception:
            pass
        
        # Preprocessing parameters
        self.image_size = 160  # FaceNet standard input size
        self.embedding_dim = 512  # Output embedding dimension
        
    def preprocess_face(self, face_image: np.ndarray) -> Optional[torch.Tensor]:
        """
        Preprocess face image for embedding extraction
        
        Args:
            face_image: Face image (BGR format, any size)
            
        Returns:
            Preprocessed tensor or None if preprocessing fails
        """
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            
            # Resize to standard size
            resized = cv2.resize(rgb_image, (self.image_size, self.image_size))
            
            tensor = torch.from_numpy(resized).permute(2, 0, 1).contiguous().float().div(255.0).unsqueeze(0)
            tensor = fixed_image_standardization(tensor)
            if self.use_fp16:
                tensor = tensor.half()
            return tensor.to(self.device)
            
        except Exception as e:
            print(f"Face preprocessing failed: {e}")
            return None
    
    def extract_embedding(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract embedding from a single face image
        
        Args:
            face_image: Face image (BGR format)
            
        Returns:
            512-dimensional embedding vector or None if extraction fails
        """
        try:
            # Preprocess face
            preprocessed = self.preprocess_face(face_image)
            if preprocessed is None:
                return None
            
            # Extract embedding
            with torch.no_grad():
                embedding = self.model(preprocessed)
                embedding = embedding.squeeze().cpu().numpy()
            
            # L2 normalize the embedding
            embedding = self.l2_normalize(embedding)
            
            return embedding
            
        except Exception as e:
            print(f"Embedding extraction failed: {e}")
            return None
    
    def extract_embeddings_batch(self, face_images: List[np.ndarray]) -> List[Optional[np.ndarray]]:
        """
        Extract embeddings from multiple face images in batch
        
        Args:
            face_images: List of face images
            
        Returns:
            List of embedding vectors (or None for failed extractions)
        """
        tensors = []
        for face_image in face_images:
            pre = self.preprocess_face(face_image)
            if pre is not None:
                tensors.append(pre)
        if not tensors:
            return [None for _ in face_images]
        batch = torch.cat(tensors, dim=0)
        with torch.no_grad():
            outs = self.model(batch)
        outs = outs.cpu().numpy()
        result = []
        idx = 0
        for face_image in face_images:
            if idx < len(outs):
                emb = outs[idx].squeeze()
                emb = self.l2_normalize(emb)
                result.append(emb)
                idx += 1
            else:
                result.append(None)
        return result
    
    def l2_normalize(self, vector: np.ndarray) -> np.ndarray:
        """
        Apply L2 normalization to a vector
        
        Args:
            vector: Input vector
            
        Returns:
            L2 normalized vector
        """
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray, 
                           method: str = "cosine") -> float:
        """
        Calculate similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            method: Similarity method ('cosine' or 'euclidean')
            
        Returns:
            Similarity score (0-1 for cosine, distance for euclidean)
        """
        try:
            if method == "cosine":
                # Cosine similarity
                dot_product = np.dot(embedding1, embedding2)
                similarity = (dot_product + 1) / 2  # Convert to 0-1 range
            elif method == "euclidean":
                # Euclidean distance (lower is better)
                distance = np.linalg.norm(embedding1 - embedding2)
                similarity = 1.0 / (1.0 + distance)  # Convert to similarity score
            else:
                raise ValueError(f"Unknown similarity method: {method}")
            
            return float(similarity)
            
        except Exception as e:
            print(f"Similarity calculation failed: {e}")
            return 0.0
    
    def save_embedding(self, embedding: np.ndarray, filepath: str):
        """
        Save embedding to file
        
        Args:
            embedding: Embedding vector
            filepath: Path to save the embedding
        """
        try:
            np.save(filepath, embedding)
        except Exception as e:
            print(f"Embedding save failed: {e}")
    
    def load_embedding(self, filepath: str) -> Optional[np.ndarray]:
        """
        Load embedding from file
        
        Args:
            filepath: Path to embedding file
            
        Returns:
            Loaded embedding or None if loading fails
        """
        try:
            embedding = np.load(filepath)
            return embedding
        except Exception as e:
            print(f"Embedding load failed: {e}")
            return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.model_name,
            "device": self.device,
            "image_size": self.image_size,
            "embedding_dim": self.embedding_dim,
            "model_loaded": self.model is not None
        }

class EmbeddingManager:
    """
    Manager for handling embedding storage and retrieval
    """
    
    def __init__(self, embeddings_file: str = "embeddings.json"):
        """
        Initialize embedding manager
        
        Args:
            embeddings_file: Path to embeddings JSON file
        """
        self.embeddings_file = embeddings_file
        self.embeddings = self.load_embeddings()
    
    def load_embeddings(self) -> Dict[str, Any]:
        """
        Load embeddings from JSON file
        
        Returns:
            Dictionary mapping user_id to embedding data
        """
        try:
            if os.path.exists(self.embeddings_file):
                import json
                with open(self.embeddings_file, 'r') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            print(f"Failed to load embeddings: {e}")
            return {}
    
    def save_embeddings(self):
        """Save embeddings to JSON file"""
        try:
            import json
            with open(self.embeddings_file, 'w') as f:
                json.dump(self.embeddings, f, indent=2)
        except Exception as e:
            print(f"Failed to save embeddings: {e}")
    
    def add_user_embeddings(self, user_id: str, user_name: str, 
                          embeddings: List[np.ndarray], metadata: Optional[Dict] = None):
        """
        Add embeddings for a new user
        
        Args:
            user_id: Unique user identifier
            user_name: User's display name
            embeddings: List of embedding vectors
            metadata: Additional metadata (enrollment date, notes, etc.)
        """
        try:
            # Convert numpy arrays to lists for JSON serialization
            embedding_lists = [emb.tolist() for emb in embeddings]
            
            self.embeddings[user_id] = {
                "name": user_name,
                "embeddings": embedding_lists,
                "metadata": metadata or {},
                "enrolled_at": "2025-11-11T08:18:25Z"
            }
            
            self.save_embeddings()
            
        except Exception as e:
            print(f"Failed to add user embeddings: {e}")
    
    def get_user_embeddings(self, user_id: str) -> Optional[List[np.ndarray]]:
        """
        Get embeddings for a specific user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of embedding vectors or None if user not found
        """
        try:
            if user_id not in self.embeddings:
                return None
            
            user_data = self.embeddings[user_id]
            embedding_lists = user_data["embeddings"]
            
            # Convert lists back to numpy arrays
            embeddings = [np.array(emb_list) for emb_list in embedding_lists]
            
            return embeddings
            
        except Exception as e:
            print(f"Failed to get user embeddings: {e}")
            return None
    
    def list_users(self) -> List[str]:
        """
        Get list of enrolled user IDs
        
        Returns:
            List of user IDs
        """
        return list(self.embeddings.keys())
    
    def remove_user(self, user_id: str) -> bool:
        """
        Remove user and all their embeddings
        
        Args:
            user_id: User identifier to remove
            
        Returns:
            True if user was removed, False otherwise
        """
        try:
            if user_id in self.embeddings:
                del self.embeddings[user_id]
                self.save_embeddings()
                return True
            return False
        except Exception as e:
            print(f"Failed to remove user: {e}")
            return False
    
    def get_all_embeddings(self) -> Dict[str, List[np.ndarray]]:
        """
        Get all embeddings organized by user
        
        Returns:
            Dictionary mapping user_id to list of embeddings
        """
        all_embeddings = {}
        
        for user_id in self.embeddings:
            embeddings = self.get_user_embeddings(user_id)
            if embeddings:
                all_embeddings[user_id] = embeddings
        
        return all_embeddings

# Test function
if __name__ == "__main__":
    # Test embedding extractor
    extractor = EmbeddingExtractor(model_name="vgg_face2", device="cpu")
    
    print("Embedding extractor initialized:")
    info = extractor.get_model_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # Test embedding manager
    manager = EmbeddingManager("test_embeddings.json")
    
    # Create test embedding
    test_embedding = np.random.rand(512)
    
    manager.add_user_embeddings("user_001", "Test User", [test_embedding])
    print(f"Added test user. Total users: {len(manager.list_users())}")
    
    # Clean up test file
    if os.path.exists("test_embeddings.json"):
        os.remove("test_embeddings.json")
