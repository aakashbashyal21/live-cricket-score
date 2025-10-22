import html
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
        
        # Initialize match data with flair and subreddit
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
            link_flair_text=post_data.get('link_flair_text') if post_data else None
        )
        
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