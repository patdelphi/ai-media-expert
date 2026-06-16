from app.api.v1.endpoints.system_config import get_config_categories
from app.api.v1.endpoints.tag_groups import get_tag_groups
from app.models.system_config import SystemConfig
from app.models.tag_group import TagGroup, TagGroupTag
from app.tests.factories import create_admin, create_user


def test_get_config_categories_counts_only_active(override_db) -> None:
    admin = create_admin(override_db, email="admin-system-config@example.com")

    override_db.add(
        SystemConfig(
            key="system.name",
            value="AI",
            category="system",
            is_active=True,
            is_public=False,
            is_encrypted=False,
            data_type="string",
        )
    )
    override_db.add(
        SystemConfig(
            key="ai.provider",
            value="custom",
            category="ai",
            is_active=True,
            is_public=False,
            is_encrypted=False,
            data_type="string",
        )
    )
    override_db.add(
        SystemConfig(
            key="system.inactive",
            value="0",
            category="system",
            is_active=False,
            is_public=False,
            is_encrypted=False,
            data_type="string",
        )
    )
    override_db.commit()

    payload = get_config_categories(current_user=admin, db=override_db)

    assert payload.code == 200
    assert payload.data is not None
    category_counts = {item.category: item.count for item in payload.data}
    assert category_counts.get("system") == 1
    assert category_counts.get("ai") == 1


def test_get_tag_groups_include_tags(override_db) -> None:
    user = create_user(override_db, email="tag-user@example.com")

    group = TagGroup(name="group-a", description="desc", is_active=True)
    override_db.add(group)
    override_db.flush()
    override_db.add(
        TagGroupTag(
            name="tag-a",
            color="#FF0000",
            tag_group_id=group.id,
            is_active=True,
        )
    )
    override_db.commit()

    payload = get_tag_groups(
        search=None,
        is_active=None,
        include_tags=True,
        current_user=user,
        db=override_db,
    )

    assert payload.code == 200
    assert payload.data is not None
    assert len(payload.data) == 1
    assert payload.data[0].name == "group-a"
    assert len(payload.data[0].tags) == 1
    assert payload.data[0].tags[0].name == "tag-a"


def test_get_tag_groups_exclude_tags_returns_tag_count(override_db) -> None:
    user = create_user(override_db, email="tag-user-no-tags@example.com")

    group = TagGroup(name="group-b", description=None, is_active=True)
    override_db.add(group)
    override_db.flush()
    override_db.add(
        TagGroupTag(
            name="tag-b",
            color=None,
            tag_group_id=group.id,
            is_active=True,
        )
    )
    override_db.commit()

    payload = get_tag_groups(
        search=None,
        is_active=None,
        include_tags=False,
        current_user=user,
        db=override_db,
    )

    assert payload.code == 200
    assert payload.data is not None
    assert len(payload.data) == 1
    assert payload.data[0].name == "group-b"
    assert getattr(payload.data[0], "tag_count", None) == 1

