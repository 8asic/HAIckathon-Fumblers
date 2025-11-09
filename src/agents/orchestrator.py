# src/agents/orchestrator.py

import asyncio
from typing import Dict, Any, List
from src.agents.detector import BiasDetector
from src.agents.rewriter import ArticleRewriter
from src.agents.explainer import BiasExplainer


class BiasAnalysisOrchestrator:
    def __init__(self, max_concurrent: int = 2):
        self.detector = BiasDetector()
        self.rewriter = ArticleRewriter()
        self.explainer = BiasExplainer()
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def analyze_article(self, article_text: str, original_title: str = "", source: str = "unknown") -> Dict[str, Any]:
        async with self.semaphore:
            bias_analysis = await self.detector.detect_biases(article_text)
            neutral_text = await self.rewriter.rewrite_neutral(article_text, bias_analysis)
            
            neutral_title = original_title
            if original_title and bias_analysis.get('overall_bias_score', 0) > 20:
                neutral_title = await self.rewriter.rewrite_title_neutral(original_title, bias_analysis)
            
            explanation = await self.explainer.explain_biases(bias_analysis)
            
            return {
                "original_text": article_text,
                "original_title": original_title,
                "neutral_version": neutral_text,
                "neutral_title": neutral_title,
                "analysis": bias_analysis,
                "explanation": explanation,
                "source": source,
                "rewrite_quality": self._assess_rewrite_quality(article_text, neutral_text)
            }
    
    async def analyze_multiple_articles(self, articles: List[Dict]) -> List[Dict[str, Any]]:
        tasks = []
        for article in articles:
            task = self.analyze_article(
                article_text=article.get('body', ''),  # ← CHANGE 'content' to 'body'
                original_title=article.get('title', ''),
                source=article.get('source', 'unknown')
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({"error": str(result)})
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _assess_rewrite_quality(self, original: str, rewritten: str) -> str:
        if original == rewritten:
            return "no_change"
        
        original_words = len(original.split())
        rewritten_words = len(rewritten.split())
        
        if abs(original_words - rewritten_words) > original_words * 0.5:
            return "significant_change"
        
        return "moderate_change"