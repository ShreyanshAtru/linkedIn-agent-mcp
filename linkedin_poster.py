from langchain.tools import tool
import requests
import logging
from typing import Dict
import settings
from post_writer_agent import run_post_writer

logger = logging.getLogger(__name__)

class LinkedInAPI:
    """LinkedIn API integration for posting content"""
    
    def __init__(self):
        self.access_token = settings.LINKEDIN_ACCESS_TOKEN
        self.base_url = "https://api.linkedin.com/v2"
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
    
    def get_user_profile(self) -> Dict:
        """Get the authenticated user's LinkedIn profile"""
        try:
            url = f"{self.base_url}/userinfo"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'error': None
                }
            else:
                logger.error(f"Failed to get user profile: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'data': None,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }
    
    def create_text_post(self, content: str, hashtags: str = "") -> Dict:
        """Create a text-only LinkedIn post"""
        try:
            profile_result = self.get_user_profile()
            # print(100*'-', profile_result)
            breakpoint()
            if not profile_result['success']:
                return profile_result
            
            user_id = profile_result['data'].get('sub')
            if not user_id:
                return {'success': False, 'error': 'Could not retrieve user ID (sub) from profile info.'}
            author_urn = f"urn:li:person:{user_id}"
            
            full_content = content
            if hashtags:
                full_content += f"\n\n{hashtags}"
            
            post_data = {
                "author": author_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": full_content
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            url = f"{self.base_url}/ugcPosts"
            response = requests.post(url, json=post_data, headers=self.headers)
            
            if response.status_code == 201:
                post_id = response.headers.get('x-linkedin-id')
                logger.info(f"Successfully posted to LinkedIn. Post ID: {post_id}")
                return {
                    'success': True,
                    'post_id': post_id,
                    'response_data': response.json() if response.content else {},
                    'error': None
                }
            else:
                logger.error(f"Failed to create LinkedIn post: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'post_id': None,
                    'response_data': None,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error creating LinkedIn post: {str(e)}")
            return {
                'success': False,
                'post_id': None,
                'response_data': None,
                'error': str(e)
            }

@tool
def post_to_linkedin(prompt: str) -> str:
    """
    Generates and posts a professional LinkedIn post from a given idea.
    
    Args:
        prompt (str): User's idea or topic.
    
    Returns:
        str: Status message or post link.
    """
    try:
        # 1. Generate post content
        # breakpoint()
        final_post = run_post_writer(prompt)

        # 2. Post to LinkedIn using new API
        result = LinkedInAPI().create_text_post(final_post)
        # breakpoint()
        
        if result['success']:
            return f"✅ Post published successfully! Post ID: {result['post_id']}"
        else:
            return f"❌ Failed to publish: {result['error']}"

    except Exception as e:
        return f"❌ Error: {str(e)}"
