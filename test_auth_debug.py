import urllib.request
import json
import sys

def test_auth_debug():
    try:
        # POST 요청 데이터
        data = {
            "email": "ww@ww.ww",
            "password": "test123"
        }
        
        # JSON 데이터로 변환
        json_data = json.dumps(data).encode('utf-8')
        
        # POST 요청 설정
        url = "https://healthwise-api-production.up.railway.app/api/debug/test-auth/"
        req = urllib.request.Request(url, data=json_data)
        req.add_header('Content-Type', 'application/json')
        
        # 요청 보내기
        response = urllib.request.urlopen(req, timeout=15)
        
        status_code = response.getcode()
        content = response.read().decode('utf-8')
        
        print(f"Status Code: {status_code}")
        print(f"Response: {content}")
        
        # JSON 파싱해서 예쁘게 출력
        try:
            json_response = json.loads(content)
            print("\n=== 상세 정보 ===")
            for key, value in json_response.items():
                print(f"{key}: {value}")
        except:
            pass
            
        return True
        
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        try:
            error_content = e.read().decode('utf-8')
            print(f"Error Response: {error_content}")
        except:
            pass
        return False
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        return False
    except Exception as e:
        print(f"Other Error: {str(e)}")
        return False

def test_real_login():
    try:
        # 실제 로그인 API 테스트
        data = {
            "username": "ww@ww.ww",
            "password": "test123"
        }
        
        json_data = json.dumps(data).encode('utf-8')
        
        url = "https://healthwise-api-production.up.railway.app/api/auth/login/"
        req = urllib.request.Request(url, data=json_data)
        req.add_header('Content-Type', 'application/json')
        
        response = urllib.request.urlopen(req, timeout=15)
        
        status_code = response.getcode()
        content = response.read().decode('utf-8')
        
        print(f"Real Login Status Code: {status_code}")
        print(f"Real Login Response: {content}")
        
        return True
        
    except urllib.error.HTTPError as e:
        print(f"Real Login HTTP Error: {e.code} - {e.reason}")
        try:
            error_content = e.read().decode('utf-8')
            print(f"Real Login Error Response: {error_content}")
        except:
            pass
        return False
    except Exception as e:
        print(f"Real Login Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== 인증 디버깅 테스트 ===")
    test_auth_debug()
    
    print("\n=== 실제 로그인 테스트 ===")
    test_real_login()
