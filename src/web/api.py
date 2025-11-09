import os
import sys
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio

# Setup project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Bias Detection API",
    description="API for detecting and analyzing bias in news articles",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class AnalysisRequest(BaseModel):
    query: Optional[str] = Field(None, description="Search query for articles")
    article_count: int = Field(3, ge=1, le=20, description="Number of articles to process")

class BiasScore(BaseModel):
    overall_bias_score: int
    emotional_bias_score: int
    framing_bias_score: int
    omission_bias_score: int
    biased_phrases: List[Dict[str, Any]]

class ArticleAnalysis(BaseModel):
    title: str
    analysis: BiasScore
    neutral_version: str
    original_length: int
    rewritten_length: int
    is_real_analysis: bool

class AnalysisResponse(BaseModel):
    status: str
    message: str
    total_articles: int
    successful_analyses: int
    failed_analyses: int
    results: List[ArticleAnalysis]
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    environment_variables: Dict[str, bool]
    timestamp: str

class StatsResponse(BaseModel):
    total_articles: int
    analyzed_articles: int
    pending_articles: int


# Business logic class - USING YOUR EXISTING PIPELINE
class BiasDetectionPipeline:
    def __init__(self):
        from src.services.news_client import NewsClient
        from src.agents.orchestrator import BiasAnalysisOrchestrator
        
        self.news_client = NewsClient()
        self.orchestrator = BiasAnalysisOrchestrator(max_concurrent=3)
    
    async def run_full_pipeline(self, query: Optional[str] = None, article_count: int = 5):
        """
        Run the complete bias detection pipeline - USING YOUR EXISTING LOGIC
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
                return {
                    "status": "error", 
                    "message": "No articles fetched",
                    "results": []
                }
            
            print(f"Fetched {len(articles)} articles")
            for article in articles:
                print(f"  - {article['title'][:60]}...")
            
            print("Step 3: Storing articles in database...")
            added_count = add_news(data=articles)
            
            if added_count == 0:
                return {
                    "status": "warning",
                    "message": "No new articles to process (all duplicates)", 
                    "results": []
                }
            
            print("Step 4: Preparing articles for analysis...")
            llm_articles = prepare_data_for_llm(limit=article_count, processed_only=True)
            
            if not llm_articles:
                return {
                    "status": "error",
                    "message": "No articles prepared for LLM processing",
                    "results": []
                }
            
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
            
            # Format for API response
            formatted_results = self._format_api_response(valid_results)
            
            return {
                "status": "success",
                "message": f"Successfully analyzed {len(valid_results)} articles",
                "results": formatted_results
            }
            
        except Exception as e:
            print(f"Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Pipeline failed: {str(e)}",
                "results": []
            }
    
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
    
    def _format_api_response(self, analysis_results):
        """Format results for API response."""
        formatted = []
        
        for result in analysis_results:
            if "error" in result:
                continue
                
            analysis = result.get("analysis", {})
            original_title = result.get("original_title", "Unknown")
            bias_score = analysis.get("overall_bias_score", 0)
            
            formatted.append({
                "title": original_title,
                "analysis": {
                    "overall_bias_score": analysis.get("overall_bias_score", 0),
                    "emotional_bias_score": analysis.get("emotional_bias_score", 0),
                    "framing_bias_score": analysis.get("framing_bias_score", 0),
                    "omission_bias_score": analysis.get("omission_bias_score", 0),
                    "biased_phrases": analysis.get("biased_phrases", [])
                },
                "neutral_version": result.get("neutral_version", ""),
                "original_length": len(result.get("original_text", "")),
                "rewritten_length": len(result.get("neutral_version", "")),
                "is_real_analysis": bias_score != 50
            })
        
        return formatted
    
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


# Global pipeline instance
pipeline = None

def get_pipeline():
    """Get or create pipeline instance."""
    global pipeline
    if pipeline is None:
        pipeline = BiasDetectionPipeline()
    return pipeline


# API Endpoints
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Bias Detection API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "analyze": "/api/v1/analyze",
            "stats": "/api/v1/stats"
        }
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API health and environment variables."""
    required_vars = ['GEMINI_API_KEY', 'GROQ_API_KEY', 'NEWSAPI_AI_KEY', 'NEWS_API_KEY']
    env_status = {var: bool(os.getenv(var)) for var in required_vars}
    
    all_present = all(env_status.values())
    
    return HealthResponse(
        status="healthy" if all_present else "degraded",
        environment_variables=env_status,
        timestamp=datetime.utcnow().isoformat()
    )

@app.post("/api/v1/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_articles(request: AnalysisRequest):
    """
    Analyze news articles for bias.
    
    - *query*: Optional search query for articles
    - *article_count*: Number of articles to analyze (1-20)
    """
    try:
        pipe = get_pipeline()
        result = await pipe.run_full_pipeline(
            query=request.query,
            article_count=request.article_count
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        successful = len([r for r in result["results"] if not r.get("error")])
        failed = len(result["results"]) - successful
        
        return AnalysisResponse(
            status=result["status"],
            message=result["message"],
            total_articles=len(result["results"]),
            successful_analyses=successful,
            failed_analyses=failed,
            results=result["results"],
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/api/v1/stats", response_model=StatsResponse, tags=["Statistics"])
async def get_statistics():
    """Get statistics about analyzed articles."""
    try:
        from src.database.news_db import get_article_stats
        
        total, processed, unique = get_article_stats()
        
        return StatsResponse(
            total_articles=total,
            analyzed_articles=processed,
            pending_articles=total - processed
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.post("/api/v1/analyze/background", tags=["Analysis"])
async def analyze_articles_background(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analyze articles in the background.
    Returns immediately while processing continues.
    """
    async def run_analysis():
        pipe = get_pipeline()
        await pipe.run_full_pipeline(
            query=request.query,
            article_count=request.article_count
        )
    
    background_tasks.add_task(run_analysis)
    
    return {
        "status": "processing",
        "message": "Analysis started in background",
        "query": request.query,
        "article_count": request.article_count
    }

@app.delete("/api/v1/clear", tags=["Database"])
async def clear_processed_articles():
    """Clear all processed articles from the database."""
    try:
        from src.database.news_db import clear_processed_articles
        clear_processed_articles()
        return {
            "status": "success",
            "message": "Processed articles cleared"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.web.api:app",  # Use import string format
        host="127.0.0.1",
        port=8000,
        reload=True
    )