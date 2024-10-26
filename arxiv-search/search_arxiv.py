import argparse
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import csv
from datetime import datetime

def query_arxiv(search_query, start=0, max_results=10, sort_by='relevance', sort_order='descending'):
    base_url = 'http://export.arxiv.org/api/query?'
    query_params = {
        'search_query': search_query,
        'start': start,
        'max_results': max_results,
        'sortBy': sort_by,
        'sortOrder': sort_order
    }
    url = base_url + urllib.parse.urlencode(query_params)
    response = urllib.request.urlopen(url)
    return response.read().decode('utf-8')

def parse_arxiv_response(xml_response):
    root = ET.fromstring(xml_response)
    
    # Namespace definition
    namespace = {'atom': 'http://www.w3.org/2005/Atom', 'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'}
    
    # Get total results
    total_results = root.find('.//opensearch:totalResults', namespace).text
    if int(total_results) == 0:
        return "No results found for your search query."
    
    # Parse entries with additional metadata
    entries = []
    for entry in root.findall('.//atom:entry', namespace):
        paper = {
            'title': entry.find('atom:title', namespace).text.strip(),
            'authors': [author.find('atom:name', namespace).text for author in entry.findall('atom:author', namespace)],
            'summary': entry.find('atom:summary', namespace).text.strip(),
            'link': entry.find('./atom:link[@title="pdf"]', namespace).get('href') if entry.find('./atom:link[@title="pdf"]', namespace) is not None else entry.find('atom:id', namespace).text,
            'published': entry.find('atom:published', namespace).text[:10],
            'updated': entry.find('atom:updated', namespace).text[:10],  # Add updated date
            'comment': entry.find('atom:comment', namespace).text if entry.find('atom:comment', namespace) is not None else "N/A",
            'journal_ref': entry.find('atom:journal_ref', namespace).text if entry.find('atom:journal_ref', namespace) is not None else "N/A"
        }
        entries.append(paper)
    
    return entries

def display_results(entries):
    if isinstance(entries, str):
        print(entries)
        return
    
    # ANSI color codes
    title_color = '\033[1;34m'  # Bold Blue
    author_color = '\033[0;32m'  # Green
    date_color = '\033[0;36m'  # Cyan
    link_color = '\033[1;35m'  # Magenta
    summary_color = '\033[0;37m'  # White
    reset_color = '\033[0m'  # Reset

    print(f"\nFound {len(entries)} results:\n")
    for i, paper in enumerate(entries, 1):
        print(f"{title_color}[{i}] {paper['title']}{reset_color}")
        print(f"{author_color}Authors:{reset_color} {', '.join(paper['authors'])}")
        print(f"{date_color}Published:{reset_color} {paper['published']}")
        print(f"{date_color}Updated:{reset_color} {paper['updated']}")
        print(f"{summary_color}Journal Reference:{reset_color} {paper['journal_ref']}")
        print(f"{summary_color}Comment:{reset_color} {paper['comment']}")
        print(f"{link_color}Link:{reset_color} {paper['link']}")
        print(f"{summary_color}Summary:{reset_color} {paper['summary'][:200]}...")  # Show first 200 chars of summary
        print("\n" + "="*80 + "\n")



def save_to_csv(entries, filename):
    if isinstance(entries, str):
        print(f"No results to save: {entries}")
        return
        
    # If no filename provided, create one with timestamp
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'arxiv_results_{timestamp}.csv'
    
    # Add .csv extension if not present
    if not filename.endswith('.csv'):
        filename += '.csv'
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['title', 'authors', 'published', 'link', 'summary']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for paper in entries:
                writer.writerow({
                    'title': paper['title'],
                    'authors': '; '.join(paper['authors']),
                    'published': paper['published'],
                    'link': paper['link'],
                    'summary': paper['summary']
                })
        print(f"\nResults saved to: {filename}")
    except Exception as e:
        print(f"Error saving to CSV: {str(e)}")

def main():
    parser = argparse.ArgumentParser(
        description='Query the arXiv API with various search parameters.',
        epilog='Example usage:\n'
               '  python review_bot.py "cat:cs.AI+OR+cat:cs.LG" --max_results 5 --sort_by submittedDate\n'
               '  python review_bot.py "ti:quantum+OR+ti:relativity" --sort_order ascending\n'
               '  python review_bot.py "all:geology" --save_csv results.csv\n\n'
               'Search Fields:\n'
               '  ti: Title\n'
               '  au: Author\n'
               '  abs: Abstract\n'
               '  co: Comment\n'
               '  jr: Journal reference\n'
               '  cat: Category\n'
               '  rn: Report number\n'
               '  all: All fields\n\n'
               'Logical Operators:\n'
               '  AND, OR, ANDNOT\n\n'
               'Use "+" to represent spaces in search terms.',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('search_query', type=str, help='The search query for arXiv. Combine fields and terms using logical operators.')
    parser.add_argument('--start', type=int, default=0, help='The starting index for results (default: 0).')
    parser.add_argument('--max_results', type=int, default=10, help='The maximum number of results to return (default: 10).')
    parser.add_argument('--sort_by', type=str, choices=['relevance', 'lastUpdatedDate', 'submittedDate'], default='relevance', help='Sort by field (default: relevance).')
    parser.add_argument('--sort_order', type=str, choices=['ascending', 'descending'], default='descending', help='Sort order (default: descending).')
    parser.add_argument('--save_csv', type=str, nargs='?', const='', 
                       help='Save results to CSV file. Optionally specify filename, otherwise timestamp will be used.')

    args = parser.parse_args()

    xml_response = query_arxiv(args.search_query, args.start, args.max_results, args.sort_by, args.sort_order)
    results = parse_arxiv_response(xml_response)
    display_results(results)
    
    if args.save_csv is not None:
        save_to_csv(results, args.save_csv)

if __name__ == '__main__':
    main()
