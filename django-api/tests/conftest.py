import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def usuario_base(db):
    """Crea un usuario jugador básico para usar en las pruebas."""
    return User.objects.create_user(username="jugador1", password="password123")


@pytest.fixture
def usuario_admin(db):
    """Crea un usuario administrador para usar en las pruebas."""
    return User.objects.create_superuser(username="admin1", password="adminpass")
