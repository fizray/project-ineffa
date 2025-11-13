"""
Matching and Identification Component
Matches query embeddings against gallery embeddings to identify users
"""

import numpy as np
from typing import List, Optional, Tuple, Dict, Any, NamedTuple
import json
import os
from embedding_extractor import EmbeddingExtractor, EmbeddingManager

class MatchResult(NamedTuple):
    """Result of face matching operation"""
    user_id: str
    user_name: str
    match_score: float
    method: str
    is_match: bool
    confidence_level: str

class MatchingEngine:
    def __init__(self, embedding_manager: EmbeddingManager, 
                 threshold_match: float = 0.70,
                 distance_metric: str = "cosine"):
        """
        Initialize matching engine
        
        Args:
            embedding_manager: Manager for gallery embeddings
            threshold_match: Minimum score for valid match
            distance_metric: Distance metric ('cosine' or 'euclidean')
        """
        self.embedding_manager = embedding_manager
        self.threshold_match = threshold_match
        self.distance_metric = distance_metric
        
    def calculate_distance(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate distance between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Distance score
        """
        if self.distance_metric == "cosine":
            # Cosine similarity (1.0 = identical, 0.0 = completely different)
            similarity = np.dot(embedding1, embedding2)
            # Convert to distance (lower is better)
            distance = 1.0 - similarity
        elif self.distance_metric == "euclidean":
            # Euclidean distance
            distance = np.linalg.norm(embedding1 - embedding2)
        else:
            raise ValueError(f"Unknown distance metric: {self.distance_metric}")
        
        return distance
    
    def calculate_similarity_score(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate similarity score between embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score (0-1, higher is better)
        """
        if self.distance_metric == "cosine":
            # Direct cosine similarity
            similarity = (np.dot(embedding1, embedding2) + 1) / 2
        elif self.distance_metric == "euclidean":
            # Convert euclidean distance to similarity
            distance = np.linalg.norm(embedding1 - embedding2)
            similarity = 1.0 / (1.0 + distance)
        else:
            similarity = 0.0
        
        return float(np.clip(similarity, 0.0, 1.0))
    
    def match_single_embedding(self, query_embedding: np.ndarray) -> MatchResult:
        """
        Match a single query embedding against gallery
        
        Args:
            query_embedding: Query embedding vector
            
        Returns:
            MatchResult with best match information
        """
        all_embeddings = self.embedding_manager.get_all_embeddings()
        
        if not all_embeddings:
            return MatchResult(
                user_id="",
                user_name="Unknown",
                match_score=0.0,
                method="none",
                is_match=False,
                confidence_level="no_users"
            )
        
        best_score = -1.0
        best_user_id = ""
        best_user_name = ""
        best_method = "none"
        
        # Compare against all stored embeddings
        for user_id, user_embeddings in all_embeddings.items():
            user_name = self.embedding_manager.embeddings[user_id]["name"]
            if not user_embeddings:
                continue
            gallery = np.vstack(user_embeddings)
            if self.distance_metric == "cosine":
                sims = np.dot(gallery, query_embedding)
                sims = (sims + 1.0) / 2.0
                user_best_score = float(np.max(sims))
            else:
                diffs = gallery - query_embedding
                dists = np.linalg.norm(diffs, axis=1)
                sims = 1.0 / (1.0 + dists)
                user_best_score = float(np.max(sims))
            if user_best_score > best_score:
                best_score = user_best_score
                best_user_id = user_id
                best_user_name = user_name
                best_method = "max_score"
        
        # Determine if it's a valid match
        is_match = best_score >= self.threshold_match
        
        # Determine confidence level
        if not is_match:
            confidence_level = "no_match"
        elif best_score >= 0.9:
            confidence_level = "high"
        elif best_score >= 0.8:
            confidence_level = "medium"
        else:
            confidence_level = "low"
        
        return MatchResult(
            user_id=best_user_id if is_match else "",
            user_name=best_user_name if is_match else "Unknown",
            match_score=best_score,
            method=best_method,
            is_match=is_match,
            confidence_level=confidence_level
        )
    
    def match_multiple_embeddings(self, query_embeddings: List[np.ndarray]) -> List[MatchResult]:
        """
        Match multiple query embeddings and return all results
        
        Args:
            query_embeddings: List of query embedding vectors
            
        Returns:
            List of MatchResult objects
        """
        results = []
        for embedding in query_embeddings:
            result = self.match_single_embedding(embedding)
            results.append(result)
        return results
    
    def verify_user_identity(self, user_id: str, query_embedding: np.ndarray) -> bool:
        """
        Verify if query embedding matches a specific user
        
        Args:
            user_id: User ID to verify against
            query_embedding: Query embedding vector
            
        Returns:
            True if verification successful
        """
        user_embeddings = self.embedding_manager.get_user_embeddings(user_id)
        
        if not user_embeddings:
            return False
        
        # Calculate similarity with all user embeddings
        scores = []
        for gallery_embedding in user_embeddings:
            score = self.calculate_similarity_score(query_embedding, gallery_embedding)
            scores.append(score)
        
        # Use the best score for verification
        best_score = max(scores) if scores else 0.0
        
        return best_score >= self.threshold_match
    
    def get_threshold_analysis(self) -> Dict[str, Any]:
        """
        Analyze current threshold effectiveness
        
        Returns:
            Dictionary with threshold analysis
        """
        all_embeddings = self.embedding_manager.get_all_embeddings()
        
        # Collect all similarities
        intra_user_similarities = []  # Same person
        inter_user_similarities = []  # Different people
        
        user_ids = list(all_embeddings.keys())
        
        # Intra-user similarities (same person)
        for user_id, embeddings in all_embeddings.items():
            for i, emb1 in enumerate(embeddings):
                for j, emb2 in enumerate(embeddings):
                    if i != j:  # Different images of same person
                        sim = self.calculate_similarity_score(emb1, emb2)
                        intra_user_similarities.append(sim)
        
        # Inter-user similarities (different people)
        for i, user1 in enumerate(user_ids):
            for j, user2 in enumerate(user_ids):
                if i < j:  # Different people
                    emb1_list = all_embeddings[user1]
                    emb2_list = all_embeddings[user2]
                    
                    for emb1 in emb1_list:
                        for emb2 in emb2_list:
                            sim = self.calculate_similarity_score(emb1, emb2)
                            inter_user_similarities.append(sim)
        
        # Calculate statistics
        stats = {
            "threshold_current": self.threshold_match,
            "intra_user_stats": {
                "mean": float(np.mean(intra_user_similarities)) if intra_user_similarities else 0.0,
                "std": float(np.std(intra_user_similarities)) if intra_user_similarities else 0.0,
                "min": float(np.min(intra_user_similarities)) if intra_user_similarities else 0.0,
                "max": float(np.max(intra_user_similarities)) if intra_user_similarities else 0.0,
                "count": len(intra_user_similarities)
            },
            "inter_user_stats": {
                "mean": float(np.mean(inter_user_similarities)) if inter_user_similarities else 0.0,
                "std": float(np.std(inter_user_similarities)) if inter_user_similarities else 0.0,
                "min": float(np.min(inter_user_similarities)) if inter_user_similarities else 0.0,
                "max": float(np.max(inter_user_similarities)) if inter_user_similarities else 0.0,
                "count": len(inter_user_similarities)
            }
        }
        
        return stats
    
    def suggest_optimal_threshold(self) -> float:
        """
        Suggest optimal threshold based on current data
        
        Returns:
            Suggested threshold value
        """
        stats = self.get_threshold_analysis()
        
        intra_mean = stats["intra_user_stats"]["mean"]
        inter_mean = stats["inter_user_stats"]["mean"]
        
        # Simple heuristic: midpoint between means with some margin
        optimal_threshold = (intra_mean + inter_mean) / 2
        
        # Ensure threshold is within reasonable bounds
        optimal_threshold = max(0.5, min(0.9, optimal_threshold))
        
        return optimal_threshold

class EnrollmentMatcher:
    """
    Specialized matcher for enrollment verification
    """
    
    def __init__(self, embedding_manager: EmbeddingManager, 
                 enrollment_threshold: float = 0.75):
        """
        Initialize enrollment matcher
        
        Args:
            embedding_manager: Manager for gallery embeddings
            enrollment_threshold: Threshold for enrollment verification
        """
        self.embedding_manager = embedding_manager
        self.enrollment_threshold = enrollment_threshold
    
    def is_face_enrolled(self, user_id: str) -> bool:
        """
        Check if a user ID already exists in the gallery
        
        Args:
            user_id: User ID to check
            
        Returns:
            True if user is already enrolled
        """
        return user_id in self.embedding_manager.embeddings
    
    def find_duplicate_user(self, query_embedding: np.ndarray) -> Optional[str]:
        """
        Find if query embedding matches any existing user
        
        Args:
            query_embedding: Query embedding vector
            
        Returns:
            User ID if duplicate found, None otherwise
        """
        engine = MatchingEngine(self.embedding_manager)
        result = engine.match_single_embedding(query_embedding)
        
        if result.is_match and result.match_score >= self.enrollment_threshold:
            return result.user_id
        
        return None
    
    def verify_enrollment_quality(self, user_embeddings: List[np.ndarray]) -> Dict[str, Any]:
        """
        Verify quality of enrollment embeddings
        
        Args:
            user_embeddings: List of embeddings for a user
            
        Returns:
            Quality analysis results
        """
        if len(user_embeddings) < 2:
            return {
                "quality": "insufficient",
                "reason": "Need at least 2 embeddings",
                "score": 0.0
            }
        
        # Calculate similarities between all pairs
        similarities = []
        for i, emb1 in enumerate(user_embeddings):
            for j, emb2 in enumerate(user_embeddings):
                if i < j:
                    # Use cosine similarity for quality check
                    dot_product = np.dot(emb1, emb2)
                    similarity = (dot_product + 1) / 2
                    similarities.append(similarity)
        
        if not similarities:
            return {
                "quality": "error",
                "reason": "Could not calculate similarities",
                "score": 0.0
            }
        
        # Calculate quality metrics
        mean_similarity = np.mean(similarities)
        std_similarity = np.std(similarities)
        
        # Quality assessment
        if mean_similarity >= 0.8 and std_similarity <= 0.1:
            quality = "excellent"
        elif mean_similarity >= 0.7 and std_similarity <= 0.15:
            quality = "good"
        elif mean_similarity >= 0.6 and std_similarity <= 0.2:
            quality = "acceptable"
        else:
            quality = "poor"
        
        return {
            "quality": quality,
            "mean_similarity": mean_similarity,
            "std_similarity": std_similarity,
            "num_embeddings": len(user_embeddings),
            "score": mean_similarity - std_similarity  # Higher is better
        }

# Test function
if __name__ == "__main__":
    # Test matching engine
    manager = EmbeddingManager("test_embeddings.json")
    
    # Add some test data
    test_embedding1 = np.random.rand(512)
    test_embedding2 = test_embedding1 + 0.1 * np.random.rand(512)  # Similar
    test_embedding3 = np.random.rand(512)  # Different
    
    manager.add_user_embeddings("user_001", "Test User 1", [test_embedding1])
    manager.add_user_embeddings("user_002", "Test User 2", [test_embedding3])
    
    # Test matching
    engine = MatchingEngine(manager, threshold_match=0.6)
    
    # Test with similar embedding
    result1 = engine.match_single_embedding(test_embedding2)
    print(f"Similar embedding match: {result1}")
    
    # Test with different embedding
    result2 = engine.match_single_embedding(test_embedding3)
    print(f"Different embedding match: {result2}")
    
    # Test threshold analysis
    analysis = engine.get_threshold_analysis()
    print(f"Threshold analysis: {analysis}")
    
    # Test enrollment matcher
    enroller = EnrollmentMatcher(manager)
    duplicate = enroller.find_duplicate_user(test_embedding2)
    print(f"Duplicate user: {duplicate}")
    
    # Clean up
    if os.path.exists("test_embeddings.json"):
        os.remove("test_embeddings.json")
