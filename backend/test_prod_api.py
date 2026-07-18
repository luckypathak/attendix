import requests

login_data = {
    "username": "ilucky",
    "password": "lucky"
}
login_url = "https://attendix-1-akff.onrender.com/api/company/auth/login/"
res = requests.post(login_url, json=login_data)
if res.status_code == 200:
    token = res.json().get('access')
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test history
    hist_res = requests.get("https://attendix-1-akff.onrender.com/api/attendance/records/history/", headers=headers)
    print("History Status:", hist_res.status_code)
    print("History Body:", hist_res.text[:500])
    
    # Test current
    cur_res = requests.get("https://attendix-1-akff.onrender.com/api/attendance/records/current/", headers=headers)
    print("Current Status:", cur_res.status_code)
    print("Current Body:", cur_res.text[:500])
else:
    print("Login Failed:", res.status_code, res.text)
