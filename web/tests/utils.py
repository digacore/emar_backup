from app.models import User, Company, UserRole


def register(username, email="username@test.com", password="password"):
    user = User(
        username=username,
        email=email,
        password=password,
        activated=True,
        company_id=Company.query.filter(Company.is_global.is_(True)).first().id,
        role=UserRole.ADMIN,
    )
    user.save()
    return user.id


def login(client, username, password="password"):
    return client.post(
        "/login", data=dict(user_id=username, password=password), follow_redirects=True
    )


def logout(client):
    return client.get("/logout", follow_redirects=True)
