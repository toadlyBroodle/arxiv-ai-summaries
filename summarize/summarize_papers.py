import sys
import logging
import os
import pandas as pd
from datetime import datetime
import time
import pytz
import argparse
from gemini_api import GeminiAPI

# Set up logging with PST timezone
pst = pytz.timezone('America/Los_Angeles')

def setup_logging():
    """Configure logging with PST timezone"""
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
    return logging.getLogger(__name__)

def prepare_csv(csv_file: str) -> pd.DataFrame:
    """Prepare CSV file by ensuring required columns exist"""
    df = pd.read_csv(csv_file)
    modified = False
    
    for column in ['ai_abstract', 'ai_summary']:
        if column not in df.columns:
            df[column] = pd.Series(dtype='string')
            modified = True
    
    if modified:
        df.to_csv(csv_file, index=False)
    
    return df

def summarize_papers(csv_file: str, logger: logging.Logger):
    """Summarize papers using Gemini API"""
    try:
        # Initialize Gemini API
        gemini = GeminiAPI()
        
        # Check API availability before starting
        if not gemini.check_api_availability():
            logger.error("Gemini API is not available. Exiting...")
            return
        
        df = prepare_csv(csv_file)
        papers_to_summarize = df[df['ai_abstract'].isna()]
        
        if papers_to_summarize.empty:
            logger.info("All papers have been summarized!")
            return

        total_papers = len(papers_to_summarize)
        for counter, (_, paper) in enumerate(papers_to_summarize.iterrows()):
            prompt = f"""Summarize this scientific paper in a couple of sentences, focusing on:
             1. The main research question or objective
             2. Key findings and conclusions
             3. Potential implications or applications

            Title: {paper['title']}
            Authors: {paper['authors']}
            Original Abstract: {paper['summary']}
            
            If you cannot generate a summary, return only 'Unable to summarize'. 
            Only return the summary, nothing else.
            """

            summary, error = gemini.generate_summary(prompt)
            
            if error:
                # Fatal errors will terminate the program
                if error.startswith("FATAL:"):
                    logger.error(f"Fatal error occurred: {error}")
                    df.loc[df['link'] == paper['link'], 'ai_abstract'] = f"Error: {error}"
                    df.to_csv(csv_file, index=False)
                    sys.exit(1)
                
                # Non-fatal errors will be logged and the paper will be skipped
                df.loc[df['link'] == paper['link'], 'ai_abstract'] = f"Error: {error}"
                logger.error(f"Error processing paper {counter + 1}/{total_papers}: {error}")
            else: # Successful summary
                df.loc[df['link'] == paper['link'], 'ai_abstract'] = summary
                logger.info(f"Summarized paper {counter + 1}/{total_papers}: {paper['title']}")
                logger.info(f"Summary: {summary[:200]}...")
            
            # Save after each paper in case of interruption
            df.to_csv(csv_file, index=False)

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Summarize scientific papers using Gemini AI')
    parser.add_argument('--csv_file', required=True, help='Path to the CSV file containing papers to summarize')
    args = parser.parse_args()

    if not os.path.exists(args.csv_file):
        print(f"Error: CSV file not found: {args.csv_file}")
        sys.exit(1)

    logger = setup_logging()
    summarize_papers(args.csv_file, logger)

if __name__ == "__main__":
    main()
