import logging
from typing import Dict, Any, List, Optional
import requests
import json

logger = logging.getLogger(__name__)


class RMPClient:
    """Client for RateMyProfessor API using GraphQL.

    This client exposes a single clear method `get_professor_summary` which
    requires a `school_name` and `professor_name`. It returns a JSON-serializable
    dict with compact fields for easy integration.
    """

    def __init__(self):
        self.base_url = "https://www.ratemyprofessors.com/graphql"
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json"
        }

    def _get_school_id(self, school_name: str) -> Optional[str]:
        """Search for a school's GraphQL ID."""
        query = """
        query SearchSchoolsQuery($query: SchoolSearchQuery!) {
          search: newSearch {
            schools(query: $query) {
              edges {
                node {
                  id
                  name
                  city
                  state
                }
              }
            }
          }
        }
        """
        
        variables = {
            "query": {
                "text": school_name
            }
        }
        
        try:
            resp = requests.post(
                self.base_url,
                headers=self.headers,
                json={"query": query, "variables": variables}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                schools = data.get('data', {}).get('search', {}).get('schools', {}).get('edges', [])
                
                if schools:
                    # Find exact match or closest match
                    school_name_lower = school_name.lower()
                    for school in schools:
                        if school['node']['name'].lower() == school_name_lower:
                            return school['node']['id']
                    
                    # If no exact match, return first result
                    return schools[0]['node']['id']
            
            raise ValueError(f"Couldn't find {school_name}... you sure that's a real school?")
                
        except Exception as e:
            logger.error(f"School search broke: {e}")
            raise ValueError(f"Something went wrong looking for the school: {str(e)}")

    def get_professor_summary(self, school_name: str, professor_name: str, comment_limit: int = 40) -> Dict[str, Any]:
        """Return a compact summary for a professor at a given school.

        Output shape example:
        {
          "name": "Full Name",
          "department": "Computer Science",
          "rating": 4.2,
          "difficulty": 3.1,
          "num_ratings": 42,
          "would_take_again": 87.5,
          "recent_comments": ["...", "..."],
        }
        """
        try:
            school_id = self._get_school_id(school_name)
            
            query = """
            query TeacherSearchResultsPageQuery($query: TeacherSearchQuery!, $numRatings: Int!) {
              search: newSearch {
                teachers(query: $query) {
                  edges {
                    node {
                      firstName
                      lastName
                      department
                      avgRating
                      avgDifficulty
                      wouldTakeAgainPercent
                      numRatings
                      recentRatings: ratings(first: $numRatings) {
                        edges {
                          node {
                            comment
                            date
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
            """
            
            variables = {
                "query": {
                    "text": professor_name,
                    "schoolID": school_id
                },
                "numRatings": comment_limit
            }
            
            resp = requests.post(
                self.base_url,
                headers=self.headers,
                json={"query": query, "variables": variables}
            )
            
            if resp.status_code != 200:
                raise ValueError(f"RMP's servers are being weird: {resp.text}")
            
            data = resp.json()
            professors = data.get('data', {}).get('search', {}).get('teachers', {}).get('edges', [])
            
            if not professors:
                raise ValueError(f"Can't find {professor_name}... maybe they're too new to be rated?")
            
            # Find the prof we're looking for
            professor = None
            search_name = professor_name.lower()
            for prof in professors:
                full_name = f"{prof['node']['firstName']} {prof['node']['lastName']}".lower()
                if search_name in full_name:
                    professor = prof['node']
                    break
            
            if not professor:
                # Couldn't find exact match but whatever, first one's probably right
                professor = professors[0]['node']
            
            # Extract comments
            comments = []
            if professor.get('recentRatings', {}).get('edges'):
                for rating in professor['recentRatings']['edges']:
                    if rating['node'].get('comment'):
                        comments.append(rating['node']['comment'])
                comments = comments[:comment_limit]
            
            return {
                "name": f"{professor['firstName']} {professor['lastName']}",
                "department": professor['department'],
                "rating": round(float(professor['avgRating']), 1) if professor.get('avgRating') is not None else None,
                "difficulty": round(float(professor['avgDifficulty']), 1) if professor.get('avgDifficulty') is not None else None,
                "num_ratings": professor['numRatings'],
                "would_take_again": round(float(professor['wouldTakeAgainPercent']), 1) if professor.get('wouldTakeAgainPercent') not in [None, -1] else None,
                # "recent_comments": comments
            }
                
        except Exception as e:
            logger.error(f"Error getting professor summary: {e}")
            raise ValueError(str(e))