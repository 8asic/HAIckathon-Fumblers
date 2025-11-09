#!/usr/bin/env python3
"""
Main orchestrator for Bias Detection System
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from typing import Optional

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

load_dotenv()


class BiasDetectionPipeline:
    def __init__(self):
        from src.services.news_client import NewsClient
        from src.agents.orchestrator import BiasAnalysisOrchestrator
        
        self.news_client = NewsClient()
        self.orchestrator = BiasAnalysisOrchestrator(max_concurrent=3)
    
    async def run_full_pipeline(self, query: Optional[str] = None, article_count: int = 5):
        """
        Run the complete bias detection pipeline.
        """
        print("Starting Bias Detection Pipeline")
        print("=" * 50)
        
        try:
            from src.database.news_db import (
                get_connection_to_news_db, 
                add_news, 
                prepare_data_for_llm,
                add_bias,
                clear_old_articles,
                get_article_stats,
                clear_processed_articles
            )
            
            query_display = f"'{query}'" if query else "all recent articles"
            print(f"Processing parameters - Query: {query_display}, Count: {article_count}")
            
            # Clear any previously processed articles to ensure fresh analysis
            print("Step 1: Clearing previously processed articles...")
            get_connection_to_news_db()
            clear_processed_articles()
            
            print("Step 2: Fetching fresh articles...")
            articles = await self.news_client.fetch_articles(query, article_count)
            
            if not articles:
                print("No articles fetched")
                return None
            
            print(f"Fetched {len(articles)} articles")
            for article in articles:
                print(f"  - {article['title'][:60]}...")
            
            print("Step 3: Storing articles in database...")
            added_count = add_news(data=articles)
            
            if added_count == 0:
                print("No new articles to process (all duplicates)")
                return None
            
            print("Step 4: Preparing articles for analysis...")
            llm_articles = prepare_data_for_llm(limit=article_count, processed_only=True)
            
            if not llm_articles:
                print("No articles prepared for LLM processing")
                return None
            
            print(f"Prepared {len(llm_articles)} articles for bias analysis")
            
            print("Step 5: Analyzing biases with AI agents...")
            analysis_results = await self.orchestrator.analyze_multiple_articles(llm_articles)
            
            # Verify we got real LLM analysis, not fallbacks
            valid_results = self._verify_llm_results(analysis_results)
            
            print("Step 6: Storing analysis results...")
            db_ready_results = self._format_results_for_db(valid_results, llm_articles)
            
            if db_ready_results:
                add_bias(db_ready_results)
            
            print("Step 7: Generating summary...")
            self._display_summary(valid_results)
            get_article_stats()
            
            return valid_results
            
        except ImportError as e:
            print(f"Import error: {e}")
            print("Please ensure all required functions are implemented in the database module")
            return None
        except Exception as e:
            print(f"Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _verify_llm_results(self, analysis_results):
        """Just verify, don't filter out fallbacks."""
        for result in analysis_results:
            if "error" not in result:
                analysis = result.get("analysis", {})
                if analysis.get("overall_bias_score", 0) == 50:
                    print(f"⚠️  Fallback analysis for: {result.get('original_title', 'Unknown')[:50]}...")
                else:
                    print(f"✅ Real analysis for: {result.get('original_title', 'Unknown')[:50]}...")
        
        # Return all results, even fallbacks
        return analysis_results
    
    def _format_results_for_db(self, analysis_results, original_articles):
        """Format analysis results for database storage."""
        db_results = []
        
        for i, result in enumerate(analysis_results):
            if "error" in result or not result:
                print(f"Skipping invalid result for article {i}")
                continue
                
            original_title = original_articles[i]["title"] if i < len(original_articles) else "Unknown"
            analysis = result.get("analysis", {})
            neutral_version = result.get("neutral_version", "")
            
            # Ensure we have valid data to store
            if not analysis or not neutral_version:
                print(f"Skipping empty analysis for: {original_title[:50]}...")
                continue
            
            # Convert analysis dict to string
            bias_string = str(analysis) if analysis else "{}"
            
            db_results.append({
                "title": original_title,
                "bias": bias_string,
                "rewritten_article": neutral_version
            })
        
        return db_results
    
    def _display_summary(self, analysis_results):
        """Display a summary of the analysis results."""
        successful_analyses = [r for r in analysis_results if "error" not in r]
        
        print(f"Articles Processed: {len(analysis_results)}")
        print(f"Successful Analyses: {len(successful_analyses)}")
        print(f"Failed Analyses: {len(analysis_results) - len(successful_analyses)}")
        
        if successful_analyses:
            print("Bias Scores Summary:")
            for i, result in enumerate(successful_analyses):
                analysis = result.get("analysis", {})
                original_title = result.get("original_title", "Unknown")[:60]
                bias_score = analysis.get("overall_bias_score", 0)
                
                # Highlight if this looks like real analysis
                analysis_type = " REAL" if bias_score != 50 else "  FALLBACK"
                
                print(f"  {i+1}. {analysis_type} '{original_title}...'")
                print(f"     Overall Bias: {bias_score}/100")
                print(f"     Emotional: {analysis.get('emotional_bias_score', 0)}/100")
                print(f"     Framing: {analysis.get('framing_bias_score', 0)}/100")
                print(f"     Omission: {analysis.get('omission_bias_score', 0)}/100")
                
                # Show biased phrases count if available
                biased_phrases = analysis.get("biased_phrases", [])
                if biased_phrases:
                    print(f"     Biased Phrases Found: {len(biased_phrases)}")
                
                # Show rewrite quality
                original_len = len(result.get("original_text", ""))
                rewritten_len = len(result.get("neutral_version", ""))
                print(f"     Original: {original_len} chars, Rewritten: {rewritten_len} chars")


async def main():
    """Main entry point with configurable parameters."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bias Detection Pipeline')
    parser.add_argument('--query', type=str, help='Search query for articles (optional)')
    parser.add_argument('--count', type=int, default=3, help='Number of articles to process')
    
    args = parser.parse_args()
    
    print("Bias Detection System")
    print("=" * 40)
    
    required_vars = ['GEMINI_API_KEY', 'GROQ_API_KEY', 'NEWSAPI_AI_KEY', 'NEWS_API_KEY']
    print("Environment Check:")
    for var in required_vars:
        if os.getenv(var):
            print(f"  SET: {var}")
        else:
            print(f"  MISSING: {var}")
    
    pipeline = BiasDetectionPipeline()
    
    results = await pipeline.run_full_pipeline(
        query=args.query,
        article_count=args.count
    )
    
    if results:
        print("Pipeline completed successfully")
        print("Results stored in: data/databases/news.db")
        
        # Final verification
        real_analyses = [r for r in results if r.get("analysis", {}).get("overall_bias_score", 0) != 50]
        if len(real_analyses) == len(results):
            print(" ALL analyses used real LLM (no fallbacks)")
        else:
            print(f"  Some analyses used fallbacks: {len(real_analyses)}/{len(results)} real")
    else:
        print("Pipeline failed")


if __name__ == "__main__":
    asyncio.run(main())