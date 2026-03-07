"""
TF-IDF based project matching implementation.
"""

import re
import math
from collections import Counter, defaultdict
from typing import List, Dict, Any, Set
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from loguru import logger

from .base_matcher import BaseProjectMatcher, MatchResult, JobContext
from app.models import Project

class TFIDFProjectMatcher(BaseProjectMatcher):
    """TF-IDF based project matching with keyword analysis."""
    
    def __init__(self):
        self.vectorizer = None
        self.stop_words = self._get_custom_stop_words()
        self.tech_keywords = self._load_technology_keywords()
        
    def match_projects(
        self, 
        projects: List[Project], 
        job_context: JobContext,
        max_results: int = 5
    ) -> List[MatchResult]:
        """Match projects using TF-IDF similarity with keyword analysis."""
        
        if not projects:
            return []
        
        logger.info(f"Matching {len(projects)} projects to job: {job_context.title}")
        
        # Prepare documents for TF-IDF
        project_documents = self._prepare_project_documents(projects)
        job_document = self._prepare_job_document(job_context)
        
        # Calculate TF-IDF similarities
        similarity_scores = self._calculate_tfidf_similarity(
            project_documents, job_document
        )
        
        # Calculate keyword matches
        keyword_matches = self._calculate_keyword_matches(projects, job_context)
        
        # Calculate technology matches
        tech_matches = self._calculate_technology_matches(projects, job_context)
        
        # Combine scores and create results
        results = []
        for i, project in enumerate(projects):
            
            # Weighted scoring
            tfidf_score = similarity_scores[i]
            keyword_score = keyword_matches[i]['score']
            tech_score = tech_matches[i]['score']
            
            # Combine scores with weights
            confidence_score = (
                tfidf_score * 0.4 +          # TF-IDF similarity
                keyword_score * 0.35 +       # Keyword matching
                tech_score * 0.25            # Technology matching
            )
            
            # Create explanation
            explanation = {
                "algorithm": "TF-IDF + Keyword Matching",
                "tfidf_similarity": round(tfidf_score, 3),
                "keyword_match_score": round(keyword_score, 3),
                "technology_match_score": round(tech_score, 3),
                "weighted_final_score": round(confidence_score, 3),
                "matching_details": {
                    "matched_keywords": keyword_matches[i]['keywords'],
                    "matched_technologies": tech_matches[i]['technologies'],
                    "missing_required_skills": tech_matches[i]['missing_required'],
                }
            }
            
            # Extract all matching keywords for easy access
            all_matching_keywords = (
                keyword_matches[i]['keywords'] + 
                tech_matches[i]['technologies']
            )
            
            similarity_breakdown = {
                "content_similarity": tfidf_score,
                "keyword_relevance": keyword_score,
                "technical_alignment": tech_score
            }
            
            result = MatchResult(
                project=project,
                confidence_score=confidence_score,
                explanation=explanation,
                matching_keywords=all_matching_keywords,
                similarity_breakdown=similarity_breakdown
            )
            
            results.append(result)
        
        # Sort by confidence score and return top results
        results.sort(key=lambda x: x.confidence_score, reverse=True)
        return results[:max_results]
    
    def _prepare_project_documents(self, projects: List[Project]) -> List[str]:
        """Prepare project text documents for TF-IDF analysis."""
        documents = []
        
        for project in projects:
            # Combine all project text fields
            text_parts = [
                project.title or "",
                project.description or "",
                project.category or "",
                " ".join(project.technologies or []),
                " ".join(project.skills_demonstrated or []),
            ]
            
            document = " ".join(text_parts).lower()
            # Clean and normalize text
            document = re.sub(r'[^\w\s]', ' ', document)
            document = re.sub(r'\s+', ' ', document).strip()
            
            documents.append(document)
        
        return documents
    
    def _prepare_job_document(self, job_context: JobContext) -> str:
        """Prepare job description document for TF-IDF analysis."""
        text_parts = [
            job_context.title or "",
            job_context.description or "",
            job_context.category or "",
            " ".join(job_context.required_skills or []),
            " ".join(job_context.preferred_skills or [])
        ]
        
        document = " ".join(text_parts).lower()
        # Clean and normalize text
        document = re.sub(r'[^\w\s]', ' ', document)
        document = re.sub(r'\s+', ' ', document).strip()
        
        return document
    
    def _calculate_tfidf_similarity(
        self, 
        project_documents: List[str], 
        job_document: str
    ) -> List[float]:
        """Calculate TF-IDF cosine similarity between projects and job."""
        
        # Combine all documents for vectorization
        all_documents = project_documents + [job_document]
        
        # Create TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            stop_words=list(self.stop_words),
            max_features=5000,
            ngram_range=(1, 2),  # Include bigrams
            min_df=1,
            max_df=0.8
        )
        
        # Fit and transform documents
        tfidf_matrix = self.vectorizer.fit_transform(all_documents)
        
        # Calculate cosine similarity between projects and job
        job_vector = tfidf_matrix[-1]  # Last document is the job
        project_vectors = tfidf_matrix[:-1]  # All except last are projects
        
        similarities = cosine_similarity(project_vectors, job_vector.reshape(1, -1))
        
        return similarities.flatten().tolist()
    
    def _calculate_keyword_matches(
        self, 
        projects: List[Project], 
        job_context: JobContext
    ) -> List[Dict[str, Any]]:
        """Calculate keyword-based matches with explanations."""
        
        # Extract keywords from job
        job_keywords = self._extract_keywords(
            f"{job_context.title} {job_context.description}"
        )
        
        results = []
        for project in projects:
            project_text = f"{project.title} {project.description} "
            project_keywords = self._extract_keywords(project_text)
            
            # Find matching keywords
            matching_keywords = list(job_keywords.intersection(project_keywords))
            
            # Calculate score based on matches
            if job_keywords:
                score = len(matching_keywords) / len(job_keywords)
            else:
                score = 0.0
            
            results.append({
                'score': min(score, 1.0),  # Cap at 1.0
                'keywords': matching_keywords,
                'total_job_keywords': len(job_keywords),
                'matched_count': len(matching_keywords)
            })
        
        return results
    
    def _calculate_technology_matches(
        self, 
        projects: List[Project], 
        job_context: JobContext
    ) -> List[Dict[str, Any]]:
        """Calculate technology-specific matches."""
        
        all_job_techs = set()
        required_techs = set([skill.lower() for skill in job_context.required_skills])
        preferred_techs = set([skill.lower() for skill in job_context.preferred_skills])
        all_job_techs.update(required_techs)
        all_job_techs.update(preferred_techs)
        
        results = []
        for project in projects:
            project_techs = set()
            if project.technologies:
                project_techs.update([tech.lower() for tech in project.technologies])
            if project.skills_demonstrated:
                project_techs.update([skill.lower() for skill in project.skills_demonstrated])
            
            # Find matches
            matched_required = project_techs.intersection(required_techs)
            matched_preferred = project_techs.intersection(preferred_techs)
            all_matched = project_techs.intersection(all_job_techs)
            
            # Calculate score
            required_score = len(matched_required) / len(required_techs) if required_techs else 0
            preferred_score = len(matched_preferred) / len(preferred_techs) if preferred_techs else 0
            
            # Weight required skills higher
            tech_score = (required_score * 0.7) + (preferred_score * 0.3)
            
            results.append({
                'score': min(tech_score, 1.0),
                'technologies': list(all_matched),
                'required_matches': list(matched_required),
                'preferred_matches': list(matched_preferred),
                'missing_required': list(required_techs - matched_required)
            })
        
        return results
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract meaningful keywords from text."""
        text = text.lower()
        # Remove special characters and split
        words = re.findall(r'\b\w{3,}\b', text)
        
        # Filter out stop words and common terms
        keywords = set()
        for word in words:
            if (word not in self.stop_words and 
                len(word) >= 3 and 
                not word.isdigit()):
                keywords.add(word)
        
        return keywords
    
    def _get_custom_stop_words(self) -> Set[str]:
        """Get custom stop words for technical content."""
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'how', 
            'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 
            'its', 'let', 'put', 'say', 'she', 'too', 'use', 'will', 'about',
            'after', 'again', 'against', 'all', 'also', 'any', 'because', 'been',
            'before', 'being', 'between', 'both', 'each', 'few', 'from', 'have',
            'here', 'into', 'more', 'most', 'only', 'other', 'some', 'such',
            'than', 'that', 'the', 'their', 'them', 'these', 'they', 'this',
            'through', 'very', 'were', 'what', 'when', 'where', 'which', 'while',
            'with', 'would', 'your'
        }
        return stop_words
    
    def _load_technology_keywords(self) -> Dict[str, List[str]]:
        """Load technology keyword mappings for better matching."""
        return {
            'web_development': [
                'react', 'angular', 'vue', 'javascript', 'typescript', 'html', 'css',
                'node', 'express', 'django', 'flask', 'fastapi', 'spring'
            ],
            'mobile_development': [
                'android', 'ios', 'flutter', 'react-native', 'swift', 'kotlin', 'xamarin'
            ],
            'machine_learning': [
                'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy', 'opencv',
                'keras', 'xgboost', 'ml', 'ai', 'deep-learning', 'neural-network'
            ],
            'data_science': [
                'python', 'r', 'sql', 'tableau', 'powerbi', 'jupyter', 'matplotlib',
                'seaborn', 'plotly', 'statistics', 'analytics'
            ],
            'cloud_devops': [
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'terraform',
                'ansible', 'ci-cd', 'devops'
            ]
        }
    
    def get_algorithm_name(self) -> str:
        return "TF-IDF + Keyword Matching"
    
    def get_algorithm_version(self) -> str:
        return "1.0.0"
