import logging
from dotenv import load_dotenv
import google.generativeai as genai
import os
import pandas as pd
from datetime import datetime
import time
import pytz  # Add this import at the top

# Load environment variables from .env file
load_dotenv()

# Configure Google AI
genai.configure(api_key=os.environ["AISTUDIO_GOOGLE_API_KEY"])

# Set up logging with PST timezone
pst = pytz.timezone('America/Los_Angeles')

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(f'logs/summarize_{datetime.now(pst).strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
# Add PST timezone formatter to logger
logging.Formatter.converter = lambda *args: datetime.now(pst).timetuple()
logger = logging.getLogger(__name__)

def summarize_papers():
    csv_file = 'arxiv-search/data/papers_all_geoscience.csv'
    
    # Initialize the counter
    counter = 1
    while True:
        df = pd.read_csv(csv_file)  # Reload the CSV each time to get latest state
        
        # Find papers without an ai_abstract
        papers_to_summarize = df[df['ai_abstract'].isna()]
        
        if papers_to_summarize.empty:
            logger.info("All papers have been summarized!")
            break
            
        paper_to_summarize = papers_to_summarize.iloc[0]
        
        prompt = f"""Summarize this scientific paper in a couple of sentences, focusing on:
         1. The main research question or objective
         2. Key findings and conclusions
         3. Potential implications or applications

        Do NOT begin with phrases like 'This paper' or 'This study'.

        Title: {paper_to_summarize['title']}
        Authors: {paper_to_summarize['authors']}
        Original Abstract: {paper_to_summarize['summary']}
        
        If you cannot generate a summary, return only 'Unable to summarize'. 
        Only return the summary, nothing else.
        """

        model = genai.GenerativeModel("gemini-1.5-flash")
        try:
            response = model.generate_content(prompt)
            # Handle the response
            if hasattr(response, 'text'):
                summary = response.text.strip()
            elif hasattr(response, 'parts'):
                summary = ' '.join([part.text for part in response.parts]).strip()
            else:
                summary = str(response)
            
            # Update the CSV with the AI summary
            df.loc[df['link'] == paper_to_summarize['link'], 'ai_abstract'] = summary
            df.to_csv(csv_file, index=False)
            
            logger.info(f"Summarized paper {counter}/{len(papers_to_summarize)}: {paper_to_summarize['title']}")
            logger.info(f"Summary: {summary[:200]}...")  # Log first 200 chars of summary
            
            # Wait for 2 minutes before processing the next paper
            if len(papers_to_summarize) > 1:  # Only wait if there are more papers to process
                time.sleep(120)
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            # Store error message in CSV
            #df.loc[df['link'] == paper_to_summarize['link'], 'ai_abstract'] = f"Error: {str(e)}"
            #df.to_csv(csv_file, index=False)
            
            # Wait before trying the next paper
            logger.info("Waiting 2mins...")
            time.sleep(120)

if __name__ == "__main__":
    # Ensure new CSVs have ai_abstract, ai_summary columns
    df = pd.read_csv('arxiv-search/data/papers_all_geoscience.csv')
    if 'ai_abstract' not in df.columns:
        df['ai_abstract'] = pd.Series(dtype='string')
        df.to_csv('arxiv-search/data/papers_all_geoscience.csv', index=False)
    if 'ai_summary' not in df.columns:
        df['ai_summary'] = pd.Series(dtype='string')
        df.to_csv('arxiv-search/data/papers_all_geoscience.csv', index=False)
    
    summarize_papers()
