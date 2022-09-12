from urllib.parse import urlparse

def valid_url(to_validate:str) -> bool:
    try:
        v = urlparse(to_validate)    
        if (v.scheme in ('http', 'https') and
            v.netloc and
            (v.port == None or v.port)):
            return True
    except:
        pass
    return False
