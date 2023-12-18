from app.utils import create_desktop_icon


def test_create_desktop_icon():
    """test create_desktop_icon()"""

    assert not create_desktop_icon()
