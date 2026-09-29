from app.repositories.user_repository import UserRepository
def test_user_permissions(db_session): assert isinstance(UserRepository(db_session).get_permissions(1),list)
def test_has_permission_matches_returned_permissions(db_session):
    repo=UserRepository(db_session)
    for code in repo.get_permissions(1): assert repo.has_permission(1,code) is True
