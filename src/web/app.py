from shiny import App, ui, render, reactive
import pandas as pd
import sqlite3
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path to import your modules
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

app_ui = ui.page_fluid(
    ui.div(
        {"style": "width: 100%; margin: 0; padding: 20px;"},
        ui.h2("HalfTruths - a Bias Detection Dashboard", style="margin: 10px 0; color: inherit;"),
        
        ui.div(
            ui.div(
                ui.h4("News Articles", style="color: inherit;"),
                ui.input_action_button("fetch_articles", "Fetch Latest Articles", width="100%"),                
                ui.hr(style="margin: 20px 0; border-color: #ddd;"),
                
                ui.output_ui("articles_list"),
                
                ui.div(
                    ui.input_checkbox("dark_mode", "Dark Mode", False),
                    style="margin-top: 20px;"
                ),
                style=(
                    "padding: 15px; background: #f8f9fa; border-radius: 5px; "
                    "width: 300px; float: left; height: 800px; overflow-y: auto;"
                ),
                id="sidebar"
            ),
            
            ui.div(
                ui.div(
                    ui.h4("Article Analysis", style="color: inherit;"),
                    ui.output_ui("article_display"),
                    style="margin-bottom: 20px;"
                ),
                style="margin-left: 320px; padding-right: 20px;",
                id="main-content"
            ),
            style="overflow: hidden;"
        )
    )
)

def server(input, output, session):
    @reactive.effect
    @reactive.event(input.dark_mode)
    def _():
        if input.dark_mode():
            ui.insert_ui(
                ui.tags.style("""
                    body { 
                        background-color: #222; 
                        color: white; 
                    }
                    #sidebar { 
                        background-color: #333 !important; 
                        color: white !important;
                    }
                    .form-control { 
                        background-color: #444 !important; 
                        color: white !important; 
                        border-color: #666 !important;
                    }
                    .data-grid { 
                        background-color: #333 !important; 
                        color: white !important; 
                    }
                    .btn { 
                        border-color: white !important;
                        color: white !important;
                    }
                    .btn-default {
                        background-color: #444 !important;
                    }
                    .btn-primary {
                        background-color: #0069d9 !important;
                    }
                """),
                selector="body",
                immediate=True
            )
            ui.update_checkbox("dark_mode", label="Light Mode")
        else:
            ui.remove_ui(selector="style", multiple=True)
            ui.update_checkbox("dark_mode", label="Dark Mode")

    articles_data = reactive.value(pd.DataFrame())
    selected_article = reactive.value(None)

    def get_articles_from_db():
        """Fetch articles from SQLite database."""
        try:
            conn = sqlite3.connect('data/databases/news.db')
            query = """
                SELECT title, source, date, category, body, bias, rewritten_article
                FROM data_news 
                ORDER BY date DESC
                LIMIT 50
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Database error: {e}")
            return pd.DataFrame()

    import httpx

    async def run_bias_analysis():
        """Run bias analysis via the FastAPI backend."""
        try:
            print("🔍 DEBUG: Calling FastAPI backend for analysis...")
            
            async with httpx.AsyncClient() as client:
                # Call the analyze endpoint
                response = await client.post(
                    "http://127.0.0.1:8000/api/v1/analyze",
                    json={
                        "query": None,
                        "article_count": 3
                    },
                    timeout=120.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ DEBUG: API analysis successful - {result['message']}")
                    print(f"✅ DEBUG: Got {len(result['results'])} analyzed articles")
                    
                    # Return the results in the format your Shiny app expects
                    return result['results']
                else:
                    print(f"❌ DEBUG: API analysis failed - {response.status_code}: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ DEBUG: API analysis call failed: {e}")
            return None

    @reactive.effect
    @reactive.event(input.fetch_articles)
    def fetch_articles():
        ui.notification_show("Fetching latest articles...", duration=3)
        df = get_articles_from_db()
        articles_data.set(df)
        if not df.empty:
            ui.notification_show(f"Loaded {len(df)} articles", duration=3)

    @reactive.effect
    @reactive.event(input.analyze_bias)
    def analyze_bias():
        ui.notification_show("Starting bias analysis pipeline...", duration=5)
        
        # Use reactive.Value to communicate between threads
        analysis_status = reactive.value("running")
        analysis_message = reactive.value("")
        
        # Run the async pipeline
        def run_async_analysis():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(run_bias_analysis())
                if results:
                    analysis_status.set("success")
                    analysis_message.set(f"Analyzed {len(results)} articles")
                else:
                    analysis_status.set("failed")
                    analysis_message.set("Analysis failed or no articles processed")
            except Exception as e:
                analysis_status.set("error")
                analysis_message.set(f"Analysis error: {str(e)}")
                print(f"Analysis thread error: {e}")
            finally:
                loop.close()
        
        # Run in a thread to avoid blocking
        import threading
        thread = threading.Thread(target=run_async_analysis)
        thread.start()
        
        # Watch for completion
        @reactive.effect
        def _():
            status = analysis_status()
            if status != "running":
                # Remove this effect once it completes
                reactive.invalidate_later(0)
                ui.notification_show(analysis_message(), duration=5)
                # Refresh articles after analysis
                if status == "success":
                    df = get_articles_from_db()
                    articles_data.set(df)

    @reactive.effect
    @reactive.event(input.test_imports)
    def test_imports():
        """Test if we can import the required modules."""
        ui.notification_show("Testing imports...", duration=5)
        
        def run_import_test():
            try:
                print("🧪 TEST: Testing imports...")
                
                # Test basic imports
                import sys
                print(f"🧪 TEST: Python path: {sys.path}")
                print(f"🧪 TEST: Current directory: {os.getcwd()}")
                print(f"🧪 TEST: Project root: {project_root}")
                
                # Test project imports
                try:
                    from src.services.news_client import NewsClient
                    print("✅ TEST: NewsClient import successful")
                except ImportError as e:
                    print(f"❌ TEST: NewsClient import failed: {e}")
                    
                try:
                    from src.agents.orchestrator import BiasAnalysisOrchestrator
                    print("✅ TEST: BiasAnalysisOrchestrator import successful")
                except ImportError as e:
                    print(f"❌ TEST: BiasAnalysisOrchestrator import failed: {e}")
                    
                try:
                    from src.database.news_db import get_connection_to_news_db
                    print("✅ TEST: Database functions import successful")
                except ImportError as e:
                    print(f"❌ TEST: Database functions import failed: {e}")
                    
                print("🧪 TEST: Import test completed")
                
            except Exception as e:
                print(f"❌ TEST: Import test failed: {e}")
        
        import threading
        thread = threading.Thread(target=run_import_test)
        thread.start()

    @render.ui
    def articles_list():
        df = articles_data()
        if df.empty:
            return ui.p("No articles available. Click 'Fetch Latest Articles' to load articles.")
        
        articles_ui = []
        for idx, row in df.iterrows():
            has_analysis = pd.notna(row.get('bias')) and row.get('bias') not in ['None', '{}', '']
            
            article_card = ui.div(
                ui.div(
                    ui.h5(row['title'][:80] + "..." if len(row['title']) > 80 else row['title']),
                    ui.p(f"Source: {row['source']} | {row['date']}"),
                    ui.p(f"Category: {row['category']}"),
                    ui.div(
                        "✅ Analyzed" if has_analysis else "⏳ Pending Analysis",
                        style="font-size: 0.8em; color: " + ("green" if has_analysis else "orange") + ";"
                    ),
                    style=(
                        "padding: 10px; margin: 5px 0; border: 1px solid #ddd; "
                        "border-radius: 5px; cursor: pointer; background: white;"
                    )
                ),
                onclick=f"Shiny.setInputValue('select_article', {idx});"
            )
            articles_ui.append(article_card)
        
        return ui.div(*articles_ui)

    @reactive.effect
    @reactive.event(input.select_article)
    def update_selected_article():
        idx = input.select_article()
        df = articles_data()
        if not df.empty and 0 <= idx < len(df):
            selected_article.set(df.iloc[idx].to_dict())

    @render.ui
    def article_display():
        article = selected_article()
        if not article:
            return ui.p("Select an article from the left to view details.")
        
        has_analysis = article.get('bias') and article.get('bias') not in ['None', '{}', '']
        
        content = [
            ui.h3(article['title']),
            ui.p(f"Source: {article['source']}"),
            ui.p(f"Date: {article['date']}"),
            ui.p(f"Category: {article['category']}"),
            ui.hr()
        ]
        
        # Show original article body
        if article.get('body'):
            content.extend([
                ui.h4("Original Article"),
                ui.div(
                    article['body'],
                    style="max-height: 300px; overflow-y: auto; padding: 10px; background: #f5f5f5; border-radius: 5px;"
                ),
                ui.hr()
            ])
        
        if has_analysis and article.get('rewritten_article'):
            try:
                bias_data = eval(article['bias']) if isinstance(article['bias'], str) else article['bias']
                
                # Bias scores
                content.extend([
                    ui.h4("Bias Analysis"),
                    ui.div(
                        ui.div(
                            f"Overall Bias: {bias_data.get('overall_bias_score', 'N/A')}/100",
                            style=f"font-size: 1.2em; font-weight: bold; color: {'red' if bias_data.get('overall_bias_score', 0) > 70 else 'orange' if bias_data.get('overall_bias_score', 0) > 30 else 'green'};"
                        ),
                        ui.p(f"Emotional Bias: {bias_data.get('emotional_bias_score', 'N/A')}/100"),
                        ui.p(f"Framing Bias: {bias_data.get('framing_bias_score', 'N/A')}/100"),
                        ui.p(f"Omission Bias: {bias_data.get('omission_bias_score', 'N/A')}/100"),
                        style="padding: 10px; background: #f0f8ff; border-radius: 5px; margin: 10px 0;"
                    ),
                    ui.hr(),
                    ui.h4("Unbiased Rewrite"),
                    ui.div(
                        article['rewritten_article'],
                        style="padding: 15px; background: #f9f9f9; border-radius: 5px; border-left: 4px solid #007bff;"
                    )
                ])
                
                # Show biased phrases if available
                biased_phrases = bias_data.get('biased_phrases', [])
                if biased_phrases:
                    content.extend([
                        ui.hr(),
                        ui.h4("Detected Biased Phrases"),
                        ui.ul(*[
                            ui.li(f"'{phrase.get('text', '')}' → {phrase.get('suggested_replacement', 'neutral')} ({phrase.get('bias_type', 'unknown')})")
                            for phrase in biased_phrases[:5]  # Show first 5
                        ])
                    ])
                    
            except Exception as e:
                content.append(ui.p(f"Error displaying analysis data: {str(e)}"))
        else:
            content.append(ui.p("This article hasn't been analyzed yet. Click 'Analyze All Pending' to process it."))
        
        return ui.div(*content)

app = App(app_ui, server)