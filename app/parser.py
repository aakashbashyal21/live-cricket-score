import html
import re
from bs4 import BeautifulSoup
from typing import Dict, Any
from models import CricketMatch, Innings, Batter, Bowler, MatchStatus

class CricketMatchParser:
    @staticmethod
    def parse_match(html_content: str, post_data: Dict[str, Any] = None) -> CricketMatch:
        """Parse cricket match data from Reddit HTML"""
        decoded_text = html.unescape(html_content)
        soup = BeautifulSoup(decoded_text, 'html.parser')
        
        # Extract match title
        title_elem = soup.find('h3')
        match_title = title_elem.get_text().strip() if title_elem else None

        # Extract Cricinfo URL and match_id
        cricinfo_url = None
        match_id = None
        
        # Look for Cricinfo links
        all_links = soup.find_all('a', href=True)
        cricinfo_links = []
        
        for link in all_links:
            href = link.get('href', '')
            if 'cricinfo' in href.lower():
                cricinfo_links.append(href)
        
        # Prioritize links that contain "/game/" as they're more likely to be direct match links
        game_links = [link for link in cricinfo_links if '/game/' in link]
        
        if game_links:
            # Use the first game link found
            cricinfo_url = game_links[0]
            # Extract match_id - simpler approach
            parts = cricinfo_url.split('/')
            for i, part in enumerate(parts):
                if part == 'game' and i + 1 < len(parts):
                    match_id = parts[i + 1]
                    break
        elif cricinfo_links:
            # Fallback to any cricinfo link
            cricinfo_url = cricinfo_links[0]
            # Try to extract any numeric ID from the URL
            numbers = re.findall(r'\d+', cricinfo_url)
            if numbers:
                # Use the longest number (likely the match ID)
                match_id = max(numbers, key=len)

        # Initialize match data BEFORE using it
        match_data = CricketMatch(
            post_title=post_data.get('title') if post_data else "",
            match_title=match_title,
            innings=[],
            current_batters=[],
            current_bowlers=[],
            match_status=MatchStatus(),
            created_utc=post_data.get('created_utc') if post_data else None,
            url=post_data.get('url') if post_data else None,
            reddit_id=post_data.get('id') if post_data else None,
            subreddit=post_data.get('subreddit') if post_data else None,
            link_flair_text=post_data.get('link_flair_text') if post_data else None,
            match_id=match_id,
            cricinfo_url=cricinfo_url
        )

        print(f"✅ Parsed match: {match_data.match_title or post_data.get('title')}")

        # Parse all tables
        tables = soup.find_all('table')
        
        for table in tables:
            headers = [th.get_text().strip().lower() for th in table.find_all('th')]
            rows = table.find_all('tr')[1:]  # Skip header
            
            if not headers or not rows:
                continue
                
            if 'innings' in headers and 'score' in headers:
                # Innings table
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        match_data.innings.append(
                            Innings(
                                team=cells[0].get_text().strip(),
                                score=cells[1].get_text().strip()
                            )
                        )
            
            elif 'batter' in headers:
                # Batter table
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        match_data.current_batters.append(
                            Batter(
                                name=cells[0].get_text().strip(),
                                runs=cells[1].get_text().strip(),
                                balls=cells[2].get_text().strip(),
                                strike_rate=cells[3].get_text().strip()
                            )
                        )
            
            elif 'bowler' in headers:
                # Bowler table
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        match_data.current_bowlers.append(
                            Bowler(
                                name=cells[0].get_text().strip(),
                                overs=cells[1].get_text().strip(),
                                runs=cells[2].get_text().strip(),
                                wickets=cells[3].get_text().strip()
                            )
                        )
        
        # Extract recent balls
        recent_balls = soup.find('pre')
        if recent_balls:
            match_data.match_status.recent_balls = recent_balls.get_text().strip()
        
        # Extract match status
        paragraphs = soup.find_all('p')
        if len(paragraphs) >= 2:
            status_text = paragraphs[-2].get_text().strip()
            match_data.match_status.text = status_text
        
        return match_data