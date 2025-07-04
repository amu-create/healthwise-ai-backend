import urllib.request
import json
import sys

def test_debug_reset_password():
    try:
        # POST 요청 데이터
        data = {
            "email": "ww@ww.ww",
            "password": "test123"
        }
        
        # JSON 데이터로 변환
        json_data = json.dumps(data).encode('utf-8')
        
        # POST 요청 설정
        url = "https://healthwise-api-production.up.railway.app/api/debug/reset-password/"
        req = urllib.request.Request(url, data=json_data)
        req.add_header('Content-Type', 'application/json')
        
        # 요청 보내기
        response = urllib.request.urlopen(req, timeout=15)
        
        status_code = response.getcode()
        content = response.read().decode('utf-8')
        
        print(f"Status Code: {status_code}")
        print(f"Response: {content}")
        
        return True
        
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        print(f"Response: {e.read().decode('utf-8')}")
        return False
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        return False
    except Exception as e:
        print(f"Other Error: {str(e)}")
        return False

def test_debug_create_user():
    try:
        # POST 요청 데이터
        data = {
            "username": "testuser123",
            "email": "test123@test.com",
            "password": "test123"
        }
        
        # JSON 데이터로 변환
        json_data = json.dumps(data).encode('utf-8')
        
        # POST 요청 설정
        url = "https://healthwise-api-production.up.railway.app/api/debug/create-user/"
        req = urllib.request.Request(url, data=json_data)
        req.add_header('Content-Type', 'application/json')
        
        # 요청 보내기
        response = urllib.request.urlopen(req, timeout=15)
        
        status_code = response.getcode()
        content = response.read().decode('utf-8')
        
        print(f"Status Code: {status_code}")
        print(f"Response: {content}")
        
        return True
        
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        print(f"Response: {e.read().decode('utf-8')}")
        return False
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        return False
    except Exception as e:
        print(f"Other Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== 기존 사용자 비밀번호 재설정 ===")
    test_debug_reset_password()
    
    print("\n=== 새 사용자 생성 ===")
    test_debug_create_user()
