from .config import settings
from exa_py import Exa
import cohere


EXA_CLIENT = Exa(api_key=settings.EXA_API_KEY)

COHERE_CLIENT = cohere.AsyncClientV2(api_key=settings.COHERE_API_KEY)
