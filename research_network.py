import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import requests
from bs4 import BeautifulSoup
import wikipedia
from urllib.parse import urljoin, urlparse
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ResearchResult:
    """Data class to store research results"""
    source: str
    title: str
    content: str
    url: Optional[str] = None
    timestamp: str = None
    reliability_score: float = 0.0
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class WebScrapingTool:
    """Enhanced web scraping tool with multiple search engines"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.search_engines = {
            'duckduckgo': self._search_duckduckgo,
            'bing': self._search_bing
        }
    
    def _search_duckduckgo(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search using DuckDuckGo"""
        try:
            # DuckDuckGo instant answer API
            url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
            response = self.session.get(url, timeout=10)
            
            results = []
            if response.status_code == 200:
                data = response.json()
                
                # Abstract result
                if data.get('Abstract'):
                    results.append({
                        'title': data.get('Heading', query),
                        'url': data.get('AbstractURL', ''),
                        'snippet': data.get('Abstract', ''),
                        'source': 'DuckDuckGo Abstract'
                    })
                
                # Related topics
                for topic in data.get('RelatedTopics', [])[:5]:
                    if isinstance(topic, dict) and topic.get('Text'):
                        results.append({
                            'title': topic.get('Text', '')[:100],
                            'url': topic.get('FirstURL', ''),
                            'snippet': topic.get('Text', ''),
                            'source': 'DuckDuckGo Related'
                        })
            
            return results[:num_results]
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []
    
    def _search_bing(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search using Bing (scraping search results page)"""
        try:
            url = f"https://www.bing.com/search?q={query}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Find search results
            for result in soup.find_all('li', class_='b_algo')[:num_results]:
                title_elem = result.find('h2')
                snippet_elem = result.find('p') or result.find('div', class_='b_caption')
                
                if title_elem and snippet_elem:
                    title = title_elem.get_text().strip()
                    snippet = snippet_elem.get_text().strip()
                    link_elem = title_elem.find('a')
                    url = link_elem.get('href') if link_elem else ''
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'source': 'Bing Search'
                    })
            
            return results
        except Exception as e:
            logger.error(f"Bing search failed: {e}")
            return []
    
    def search_web(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search web using multiple engines"""
        all_results = []
        
        for engine_name, search_func in self.search_engines.items():
            try:
                results = search_func(query, num_results//len(self.search_engines))
                for result in results:
                    result['search_engine'] = engine_name
                all_results.extend(results)
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.error(f"Search engine {engine_name} failed: {e}")
        
        return all_results[:num_results]
    
    def scrape_content(self, url: str) -> Optional[str]:
        """Scrape content from a given URL"""
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Try to find main content
                content_selectors = [
                    'article', 'main', '.content', '.post-content', 
                    '.entry-content', '#content', '.article-body'
                ]
                
                content = ""
                for selector in content_selectors:
                    element = soup.select_one(selector)
                    if element:
                        content = element.get_text().strip()
                        break
                
                if not content:
                    # Fallback to body content
                    body = soup.find('body')
                    if body:
                        content = body.get_text().strip()
                
                # Clean up the content
                content = re.sub(r'\s+', ' ', content)
                return content[:5000]  # Limit content length
                
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
        
        return None

class WikipediaAgent:
    """Agent for Wikipedia research"""
    
    def search_wikipedia(self, query: str, num_results: int = 5) -> List[ResearchResult]:
        """Search Wikipedia for relevant articles"""
        results = []
        try:
            # Search for pages
            search_results = wikipedia.search(query, results=num_results)
            
            for title in search_results:
                try:
                    page = wikipedia.page(title)
                    content = page.summary[:2000]  # Limit summary length
                    
                    results.append(ResearchResult(
                        source="Wikipedia",
                        title=title,
                        content=content,
                        url=page.url,
                        reliability_score=0.8  # Wikipedia generally reliable
                    ))
                    
                except wikipedia.exceptions.DisambiguationError as e:
                    # Take the first option
                    try:
                        page = wikipedia.page(e.options[0])
                        content = page.summary[:2000]
                        
                        results.append(ResearchResult(
                            source="Wikipedia",
                            title=e.options[0],
                            content=content,
                            url=page.url,
                            reliability_score=0.8
                        ))
                    except:
                        continue
                        
                except wikipedia.exceptions.PageError:
                    continue
                    
        except Exception as e:
            logger.error(f"Wikipedia search failed: {e}")
        
        return results

class WebResearchAgent:
    """Agent for web research using scraping"""
    
    def __init__(self):
        self.scraper = WebScrapingTool()
    
    def research_topic(self, query: str, num_results: int = 10) -> List[ResearchResult]:
        """Research a topic using web scraping"""
        results = []
        
        # Get search results
        search_results = self.scraper.search_web(query, num_results)
        
        # Process each result
        for result in search_results:
            content = result.get('snippet', '')
            
            # Try to get more content by scraping the URL
            if result.get('url'):
                scraped_content = self.scraper.scrape_content(result['url'])
                if scraped_content and len(scraped_content) > len(content):
                    content = scraped_content
            
            if content:
                results.append(ResearchResult(
                    source=result.get('search_engine', 'Web'),
                    title=result.get('title', 'Unknown'),
                    content=content,
                    url=result.get('url'),
                    reliability_score=self._calculate_reliability(result.get('url', ''))
                ))
        
        return results
    
    def _calculate_reliability(self, url: str) -> float:
        """Simple reliability scoring based on domain"""
        if not url:
            return 0.3
        
        domain = urlparse(url).netloc.lower()
        
        # High reliability domains
        if any(trusted in domain for trusted in [
            'edu', 'gov', 'org', 'nature.com', 'science.org', 
            'ieee.org', 'acm.org', 'arxiv.org'
        ]):
            return 0.9
        
        # Medium reliability
        if any(medium in domain for medium in [
            'reuters.com', 'bbc.com', 'npr.org', 'pbs.org',
            'wikipedia.org', 'britannica.com'
        ]):
            return 0.7
        
        # Default reliability
        return 0.5

class SummarizerAgent:
    """Agent for summarizing research results"""
    
    def summarize_content(self, content: str, max_length: int = 500) -> str:
        """Simple extractive summarization"""
        if len(content) <= max_length:
            return content
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        # Simple scoring based on position and length
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = 0
            
            # Position-based scoring (first and last sentences often important)
            if i < len(sentences) * 0.3:
                score += 2
            if i > len(sentences) * 0.7:
                score += 1
            
            # Length-based scoring
            if 50 < len(sentence) < 200:
                score += 1
            
            # Keyword-based scoring (simple approach)
            important_words = ['important', 'significant', 'key', 'main', 'primary', 'conclude']
            for word in important_words:
                if word in sentence.lower():
                    score += 1
            
            scored_sentences.append((sentence, score))
        
        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Select sentences to fit within max_length
        selected_sentences = []
        current_length = 0
        
        for sentence, score in scored_sentences:
            if current_length + len(sentence) <= max_length:
                selected_sentences.append(sentence)
                current_length += len(sentence)
            else:
                break
        
        return '. '.join(selected_sentences) + '.'
    
    def create_comprehensive_summary(self, research_results: List[ResearchResult]) -> Dict[str, Any]:
        """Create a comprehensive summary from all research results"""
        if not research_results:
            return {"summary": "No research results found.", "sources": []}
        
        # Group results by source
        by_source = {}
        for result in research_results:
            if result.source not in by_source:
                by_source[result.source] = []
            by_source[result.source].append(result)
        
        # Create source summaries
        source_summaries = {}
        all_content = []
        
        for source, results in by_source.items():
            combined_content = " ".join([r.content for r in results])
            source_summaries[source] = {
                "summary": self.summarize_content(combined_content, 300),
                "count": len(results),
                "avg_reliability": sum(r.reliability_score for r in results) / len(results)
            }
            all_content.append(combined_content)
        
        # Create overall summary
        overall_content = " ".join(all_content)
        overall_summary = self.summarize_content(overall_content, 800)
        
        return {
            "overall_summary": overall_summary,
            "source_summaries": source_summaries,
            "total_sources": len(research_results),
            "avg_reliability": sum(r.reliability_score for r in research_results) / len(research_results),
            "sources": [{"title": r.title, "url": r.url, "source": r.source} for r in research_results]
        }

class FactCheckerAgent:
    """Agent for basic fact-checking and cross-referencing"""
    
    def cross_reference_facts(self, research_results: List[ResearchResult]) -> Dict[str, Any]:
        """Cross-reference facts across multiple sources"""
        # Group similar information
        fact_groups = self._group_similar_facts(research_results)
        
        # Score facts based on source reliability and frequency
        verified_facts = []
        disputed_facts = []
        
        for fact_group in fact_groups:
            confidence = self._calculate_fact_confidence(fact_group)
            
            if confidence > 0.7:
                verified_facts.append({
                    "fact": fact_group["representative_text"],
                    "confidence": confidence,
                    "sources": len(fact_group["sources"]),
                    "source_list": fact_group["sources"]
                })
            elif confidence < 0.4:
                disputed_facts.append({
                    "fact": fact_group["representative_text"],
                    "confidence": confidence,
                    "sources": len(fact_group["sources"]),
                    "source_list": fact_group["sources"]
                })
        
        return {
            "verified_facts": verified_facts,
            "disputed_facts": disputed_facts,
            "fact_check_summary": f"Found {len(verified_facts)} verified facts and {len(disputed_facts)} disputed facts"
        }
    
    def _group_similar_facts(self, research_results: List[ResearchResult]) -> List[Dict]:
        """Simple fact grouping based on keyword similarity"""
        # This is a simplified implementation
        # In a real system, you'd use more sophisticated NLP techniques
        
        sentences = []
        for result in research_results:
            # Split content into sentences
            result_sentences = re.split(r'[.!?]+', result.content)
            for sentence in result_sentences:
                if len(sentence.strip()) > 30:  # Minimum sentence length
                    sentences.append({
                        "text": sentence.strip(),
                        "source": result.source,
                        "reliability": result.reliability_score,
                        "url": result.url
                    })
        
        # Group sentences by keyword similarity (simplified)
        groups = []
        used_indices = set()
        
        for i, sentence in enumerate(sentences):
            if i in used_indices:
                continue
            
            group = {
                "representative_text": sentence["text"],
                "sources": [sentence["source"]],
                "reliabilities": [sentence["reliability"]],
                "urls": [sentence["url"]]
            }
            used_indices.add(i)
            
            # Find similar sentences
            for j, other_sentence in enumerate(sentences):
                if j <= i or j in used_indices:
                    continue
                
                if self._are_similar(sentence["text"], other_sentence["text"]):
                    group["sources"].append(other_sentence["source"])
                    group["reliabilities"].append(other_sentence["reliability"])
                    group["urls"].append(other_sentence["url"])
                    used_indices.add(j)
            
            if len(group["sources"]) > 1:  # Only keep facts mentioned by multiple sources
                groups.append(group)
        
        return groups
    
    def _are_similar(self, text1: str, text2: str, threshold: float = 0.3) -> bool:
        """Simple similarity check based on common words"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if len(words1) == 0 or len(words2) == 0:
            return False
        
        common_words = words1.intersection(words2)
        similarity = len(common_words) / min(len(words1), len(words2))
        
        return similarity > threshold
    
    def _calculate_fact_confidence(self, fact_group: Dict) -> float:
        """Calculate confidence score for a fact"""
        # Base confidence from number of sources
        source_count = len(fact_group["sources"])
        base_confidence = min(0.9, source_count * 0.2)
        
        # Adjust by average reliability
        avg_reliability = sum(fact_group["reliabilities"]) / len(fact_group["reliabilities"])
        
        return base_confidence * avg_reliability

class ReportWriterAgent:
    """Agent for writing comprehensive research reports"""
    
    def write_research_report(self, query: str, summary_data: Dict, fact_check_data: Dict) -> str:
        """Write a comprehensive research report"""
        report = []
        
        # Title and introduction
        report.append(f"# Research Report: {query}")
        report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Executive Summary
        report.append("## Executive Summary")
        report.append(summary_data.get("overall_summary", "No summary available."))
        report.append("")
        
        # Key Statistics
        report.append("## Research Statistics")
        report.append(f"- Total sources analyzed: {summary_data.get('total_sources', 0)}")
        report.append(f"- Average source reliability: {summary_data.get('avg_reliability', 0):.2f}")
        report.append(f"- Verified facts found: {len(fact_check_data.get('verified_facts', []))}")
        report.append(f"- Disputed facts found: {len(fact_check_data.get('disputed_facts', []))}")
        report.append("")
        
        # Verified Facts
        if fact_check_data.get('verified_facts'):
            report.append("## Verified Facts")
            for fact in fact_check_data['verified_facts']:
                report.append(f"- **{fact['fact']}** (Confidence: {fact['confidence']:.2f}, Sources: {fact['sources']})")
            report.append("")
        
        # Source Analysis
        report.append("## Source Analysis")
        for source, data in summary_data.get('source_summaries', {}).items():
            report.append(f"### {source}")
            report.append(f"- Articles analyzed: {data['count']}")
            report.append(f"- Reliability score: {data['avg_reliability']:.2f}")
            report.append(f"- Summary: {data['summary']}")
            report.append("")
        
        # Disputed Information
        if fact_check_data.get('disputed_facts'):
            report.append("## Disputed Information")
            report.append("The following information appeared in sources but should be verified:")
            for fact in fact_check_data['disputed_facts']:
                report.append(f"- **{fact['fact']}** (Confidence: {fact['confidence']:.2f})")
            report.append("")
        
        # Sources
        report.append("## Sources")
        for i, source in enumerate(summary_data.get('sources', []), 1):
            if source.get('url'):
                report.append(f"{i}. [{source['title']}]({source['url']}) - {source['source']}")
            else:
                report.append(f"{i}. {source['title']} - {source['source']}")
        
        return "\n".join(report)

class ResearchAssistantNetwork:
    """Main orchestrator for the research assistant network"""
    
    def __init__(self):
        self.web_agent = WebResearchAgent()
        self.wiki_agent = WikipediaAgent()
        self.summarizer = SummarizerAgent()
        self.fact_checker = FactCheckerAgent()
        self.writer = ReportWriterAgent()
    
    async def conduct_research(self, query: str, include_web: bool = True, include_wiki: bool = True) -> str:
        """Conduct comprehensive research on a topic"""
        logger.info(f"Starting research on: {query}")
        
        all_results = []
        
        # Parallel research using different agents
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            
            if include_web:
                futures.append(executor.submit(self.web_agent.research_topic, query, 15))
            
            if include_wiki:
                futures.append(executor.submit(self.wiki_agent.search_wikipedia, query, 5))
            
            # Collect results
            for future in as_completed(futures):
                try:
                    results = future.result(timeout=30)
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"Research task failed: {e}")
        
        logger.info(f"Collected {len(all_results)} research results")
        
        # Process results
        if not all_results:
            return "No research results found. Please try a different query."
        
        # Create summary
        summary_data = self.summarizer.create_comprehensive_summary(all_results)
        
        # Perform fact checking
        fact_check_data = self.fact_checker.cross_reference_facts(all_results)
        
        # Generate final report
        report = self.writer.write_research_report(query, summary_data, fact_check_data)
        
        logger.info("Research complete!")
        return report
    
    def quick_research(self, query: str) -> str:
        """Quick synchronous research for simple queries"""
        try:
            # Get web results
            web_results = self.web_agent.research_topic(query, 8)
            
            # Get Wikipedia results
            wiki_results = self.wiki_agent.search_wikipedia(query, 3)
            
            # Combine results
            all_results = web_results + wiki_results
            
            if not all_results:
                return "No research results found."
            
            # Quick summary
            summary_data = self.summarizer.create_comprehensive_summary(all_results)
            
            return f"""# Quick Research Summary: {query}

**Overall Summary:**
{summary_data.get('overall_summary', 'No summary available.')}

**Sources Found:** {summary_data.get('total_sources', 0)}
**Average Reliability:** {summary_data.get('avg_reliability', 0):.2f}

**Key Sources:**
""" + "\n".join([f"- {s['title']} ({s['source']})" for s in summary_data.get('sources', [])[:5]])
        
        except Exception as e:
            logger.error(f"Quick research failed: {e}")
            return f"Research failed: {str(e)}"

# Example usage and testing
def main():
    # Initialize the research network
    research_network = ResearchAssistantNetwork()
    
    # Example queries
    test_queries = [
        "artificial intelligence latest developments 2024",
        "climate change renewable energy solutions",
        "quantum computing applications"
    ]
    
    print("Research Assistant Network - Test Mode")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nTesting query: {query}")
        print("-" * 30)
        
        try:
            # Quick research
            result = research_network.quick_research(query)
            print(result[:500] + "..." if len(result) > 500 else result)
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "=" * 50)

if __name__ == "__main__":
    main()