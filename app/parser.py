import html
import re
import json
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from models import CricketMatch, Innings, InningScore, Batter, Bowler, MatchStatus

# --- Load flags JSON globally
with open('flag.json', 'r', encoding='utf-8') as f:
    FLAGS = json.load(f)  # Example: [{"title": "England Women", "flag": "..."}]

def get_flag_for_team(team_name: str) -> Optional[str]:
    """Return the flag URL for a given team name."""
    for entry in FLAGS:
        if entry['title'].lower() == team_name.lower():
            return entry['flag']
    return None

class CricketMatchParser:
    @staticmethod
    def parse_match(html_content: str, post_data: Dict[str, Any] = None) -> CricketMatch:
        decoded_text = html.unescape(html_content)
        soup = BeautifulSoup(decoded_text, 'html.parser')

        # --- Extract match title
        title_elem = soup.find('h3')
        match_title = title_elem.get_text(strip=True) if title_elem else None

        # --- Extract Cricinfo URL and match_id
        cricinfo_url = None
        match_id = None
        all_links = soup.find_all('a', href=True)
        cricinfo_links = [a['href'] for a in all_links if 'cricinfo' in a['href'].lower()]

        game_links = [link for link in cricinfo_links if '/game/' in link]
        if game_links:
            cricinfo_url = game_links[0]
            parts = cricinfo_url.split('/')
            for i, part in enumerate(parts):
                if part == 'game' and i + 1 < len(parts):
                    match_id = parts[i + 1]
                    break
        elif cricinfo_links:
            cricinfo_url = cricinfo_links[0]
            numbers = re.findall(r'\d+', cricinfo_url)
            if numbers:
                match_id = max(numbers, key=len)

        # --- Initialize match object
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
            cricinfo_url=cricinfo_url,
        )

        # --- Parse innings tables
        tables = soup.find_all('table')
        if not tables:
            return match_data

        for table in tables:
            headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
            rows = table.find_all('tr')[1:]  # skip header row

            if not headers or not rows:
                continue

            if 'innings' in headers and 'score' in headers:
                # 🆕 Get <p> tags after table
                following_ps = []
                next_tag = table.find_next_sibling()
                while next_tag and next_tag.name == 'p':
                    following_ps.append(next_tag)
                    next_tag = next_tag.find_next_sibling()
                    
                remarks_text = None
                if len(following_ps) >= 2:
                    remarks_text = following_ps[0].get_text(strip=True)

                # 🆕 Parse all team/score pairs for this innings block, adding flags
                inning_scores = []
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        team_name = cells[0].get_text(strip=True)
                        score = cells[1].get_text(strip=True)
                        flag_url = get_flag_for_team(team_name)
                        inning_scores.append(
                            InningScore(
                                team=team_name,
                                score=score,
                                flag=flag_url
                            )
                        )

                match_data.innings.append(
                    Innings(
                        inning_score=inning_scores,
                        remarks=remarks_text,
                    )
                )

            elif 'batter' in headers:
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        match_data.current_batters.append(
                            Batter(
                                name=cells[0].get_text(strip=True),
                                runs=cells[1].get_text(strip=True),
                                balls=cells[2].get_text(strip=True),
                                strike_rate=cells[3].get_text(strip=True),
                            )
                        )

            elif 'bowler' in headers:
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        match_data.current_bowlers.append(
                            Bowler(
                                name=cells[0].get_text(strip=True),
                                overs=cells[1].get_text(strip=True),
                                runs=cells[2].get_text(strip=True),
                                wickets=cells[3].get_text(strip=True),
                            )
                        )

        # --- Extract recent balls
        recent_balls = soup.find('pre')
        if recent_balls:
            match_data.match_status.recent_balls = recent_balls.get_text(strip=True)

        # --- Extract global match status
        paragraphs = soup.find_all('p')
        if len(paragraphs) >= 2:
            match_data.match_status.text = paragraphs[-2].get_text(strip=True)

        if len(match_data.innings) > 0:
            last_remarks = match_data.innings[-1].remarks
            if match_data.match_status.text == last_remarks:
                match_data.match_status.text = None

        return match_data
