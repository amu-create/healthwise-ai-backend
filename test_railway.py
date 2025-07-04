import urllib.request
import json
import sys

def test_railway_api():
    try:
        # 간단한 GET 요청
        url = "https://healthwise-api-production.up.railway.app/api/health/"
        req = urllib.request.Request(url)
        
        # 타임아웃 설정
        response = urllib.request.urlopen(req, timeout=10)
        
        status_code = response.getcode()
        content = response.read().decode('utf-8')
        
        print(f"Status Code: {status_code}")
        print(f"Response: {content}")
        
        return True
        
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        return False
    except Exception as e:
        print(f"Other Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_railway_api()
