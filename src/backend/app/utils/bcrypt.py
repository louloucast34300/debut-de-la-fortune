from passlib.hash import bcrypt


# BCRYPT METHODS 

def generate_new_salt(password):
    return bcrypt.hash(password)

def verify_password(password, h_password):
    return bcrypt.verify(password, h_password)