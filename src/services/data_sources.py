"""
Data source integrations: PubMed, FDA, Google Scholar, Open Access journals
Optimized for parallel execution to meet 45-minute timeline
"""
import requests
import json
import time
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from config import PUBMED_API, FDA_API, PUBMED_TIMEOUT, FDA_TIMEOUT

class DataSourceManager:
    """Orchestrates data collection from multiple sources in parallel"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.cache = {}

    def fetch_all_sources(self, molecule_name: str, max_results: int = 50) -> Dict:
        """
        Fetch data from all sources in parallel
        Returns structured data ready for Claude synthesis
        """
        print(f"\n[FETCH] Fetching data for: {molecule_name}")

        results = {
            "molecule": molecule_name,
            "sources": {
                "pubmed": [],
                "fda": [],
                "google_scholar": [],
                "open_access": []
            },
            "total_articles": 0
        }

        # Execute all API calls in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self.fetch_pubmed, molecule_name, max_results): "pubmed",
                executor.submit(self.fetch_fda, molecule_name): "fda",
                executor.submit(self.fetch_google_scholar, molecule_name, max_results): "google_scholar",
                executor.submit(self.fetch_open_access, molecule_name, max_results): "open_access"
            }

            for future in as_completed(futures):
                source_name = futures[future]
                try:
                    articles = future.result()
                    results["sources"][source_name] = articles
                    print(f"[OK] {source_name.upper()}: {len(articles)} articles")
                except Exception as e:
                    print(f"[WARN] {source_name.upper()} fetch failed: {str(e)}")

        results["total_articles"] = sum(len(v) for v in results["sources"].values())
        return results

    def fetch_pubmed(self, molecule_name: str, max_results: int = 50) -> List[Dict]:
        """Fetch from PubMed API"""
        try:
            # Search query with optimized keywords
            search_terms = [
                molecule_name,
                "pharmacology OR pharmacokinetics OR efficacy OR safety",
                "clinical trial OR meta-analysis"
            ]
            query = f"({' AND '.join(search_terms)})"

            # Fetch from PubMed
            params = {
                'db': 'pubmed',
                'term': query,
                'retmax': max_results,
                'rettype': 'json',
                'sort': 'relevance'
            }

            response = self.session.get(
                f"{PUBMED_API}/esearch.fcgi",
                params=params,
                timeout=PUBMED_TIMEOUT
            )

            if response.status_code != 200:
                return []

            search_results = response.json().get('esearchresult', {})
            pmids = search_results.get('idlist', [])[:max_results]

            if not pmids:
                return []

            # Fetch article details
            articles = []
            detail_params = {
                'db': 'pubmed',
                'id': ','.join(pmids),
                'rettype': 'json'
            }

            detail_response = self.session.get(
                f"{PUBMED_API}/esummary.fcgi",
                params=detail_params,
                timeout=PUBMED_TIMEOUT
            )

            if detail_response.status_code == 200:
                details = detail_response.json().get('result', {})
                for pmid in pmids:
                    if pmid in details:
                        article = details[pmid]
                        articles.append({
                            'source': 'PubMed',
                            'pmid': pmid,
                            'title': article.get('title', ''),
                            'authors': [a.get('name', '') for a in article.get('authors', [])],
                            'publication_date': article.get('pubdate', ''),
                            'journal': article.get('source', ''),
                            'doi': article.get('articleids', [{}])[0].get('value', '') if article.get('articleids') else '',
                            'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                        })

            return articles[:max_results]

        except Exception as e:
            print(f"PubMed error: {str(e)}")
            return []

    def fetch_fda(self, molecule_name: str) -> List[Dict]:
        """Fetch from FDA OpenFDA API"""
        try:
            articles = []

            # Search FDA drug database
            params = {
                'search': f'openfda.generic_name:"{molecule_name.lower()}"',
                'limit': 10
            }

            response = self.session.get(
                f"{FDA_API}/label.json",
                params=params,
                timeout=FDA_TIMEOUT
            )

            if response.status_code == 200:
                results = response.json().get('results', [])
                for result in results:
                    articles.append({
                        'source': 'FDA',
                        'drug_name': result.get('openfda', {}).get('generic_name', [''])[0],
                        'brand_names': result.get('openfda', {}).get('brand_name', []),
                        'indications': result.get('indications_and_usage', [''])[0] if result.get('indications_and_usage') else '',
                        'dosage': result.get('dosage_and_administration', [''])[0] if result.get('dosage_and_administration') else '',
                        'warnings': result.get('warnings', [''])[0] if result.get('warnings') else '',
                        'adverse_reactions': result.get('adverse_reactions', [''])[0] if result.get('adverse_reactions') else '',
                        'url': f"https://www.fda.gov/drugs/information-drugs"
                    })

            return articles

        except Exception as e:
            print(f"FDA error: {str(e)}")
            return []

    def fetch_google_scholar(self, molecule_name: str, max_results: int = 20) -> List[Dict]:
        """
        Fetch from Google Scholar (simplified approach using requests)
        For production, consider using scholarly library with caching
        """
        try:
            articles = []

            # Note: Google Scholar blocks automated access.
            # For MVP, we'll return cached results or suggest user access directly
            # In production, use scholarly library with delays

            search_url = f"https://scholar.google.com/scholar?q={molecule_name}+clinical+trial"

            # This is a simplified approach - Google Scholar actively blocks bots
            # For real implementation, use scholarly library with proper delays

            return articles  # Return empty for MVP, can be enhanced

        except Exception as e:
            print(f"Google Scholar error: {str(e)}")
            return []

    def fetch_open_access(self, molecule_name: str, max_results: int = 20) -> List[Dict]:
        """Fetch from open access repositories (PubMed Central, bioRxiv, arXiv)"""
        try:
            articles = []

            # PubMed Central open access articles
            params = {
                'db': 'pmc',
                'term': f'{molecule_name} AND free full text AND clinical',
                'retmax': max_results,
                'rettype': 'json'
            }

            response = self.session.get(
                f"{PUBMED_API}/esearch.fcgi",
                params=params,
                timeout=PUBMED_TIMEOUT
            )

            if response.status_code == 200:
                results = response.json().get('esearchresult', {})
                pmcids = results.get('idlist', [])[:max_results]

                for pmcid in pmcids:
                    articles.append({
                        'source': 'PubMed Central (Open Access)',
                        'pmcid': pmcid,
                        'url': f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmcid}/",
                        'access': 'free'
                    })

            return articles

        except Exception as e:
            print(f"Open Access error: {str(e)}")
            return []

    def structure_for_claude(self, sources: Dict) -> str:
        """Convert raw sources into Claude-optimized format"""
        formatted = f"""
## RESEARCH SOURCES FOR: {sources['molecule']}
Total articles found: {sources['total_articles']}

### PubMed Articles ({len(sources['sources']['pubmed'])})
"""
        for article in sources['sources']['pubmed'][:15]:  # Top 15
            formatted += f"\n- **{article.get('title', 'N/A')}**\n"
            formatted += f"  Authors: {', '.join(article.get('authors', ['Unknown'])[:3])}\n"
            formatted += f"  Journal: {article.get('journal', 'N/A')} ({article.get('publication_date', 'N/A')})\n"
            formatted += f"  DOI: {article.get('doi', 'N/A')}\n"

        formatted += f"\n### FDA Data ({len(sources['sources']['fda'])})\n"
        for article in sources['sources']['fda']:
            formatted += f"\n- **{article.get('drug_name', 'N/A')}**\n"
            formatted += f"  Indications: {article.get('indications', 'N/A')[:200]}...\n"

        return formatted


# Initialize globally
data_manager = DataSourceManager()

if __name__ == "__main__":
    # Test the data sources
    results = data_manager.fetch_all_sources("Metformin", max_results=20)
    print(json.dumps({k: len(v) for k, v in results['sources'].items()}, indent=2))
