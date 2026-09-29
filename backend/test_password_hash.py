from app.core.security import hash_password,verify_password
if __name__=="__main__":
    password="OpsPilot@123"; h=hash_password(password); print("Original:",password); print("Hash:",h); print("Correct password:",verify_password(password,h)); print("Wrong password:",verify_password("WrongPassword",h))
