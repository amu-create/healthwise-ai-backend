import urllib.request
import json
import sys

def test_new_user_login():
    try:
        # 새 사용자로 로그인 테스트
        data = {
            "username": "test123@test.com",  # 이메일을 username으로 사용
            "password": "test123"
        }
        
        json_data = json.dumps(data).encode('utf-8')
        
        url = "https://healthwise-api-production.up.railway.app/api/auth/login/"
        req = urllib.request.Request(url, data=json_data)
        req.add_header('Content-Type', 'application/json')
        
        response = urllib.request.urlopen(req, timeout=15)
        
        status_code = response.getcode()
        content = response.read().decode('utf-8')
        
        print(f"New User Login Status Code: {status_code}")
        print(f"New User Login Response: {content}")
        
        return True
        
    except urllib.error.HTTPError as e:
        print(f"New User Login HTTP Error: {e.code} - {e.reason}")
        try:
            error_content = e.read().decode('utf-8')
            print(f"New User Login Error Response: {error_content}")
        except:
            pass
        return False
    except Exception as e:
        print(f"New User Login Error: {str(e)}")
        return False

def test_new_user_by_email():
    try:
        # 이메일로 로그인 테스트
        data = {
            "email": "test123@test.com",
            "password": "test123"
        }
        
        json_data = json.dumps(data).encode('utf-8')
        
        url = "https://healthwise-api-production.up.railway.app/api/auth/login/"
        req = urllib.request.Request(url, data=json_data)
        req.add_header('Content-Type', 'application/json')
        
        response = urllib.request.urlopen(req, timeout=15)
        
        status_code = response.getcode()
        content = response.read().decode('utf-8')
        
        print(f"Email Login Status Code: {status_code}")
        print(f"Email Login Response: {content}")
        
        return True
        
    except urllib.error.HTTPError as e:
        print(f"Email Login HTTP Error: {e.code} - {e.reason}")
        try:
            error_content = e.read().decode('utf-8')
            print(f"Email Login Error Response: {error_content}")
        except:
            pass
        return False
    except Exception as e:
        print(f"Email Login Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== 새 사용자 (username) 로그인 테스트 ===")
    test_new_user_login()
    
    print("\n=== 새 사용자 (email) 로그인 테스트 ===")
    test_new_user_by_email()
