import os
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from parser import CricketMatchParser
from models import CricketMatch

class RedditFetcher:
    def __init__(self):
        self.user_agent = os.getenv('REDDIT_USER_AGENT', 'CricketMatchAPI/1.0')
        self.base_url = "https://www.reddit.com/user/cricket-match/submitted.json"
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def fetch_all_matches_async(self) -> List[Dict[str, Any]]:
        """Fetch ALL matches asynchronously (Reddit API returns 25 by default)"""
        url = f"{self.base_url}?sort=new"
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(url, headers={'User-Agent': self.user_agent}) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['data']['children']
                else:
                    raise Exception(f"HTTP {response.status}: {await response.text()}")
    
    async def fetch_all_matches_with_retry(self, retries: int = 3) -> List[Dict[str, Any]]:
        """Fetch all matches with retry logic"""
        for attempt in range(retries):
            try:
                return await self.fetch_all_matches_async()
            except Exception as e:
                if attempt == retries - 1:
                    raise e
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
        return []

class MatchService:
    def __init__(self):
        self.fetcher = RedditFetcher()
        self.parser = CricketMatchParser()

    async def get_matches(self, limit: int = 10, today_only: bool = False, last_days: Optional[int] = None) -> List[CricketMatch]:
        """Get parsed cricket matches with optional date filtering"""
        try:
            # Fetch ALL posts first
            all_posts = await self.fetcher.fetch_all_matches_with_retry()
            matches = []

            for i, post in enumerate(all_posts):
                post_data = post['data']
                
                # Debug info for each post
                title = post_data.get('title', 'No title')
                subreddit = post_data.get('subreddit', '').lower()
                edited = post_data.get('edited')
                has_selftext_html = 'selftext_html' in post_data and bool(post_data['selftext_html'])
                
                # ALWAYS filter by subreddit=cricket
                if subreddit != 'cricket':
                    continue
                
                if 'selftext_html' in post_data and post_data['selftext_html']:
                    try:
                        match = self.parser.parse_match(
                            post_data['selftext_html'], 
                            post_data
                        )
                        matches.append(match)
                    except Exception as e:
                        continue
                else:
                    print(f"  -> SKIP: No selftext_html content")
                            
            if limit > 0:
                matches = matches[:limit]
                print(f"DEBUG: After limit - {len(matches)} matches returned")
            else:
                print(f"DEBUG: No limit applied - {len(matches)} matches returned")
            
            return matches
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            raise Exception(f"Failed to fetch matches: {str(e)}")
    
    async def get_today_matches(self, limit: int = 10) -> List[CricketMatch]:
        """Get only today's cricket matches"""
        return await self.get_matches(limit=limit, today_only=True)