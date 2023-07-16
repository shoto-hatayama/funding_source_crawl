from main.maff_public_offering import MaffPublicOffering

def test_make_isvalue():
    """クロールが成功しているかチェック"""
    maff_public_offering = MaffPublicOffering()
    maff_public_offering.make()
    assert maff_public_offering.get_public_offering() is not None