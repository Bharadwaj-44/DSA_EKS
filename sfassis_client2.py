import requests
import json
from typing import List, Dict, Iterator, Optional
import time
import urllib3
import logging  # CHANGE 1: Added logging import
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# CHANGE 2: Import RRR library for AWS Secrets Manager integration
try:
    from ReduceReuseRecycle.apifunc import get_api_secrets
    RRR_AVAILABLE = True
except ImportError:
    RRR_AVAILABLE = False
    print("⚠️ Warning: ReduceReuseRecycle.apifunc not available.")
 
 
# ============================================================================
#                         RESPONSE CLASSES
# ============================================================================
 
class UsageStats:
    """Token usage statistics"""
    def __init__(self, prompt_tokens: int = 0, completion_tokens: int = 0, total_tokens: int = 0):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens
 
 
class Choice:
    """Response choice"""
    def __init__(self, message: Dict[str, str], finish_reason: str = "stop"):
        self.message = type('Message', (), message)()
        self.finish_reason = finish_reason
        self.delta = type('Delta', (), {'content': message.get('content', '')})()
 
 
class CompletionResponse:
    """Response from completion API"""
    def __init__(self, content: str, usage: UsageStats):
        self.choices = [Choice({"role": "assistant", "content": content})]
        self.usage = usage
 
 
class StreamingChunk:
    """Streaming chunk response"""
    def __init__(self, content: str):
        delta = type('Delta', (), {'content': content})()
        choice = type('Choice', (), {'delta': delta})()
        self.choices = [choice]
 
 
# ============================================================================
#                         SF ASSIST CLIENT
# ============================================================================
 
class SFAssistClient:
    """
    SF Assist Client - matches official payload structure
   
    Sends messages as array: [{"role": "system", ...}, {"role": "user", ...}, ...]
    Uses the official structure with nested application and model objects
    """
   
    # CHANGE 3: Added env and region_name parameters
    def __init__(self, config_or_api_key, base_url: str = None, model: str = None,
                 env: str = "dev", region_name: str = "us-east-2"):
        """
        Initialize SF Assist client
       
        Args:
            config_or_api_key: Either a config dict/object OR api_key string
            base_url: Base URL for the SF Assist endpoint (optional if config provided)
            model: Model name to use (optional, defaults from config)
            env: AWS environment (dev, sit, prod) - for RRR  # CHANGE 3
            region_name: AWS region - for RRR  # CHANGE 3
        """
        # CHANGE 4: Set up logger and AWS config for RRR
        self.logger = logging.getLogger("sfassist_client")
        self.logger.setLevel(logging.INFO)
        
        # AWS configuration for RRR
        self.env = env
        self.region_name = region_name
        
        # Handle both config object and individual parameters
        if isinstance(config_or_api_key, dict):
            # Config dict provided
            config = config_or_api_key
           
            # Check if sfassist section exists
            if 'sfassist' in config:
                sfassist_config = config['sfassist']
                # CHANGE 5: Removed self.api_key = ... (will be fetched from AWS)
                self.base_url = sfassist_config.get('base_url', '').rstrip('/')
                self.model = sfassist_config.get('model', 'snowflake-llama-3.3-70b')
                self.app_id = sfassist_config.get('app_id', 'aedl')
                self.aplctn_cd = sfassist_config.get('aplctn_cd', 'aedl')
                self.app_lvl_prefix = sfassist_config.get('app_lvl_prefix', '')
                self.session_id = sfassist_config.get('session_id', 'dsa_session')
                # CHANGE 6: Get AWS config from config file if available
                self.env = sfassist_config.get('env', self.env)
                self.region_name = sfassist_config.get('region_name', self.region_name)
            else:
                # Fallback to root level
                # CHANGE 7: Removed self.api_key = ... (will be fetched from AWS)
                self.base_url = config.get('base_url', '').rstrip('/')
                self.model = config.get('model', 'snowflake-llama-3.3-70b')
                self.app_id = config.get('app_id', 'aedl')
                self.aplctn_cd = config.get('aplctn_cd', 'aedl')
                self.app_lvl_prefix = config.get('app_lvl_prefix', '')
                self.session_id = config.get('session_id', 'dsa_session')
                # CHANGE 8: Get AWS config from root level
                self.env = config.get('env', self.env)
                self.region_name = config.get('region_name', self.region_name)
               
        elif hasattr(config_or_api_key, 'api_key') or hasattr(config_or_api_key, 'sfassist'):
            # Config object provided
            config = config_or_api_key
           
            # Check if sfassist attribute exists
            if hasattr(config, 'sfassist'):
                sfassist_config = config.sfassist
                # CHANGE 9: Removed self.api_key = ... (will be fetched from AWS)
                self.base_url = getattr(sfassist_config, 'base_url', '').rstrip('/')
                self.model = getattr(sfassist_config, 'model', 'snowflake-llama-3.3-70b')
                self.app_id = getattr(sfassist_config, 'app_id', 'aedl')
                self.aplctn_cd = getattr(sfassist_config, 'aplctn_cd', 'aedl')
                self.app_lvl_prefix = getattr(sfassist_config, 'app_lvl_prefix', '')
                self.session_id = getattr(sfassist_config, 'session_id', 'dsa_session')
                # CHANGE 10: Get AWS config from object attributes
                self.env = getattr(sfassist_config, 'env', self.env)
                self.region_name = getattr(sfassist_config, 'region_name', self.region_name)
            else:
                # Fallback to root level attributes
                # CHANGE 11: Removed self.api_key = ... (will be fetched from AWS)
                self.base_url = getattr(config, 'base_url', '').rstrip('/')
                self.model = getattr(config, 'model', 'snowflake-llama-3.3-70b')
                self.app_id = getattr(config, 'app_id', 'aedl')
                self.aplctn_cd = getattr(config, 'aplctn_cd', 'aedl')
                self.app_lvl_prefix = getattr(config, 'app_lvl_prefix', '')
                self.session_id = getattr(config, 'session_id', 'dsa_session')
                # CHANGE 12: Get AWS config from root attributes
                self.env = getattr(config, 'env', self.env)
                self.region_name = getattr(config, 'region_name', self.region_name)
        else:
            # Individual parameters provided
            # CHANGE 13: Removed self.api_key = config_or_api_key (will be fetched from AWS)
            self.base_url = base_url.rstrip('/') if base_url else ''
            self.model = model if model else 'snowflake-llama-3.3-70b'
            self.app_id = 'aedl'
            self.aplctn_cd = 'aedl'
            self.app_lvl_prefix = ''
            self.session_id = 'dsa_session'
       
        # CHANGE 14: Fetch API key from AWS using RRR
        self.api_key = None
        self.headers_with_secrets = {}
        self.cert_path = None
        
        if RRR_AVAILABLE:
            self._fetch_secrets_from_aws()
        else:
            print("⚠️ RRR not available - API calls may fail without proper authentication")
        
        # CHANGE 15: Updated debug output
        print(f"DEBUG INIT: api_key={'[SET]' if self.api_key else '[NOT SET]'}")
        print(f"DEBUG INIT: base_url={self.base_url if self.base_url else '[EMPTY]'}")
        print(f"DEBUG INIT: model={self.model}")
        print(f"DEBUG INIT: app_id={self.app_id}, aplctn_cd={self.aplctn_cd}")
        print(f"DEBUG INIT: env={self.env}, region={self.region_name}")  # CHANGE 15
       
        self.chat = self.ChatCompletion(self)
   
    # CHANGE 16: NEW METHOD - Fetch secrets from AWS using RRR
    def _fetch_secrets_from_aws(self):
        """
        Fetch API secrets from AWS Secrets Manager using RRR library
        
        This uses get_api_secrets() which:
        1. Fetches secrets from AWS at: {env}/api/{aplctn_cd}
        2. Replaces $$ placeholders in headers/params/body
        3. Downloads SSL certificates if needed
        """
        try:
            print(f"🔐 Fetching secrets from AWS Secrets Manager...")
            print(f"   📍 Secret path: {self.env}/api/{self.aplctn_cd}")
            print(f"   🏢 App ID: {self.app_id}")
            
            # Prepare headers with placeholder for API key (as your lead instructed)
            input_headers = {
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json",
                "apikey": "$${apikey}"  # ✅ Placeholder - RRR will replace this!
            }
            
            # Call RRR's get_api_secrets function
            params, headers, body, cert = get_api_secrets(
                log=self.logger,
                env=self.env,
                region_name=self.region_name,
                aplctn_cd=self.aplctn_cd,
                auth_type='api_key',
                provider='na',
                app_id=self.app_id,
                params={},
                headers=input_headers,
                body={}
            )
            
            self.headers_with_secrets = headers
            self.cert_path = cert
            
            # Extract API key from headers (after $$ replacement)
            self.api_key = headers.get('apikey') or headers.get('api-key') or headers.get('api_key')
            
            print(f"✅ Secrets fetched successfully!")
            print(f"   🔑 API key: {'[SET]' if self.api_key else '[NOT FOUND]'}")
            print(f"   📜 SSL cert: {cert if cert else '[NO CERT]'}")
            
        except Exception as e:
            print(f"❌ ERROR: Failed to fetch secrets from AWS: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to basic headers
            self.headers_with_secrets = {
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json"
            }
   
    def _build_payload(self, messages: List[Dict[str, str]], system_message: str = None) -> Dict:
        """
        Build request payload - OFFICIAL STRUCTURE
       
        Structure matches the format provided by lead:
        {
          "query": {
            "application": { aplctn_cd, app_id, app_lvl_prefix, session_id },
            "prompt": { messages: [...] },
            "model": { model, options },
            "response_format": { type, schema }
          }
        }
       
        Args:
            messages: List of message dicts with role and content
            system_message: Optional system message to prepend
           
        Returns:
            Payload dict for SF Assist API
        """
        print(f"\n{'='*80}")
        print(f"🔍 BUILDING PAYLOAD - OFFICIAL STRUCTURE")
        print(f"{'='*80}")
       
        # Extract system message
        sys_msg = system_message
        filtered_messages = []
       
        for msg in messages:
            if msg.get('role') == 'system':
                if not sys_msg:
                    sys_msg = msg['content']
            else:
                filtered_messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
       
        # Default system message
        if not sys_msg:
            sys_msg = "You are a helpful AI assistant for data analysis and Python programming."
       
        # Build messages array with system first
        all_messages = [{"role": "system", "content": sys_msg}] + filtered_messages
       
        print(f"✅ Messages array: {len(all_messages)} messages")
        print(f"   • System message: {len(sys_msg)} chars")
        print(f"   • User/Assistant messages: {len(filtered_messages)}")
       
        # Build payload - OFFICIAL STRUCTURE
        payload = {
            "query": {
                "application": {
                    "aplctn_cd": self.aplctn_cd,
                    "app_id": self.app_id,
                    "app_lvl_prefix": self.app_lvl_prefix,
                    "session_id": self.session_id
                },
                "prompt": {
                    "messages": all_messages  # 🔥 Messages as array!
                },
                "model": {
                    "model": self.model,
                    "options": {}
                },
                #"response_format": {
                #   "type": "json",
                #    "schema": {}
                #}
            }
        }
       
        print(f"✅ Payload Structure:")
        print(f"   • application.aplctn_cd: {self.aplctn_cd}")
        print(f"   • application.app_id: {self.app_id}")
        print(f"   • model.model: {self.model}")
        print(f"   • prompt.messages: {len(all_messages)} messages")
        print(f"{'='*80}\n")
       
        return payload
   
    # CHANGE 17: Updated _make_request to use headers from RRR
    def _make_request(self, payload: Dict) -> requests.Response:
        """Make HTTP request to SF Assist API"""
        # Use headers from RRR (already has API key filled in)
        headers = self.headers_with_secrets.copy()  # CHANGE 17
       
        print(f"DEBUG: Making request to {self.base_url}")
        print(f"DEBUG: Headers: {list(headers.keys())}")
       
        # CHANGE 18: Use SSL cert from RRR if available
        verify_value = self.cert_path if self.cert_path else False
       
        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            verify=verify_value,  # CHANGE 18
            timeout=120
        )
       
        return response
   
    class ChatCompletion:
        """Chat completion interface for SF Assist"""
       
        def __init__(self, client):
            self.client = client
            self.completions = self  # Support OpenAI-style API
       
        def create(self, model: str, messages: List[Dict[str, str]],
                   stream: bool = False, **kwargs):
            """
            Create chat completion using SF Assist
           
            Args:
                model: Model name (will use client's configured model)
                messages: List of messages
                stream: Whether to stream the response
                **kwargs: Additional parameters
               
            Returns:
                CompletionResponse object or Iterator[StreamingChunk] for streaming
            """
            # Build payload (messages as array - official structure!)
            payload = self.client._build_payload(messages)
           
            # Make request
            response = self.client._make_request(payload)
           
            # Handle response
            if response.status_code == 200:
                try:
                    # Try parsing as JSON first
                    data = response.json()
                   
                    # Extract content from various possible response formats
                    content = None
                    if 'text' in data:
                        content = data['text']
                    elif 'response' in data:
                        content = data['response']
                    elif 'choices' in data and len(data['choices']) > 0:
                        content = data['choices'][0].get('message', {}).get('content', '')
                    elif 'message' in data:
                        # Horizon-style response
                        content = data['message'].get('content', '')
                    elif 'content' in data:
                        content = data['content']
                    else:
                        content = str(data)
                   
                    print(f"DEBUG: Response received ({len(content)} chars)")
                   
                    # Handle streaming vs non-streaming
                    if stream:
                        # Simulate streaming by yielding chunks
                        return self._simulate_streaming(content)
                    else:
                        # Create usage stats (estimate if not provided)
                        usage_data = data.get('usage', {})
                        usage = UsageStats(
                            prompt_tokens=usage_data.get('prompt_tokens', 0),
                            completion_tokens=usage_data.get('completion_tokens', 0),
                            total_tokens=usage_data.get('total_tokens', 0)
                        )
                        return CompletionResponse(content, usage)
               
                except (json.JSONDecodeError, ValueError) as e:
                    # If not JSON, treat as plain text
                    print(f"DEBUG: JSON decode error, treating as plain text: {e}")
                    content = response.text
                   
                    if stream:
                        return self._simulate_streaming(content)
                    else:
                        usage = UsageStats()
                        return CompletionResponse(content, usage)
           
            else:
                # Handle error responses
                print(f"ERROR: Response status {response.status_code}")
                print(f"ERROR: Response body: {response.text}")
                try:
                    error_data = response.json()
                    raise Exception(f"API Error Response: {json.dumps(error_data, indent=2)}")
                except json.JSONDecodeError:
                    raise Exception(f"API Error Response ({response.status_code}): {response.text}")
       
        def _simulate_streaming(self, content: str):
            """
            Simulate streaming by yielding chunks of the response
           
            Args:
                content: Full response content to stream
               
            Yields:
                StreamingChunk objects
            """
            # Split content into words for more natural streaming
            words = content.split(' ')
            for i, word in enumerate(words):
                # Add space before word except for first word
                chunk_text = word if i == 0 else ' ' + word
                yield StreamingChunk(chunk_text)
 
 
def create_sfassist_client(api_key: str, base_url: str, model: str = "snowflake-llama-3.3-70b"):
    """
    Factory function to create SF Assist client
   
    Args:
        api_key: API key for authentication
        base_url: Base URL for the SF Assist endpoint
        model: Model name to use
       
    Returns:
        SFAssistClient instance
    """
    return SFAssistClient(api_key, base_url, model)
